"""The attack playground, introduced inside CTFd.

The playground is a service of its own: ssh into it and you get a throwaway
Ubuntu container to attack from, on a network that reaches the exercise
endpoints and nothing else. This plugin adds one page, ``/playground``, listed
in the user menu, which says what the playground is and how to connect to it.

The page is rendered from configuration alone - CTFd never talks to the
playground - so it works whether or not the playground is up.

See README.md for the settings.
"""

from flask import Blueprint, current_app, render_template

from CTFd.plugins import register_user_page_menu_bar

from .config import config


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
        return render_template(
            "playground.html",
            ssh_host=current_app.config["PLAYGROUND_SSH_HOST"],
            ssh_port=current_app.config["PLAYGROUND_SSH_PORT"],
            ssh_user=current_app.config["PLAYGROUND_SSH_USER"],
            gateway_host=current_app.config["PLAYGROUND_GATEWAY_HOST"],
            docs_url=current_app.config["PLAYGROUND_DOCS_URL"],
        )

    app.register_blueprint(playground_bp)

    register_user_page_menu_bar("Playground", "/playground")
