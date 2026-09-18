"""Live connection statistics of the attack playground, inside CTFd.

The playground's stats server counts ssh sessions and answers with three
numbers - connected right now, connected during a window, ever connected - plus
whether its collector is currently following docker. This plugin adds:

  * ``/playground``, a page that shows those numbers and keeps them fresh
  * ``/api/v1/playground/stats``, the json the page polls, fetched from the
    stats server by CTFd (the server listens on loopback only, so browsers
    cannot ask it themselves)
  * ``/admin/playground_stats``, the configuration in effect and a live probe

See README.md for the settings.
"""

from flask import Blueprint, current_app, jsonify, render_template, request

from CTFd.plugins import register_admin_plugin_menu_bar, register_user_page_menu_bar
from CTFd.utils.decorators import admins_only

from .client import StatsClient, StatsUnavailable
from .config import config, describe_window, window_seconds

EXTENSION = "playground_stats"


def get_client():
    return current_app.extensions[EXTENSION]


def windows():
    """The selectable windows, each with the label the page shows for it."""
    return [
        {
            "window": window,
            "seconds": window_seconds(window),
            "label": describe_window(window_seconds(window)),
        }
        for window in current_app.config["PLAYGROUND_STATS_WINDOWS"]
    ]


def load(app):
    config(app)
    app.extensions[EXTENSION] = StatsClient(
        url=app.config["PLAYGROUND_STATS_URL"],
        timeout=app.config["PLAYGROUND_STATS_TIMEOUT"],
        ttl=app.config["PLAYGROUND_STATS_CACHE"],
    )

    playground_bp = Blueprint(
        "playground_stats",
        __name__,
        template_folder="templates",
        static_folder="assets",
        static_url_path="/plugins/ctfd_plugin_playground_stats/assets",
    )

    @playground_bp.route("/playground", methods=["GET"])
    def playground_page():
        window = current_app.config["PLAYGROUND_STATS_WINDOW"]
        stats, error = None, None
        try:
            stats = get_client().get(window)
        except StatsUnavailable as exc:
            error = str(exc)
        return render_template(
            "playground.html",
            stats=stats,
            error=error,
            window=window,
            windows=windows(),
            refresh=current_app.config["PLAYGROUND_STATS_REFRESH"],
        )

    @playground_bp.route("/api/v1/playground/stats", methods=["GET"])
    def playground_stats_api():
        window = request.args.get(
            "window", current_app.config["PLAYGROUND_STATS_WINDOW"]
        )
        if window not in current_app.config["PLAYGROUND_STATS_WINDOWS"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "errors": {
                            "window": "not one of "
                            + ", ".join(current_app.config["PLAYGROUND_STATS_WINDOWS"])
                        },
                    }
                ),
                400,
            )
        try:
            stats = get_client().get(window)
        except StatsUnavailable as exc:
            return jsonify({"success": False, "errors": {"playground": str(exc)}}), 503
        return jsonify({"success": True, "data": stats})

    @playground_bp.route("/admin/playground_stats", methods=["GET"])
    @admins_only
    def admin_playground_stats():
        window = current_app.config["PLAYGROUND_STATS_WINDOW"]
        stats, error = None, None
        try:
            stats = get_client().fetch(window)
        except StatsUnavailable as exc:
            error = str(exc)
        settings = {
            key: current_app.config[key]
            for key in (
                "PLAYGROUND_STATS_URL",
                "PLAYGROUND_STATS_WINDOWS",
                "PLAYGROUND_STATS_WINDOW",
                "PLAYGROUND_STATS_REFRESH",
                "PLAYGROUND_STATS_TIMEOUT",
                "PLAYGROUND_STATS_CACHE",
            )
        }
        return render_template(
            "admin_playground_stats.html",
            settings=settings,
            stats=stats,
            error=error,
            window=window,
        )

    app.register_blueprint(playground_bp)

    register_admin_plugin_menu_bar("playground stats", "/admin/playground_stats")
    register_user_page_menu_bar("Playground", "/playground")
