"""Configuration helpers for the playground plugin.

Settings saved in the admin dashboard live in CTFd's ``Configs`` table. A
deployment can still force a value with an environment variable; otherwise a
dashboard value takes precedence over ``config.ini`` and the built-in default.
"""

import os

from flask import current_app

from CTFd.utils import get_config, set_config


NAMESPACE = "playground"

SETTINGS = {
    "ssh_host": {
        "config_key": "PLAYGROUND_SSH_HOST",
        "default": "researchlabs.tech",
    },
    "ssh_port": {
        "config_key": "PLAYGROUND_SSH_PORT",
        "default": 2222,
    },
    "ssh_user": {
        "config_key": "PLAYGROUND_SSH_USER",
        "default": "guestuser",
    },
    "gateway_host": {
        "config_key": "PLAYGROUND_GATEWAY_HOST",
        "default": "researchlabs.tech",
    },
}


def _stored_key(name):
    return "{}:{}".format(NAMESPACE, name)


def _coerce(name, value):
    """Validate and normalize one setting."""
    if name not in SETTINGS:
        raise KeyError("Unknown playground setting: {}".format(name))

    if name == "ssh_port":
        try:
            port = int(value)
        except (TypeError, ValueError):
            raise ValueError(
                "SSH port must be a number between 1 and 65535."
            ) from None
        if not 1 <= port <= 65535:
            raise ValueError("SSH port must be a number between 1 and 65535.")
        return port

    value = "" if value is None else str(value).strip()
    if not value:
        raise ValueError("All fields are required.")
    if len(value) > 255:
        raise ValueError("Host names and usernames must be 255 characters or fewer.")
    return value


def _deployment_value(name):
    setting = SETTINGS[name]
    value = current_app.config.get(setting["config_key"], setting["default"])
    try:
        return _coerce(name, value)
    except ValueError:
        return setting["default"]


def get_setting(name):
    """Return the effective value of a setting.

    Environment variables are deployment-level overrides. Dashboard values
    come next, followed by values loaded from ``config.ini`` and the default.
    """
    if name not in SETTINGS:
        raise KeyError("Unknown playground setting: {}".format(name))

    environment_key = SETTINGS[name]["config_key"]
    if environment_key in os.environ:
        try:
            return _coerce(name, os.environ[environment_key])
        except ValueError:
            return SETTINGS[name]["default"]

    stored = get_config(_stored_key(name), default=None)
    if stored is not None:
        try:
            return _coerce(name, stored)
        except ValueError:
            return SETTINGS[name]["default"]

    return _deployment_value(name)


def set_setting(name, value):
    """Validate and persist a dashboard setting."""
    value = _coerce(name, value)
    set_config(_stored_key(name), value)
    return value


def validate_settings(values):
    """Validate a collection without persisting a partial update."""
    return {name: _coerce(name, value) for name, value in values.items()}


def reset_settings():
    """Remove dashboard overrides so deployment values apply again."""
    for name in SETTINGS:
        set_config(_stored_key(name), None)


def all_settings():
    return {name: get_setting(name) for name in SETTINGS}


def setting_sources():
    """Describe which layer supplies each effective setting for the UI."""
    sources = {}
    for name, setting in SETTINGS.items():
        if setting["config_key"] in os.environ:
            sources[name] = "environment"
        elif get_config(_stored_key(name), default=None) is not None:
            sources[name] = "dashboard"
        else:
            sources[name] = "config.ini or default"
    return sources


def config(app):
    """Normalize deployment-provided values in ``app.config``.

    This retains the plugin's original ``current_app.config`` interface for
    other code while request handlers use :func:`get_setting` so dashboard
    changes take effect immediately.
    """
    for name, setting in SETTINGS.items():
        key = setting["config_key"]
        raw_value = os.environ.get(key, app.config.get(key, setting["default"]))
        try:
            app.config[key] = _coerce(name, raw_value)
        except ValueError:
            app.config[key] = setting["default"]
