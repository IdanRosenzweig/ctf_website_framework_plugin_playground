from flask import Blueprint, redirect, render_template, request, url_for

from CTFd.plugins import (
    register_admin_plugin_menu_bar,
    register_user_page_menu_bar,
)
from CTFd.utils.decorators import admins_only

from .config import (
    SETTINGS,
    all_settings,
    config,
    reset_settings,
    set_setting,
    setting_sources,
    validate_settings,
)


def load(app):
    config(app)

    playground_bp = Blueprint(
        "playground",
        __name__,
        template_folder="templates",
        static_folder="assets",
        static_url_path="/plugins/ctfd_plugin_playground/assets",
    )

    @playground_bp.route("/playground", methods=["GET"])
    def playground_page():
        return render_template("playground.html", **all_settings())

    @playground_bp.route("/admin/playground", methods=["GET", "POST"])
    @admins_only
    def admin_page():
        error = None

        if request.method == "POST":
            action = request.form.get("action", "save")

            if action == "reset":
                reset_settings()
                return redirect(url_for("playground.admin_page", reset="1"))

            if action == "save":
                submitted = {}
                for name, setting in SETTINGS.items():
                    # Environment-controlled fields are disabled in the form
                    # and therefore absent from the submission.
                    key = setting["config_key"]
                    if key in request.form:
                        submitted[name] = request.form[key]

                try:
                    submitted = validate_settings(submitted)
                except ValueError as exc:
                    error = str(exc)
                else:
                    for name, value in submitted.items():
                        set_setting(name, value)
                    return redirect(url_for("playground.admin_page", saved="1"))

        message = None
        if request.args.get("saved") == "1":
            message = "Playground settings saved."
        elif request.args.get("reset") == "1":
            message = "Dashboard overrides cleared; deployment settings now apply."

        return render_template(
            "playground_admin.html",
            settings=all_settings(),
            sources=setting_sources(),
            message=message,
            error=error,
        )

    app.register_blueprint(playground_bp)

    register_user_page_menu_bar("Playground", "/playground")
    register_admin_plugin_menu_bar("Playground", "/admin/playground")
