"""Configuration for the playground plugin.

Every option can be supplied either as an environment variable or through the
``[extra]`` section of ``CTFd/config.ini``. Environment variables win over
``config.ini`` so that a deployment can override a baked in value. The defaults
match a playground running on the host it ships with, on the ports it ships
with, so an unconfigured install shows something sensible.

Nothing here is asked of the playground at runtime: the page is rendered from
these values alone, so CTFd never talks to the playground at all.
"""

import os

DEFAULT_DOCS_URL = "https://github.com/jonathanlotan/attack_playground"


def envvar(app, key, default=None):
    """Read a value from the environment, then ``app.config``, then the default."""
    value = os.environ.get(key)

    if value is None:
        value = app.config.get(key)

    if value is None:
        return default

    return value


def strvar(app, key, default):
    """Read a stripped string; an empty value falls back to the default."""
    return str(envvar(app, key, default)).strip() or str(default)


def numvar(app, key, default, kind=int):
    """Read a numeric value; malformed values fall back to the default."""
    value = envvar(app, key, default)
    try:
        return kind(value)
    except (TypeError, ValueError):
        return kind(default)


def config(app):
    """Load the plugin configuration into ``app.config``."""

    # PLAYGROUND_SSH_HOST and PLAYGROUND_SSH_PORT are what a player types: the
    # address containerssh listens on, as reachable from wherever the players
    # are. The port is SSH_PORT from the playground's .env (2222 as shipped).
    # These are the players' route to the playground, not CTFd's - CTFd does
    # not connect to it.
    app.config["PLAYGROUND_SSH_HOST"] = strvar(
        app, "PLAYGROUND_SSH_HOST", "researchlabs"
    )

    port = numvar(app, "PLAYGROUND_SSH_PORT", 2222, int)
    app.config["PLAYGROUND_SSH_PORT"] = port if 1 <= port <= 65535 else 2222

    # PLAYGROUND_SSH_USER is the name the page suggests logging in with. The
    # playground's auth webhook accepts every name and every password, so this
    # is only the example; it is the name a guest falls back to when a client
    # sends none.
    app.config["PLAYGROUND_SSH_USER"] = strvar(
        app, "PLAYGROUND_SSH_USER", "guestuser"
    )

    # PLAYGROUND_GATEWAY_HOST is the name that, inside a session, resolves to
    # the address the exercise endpoints are exposed on. The playground defines
    # it in its config.yaml under docker.execution.host.extrahosts; ask the
    # playground for the current one with
    # "python3 scripts/render_config.py hostname".
    app.config["PLAYGROUND_GATEWAY_HOST"] = strvar(
        app, "PLAYGROUND_GATEWAY_HOST", "researchlabs.tech"
    )

    # PLAYGROUND_DOCS_URL is where "read the docs" on the page points.
    app.config["PLAYGROUND_DOCS_URL"] = strvar(
        app, "PLAYGROUND_DOCS_URL", DEFAULT_DOCS_URL
    )
