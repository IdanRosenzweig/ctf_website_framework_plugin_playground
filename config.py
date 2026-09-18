"""Configuration for the playground stats plugin.

Every option can be supplied either as an environment variable or through the
``[extra]`` section of ``CTFd/config.ini``. Environment variables win over
``config.ini`` so that a deployment can override a baked in value. The defaults
match a playground running on the same machine as CTFd with the ports it ships
with, so an unconfigured install works as is.
"""

import os
import re

# a window as the stats server accepts it: seconds, or a count with a unit
WINDOW_RE = re.compile(r"(\d+)([smhd]?)", re.ASCII)
WINDOW_UNITS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}


def envvar(app, key, default=None):
    """Read a value from the environment, then ``app.config``, then the default."""
    value = os.environ.get(key)

    if value is None:
        value = app.config.get(key)

    if value is None:
        return default

    return value


def numvar(app, key, default, kind=float):
    """Read a numeric value; malformed values fall back to the default."""
    value = envvar(app, key, default)
    try:
        return kind(value)
    except (TypeError, ValueError):
        return kind(default)


def listvar(app, key, default):
    """Read a comma separated value into a list of stripped strings."""
    value = envvar(app, key, default)

    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]

    return [item.strip() for item in str(value).split(",") if item.strip()]


def window_seconds(text):
    """The length of a window in seconds, or None when it is not a window."""
    match = WINDOW_RE.fullmatch(str(text).strip().lower())
    if not match:
        return None
    seconds = int(match.group(1)) * WINDOW_UNITS[match.group(2)]
    return seconds or None


def describe_window(seconds):
    """A window for a label: 900 -> "15 minutes", 3600 -> "hour", 86400 -> "day"."""
    for unit, name in ((86400, "day"), (3600, "hour"), (60, "minute")):
        if seconds % unit == 0:
            count = seconds // unit
            return name if count == 1 else f"{count} {name}s"
    return "second" if seconds == 1 else f"{seconds} seconds"


def config(app):
    """Load the plugin configuration into ``app.config``."""

    # PLAYGROUND_STATS_URL is where the stats server answers: the playground host
    # on STATS_PORT from its .env (2224 as shipped). CTFd runs in its own docker
    # sandbox, where 127.0.0.1 is the CTFd container itself, so the default names
    # the host and docker-compose.yml maps that name to the docker host. A
    # trailing "/stats" is optional.
    url = str(envvar(app, "PLAYGROUND_STATS_URL", "http://researchlabs:2224")).rstrip(
        "/"
    )
    if url.endswith("/stats"):
        url = url[: -len("/stats")]
    app.config["PLAYGROUND_STATS_URL"] = url

    # PLAYGROUND_STATS_WINDOWS lists the "connected in the last ..." windows the
    # page lets a viewer pick from, in the stats server's own notation (seconds,
    # or a count with s, m, h or d). Only these are ever requested upstream.
    windows = []
    for window in listvar(app, "PLAYGROUND_STATS_WINDOWS", "15m,1h,24h,7d"):
        if window_seconds(window) and window not in windows:
            windows.append(window)
    if not windows:
        windows = ["1h"]
    app.config["PLAYGROUND_STATS_WINDOWS"] = windows

    # PLAYGROUND_STATS_WINDOW is the window the page opens with. It has to be
    # one of the windows above; otherwise the first of them is used.
    window = str(envvar(app, "PLAYGROUND_STATS_WINDOW", "1h")).strip().lower()
    if window not in windows:
        window = windows[0]
    app.config["PLAYGROUND_STATS_WINDOW"] = window

    # PLAYGROUND_STATS_REFRESH is how often, in seconds, the page asks for fresh
    # numbers while it is open. 0 turns the polling off.
    app.config["PLAYGROUND_STATS_REFRESH"] = max(
        0, numvar(app, "PLAYGROUND_STATS_REFRESH", 5, int)
    )

    # PLAYGROUND_STATS_TIMEOUT bounds how long a request to the stats server may
    # take, in seconds, so an unresponsive server cannot hang a CTFd worker.
    app.config["PLAYGROUND_STATS_TIMEOUT"] = max(
        0.1, numvar(app, "PLAYGROUND_STATS_TIMEOUT", 2.0)
    )

    # PLAYGROUND_STATS_CACHE is how long, in seconds, an answer from the stats
    # server is reused before it is fetched again, so that many open pages add
    # up to one request per window every few seconds rather than one each. An
    # unreachable server is remembered for the same time.
    app.config["PLAYGROUND_STATS_CACHE"] = max(
        0.0, numvar(app, "PLAYGROUND_STATS_CACHE", 2.0)
    )
