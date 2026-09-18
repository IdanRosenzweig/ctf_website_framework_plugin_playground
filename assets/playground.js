// Keeps the /playground page fresh: polls CTFd's stats endpoint every few
// seconds while the tab is visible, lets the viewer change the window, and
// shows how old the numbers on screen are.
(function () {
  "use strict";

  var root = document.getElementById("playground-stats");
  if (!root) {
    return;
  }

  var api = root.dataset.api;
  var refresh = parseInt(root.dataset.refresh, 10) || 0;
  var window_ = root.dataset.window;

  var el = {
    status: document.getElementById("pg-status"),
    statusIcon: document.getElementById("pg-status-icon"),
    statusText: document.getElementById("pg-status-text"),
    updated: document.getElementById("pg-updated"),
    current: document.getElementById("pg-current"),
    inWindow: document.getElementById("pg-window"),
    windowLabel: document.getElementById("pg-window-label"),
    ever: document.getElementById("pg-ever"),
    error: document.getElementById("pg-error"),
    errorText: document.getElementById("pg-error-text"),
  };

  var STATES = {
    live: { icon: "fa-check-circle", text: "Live" },
    stale: { icon: "fa-pause-circle", text: "Stale" },
    unavailable: { icon: "fa-times-circle", text: "Unavailable" },
  };

  var lastUpdate = null; // Date of the last successful answer
  var timer = null;
  var inFlight = false;

  function setState(state) {
    el.status.dataset.state = state;
    el.statusIcon.className = "fas " + STATES[state].icon;
    el.statusText.textContent = STATES[state].text;
    el.status.title = {
      live: "The stats server is following the playground; these numbers are current.",
      stale: "The stats server is up but not following docker right now; these numbers may be out of date.",
      unavailable: "CTFd could not reach the stats server; these are the last numbers it saw.",
    }[state];
  }

  function formatCount(n) {
    return typeof n === "number" ? n.toLocaleString() : "–";
  }

  function render(stats) {
    el.current.textContent = formatCount(stats.currently_connected);
    el.inWindow.textContent = formatCount(stats.connected_in_window);
    el.ever.textContent = formatCount(stats.ever_connected);
    setState(stats.collector && stats.collector.connected ? "live" : "stale");
    el.error.classList.add("d-none");
    lastUpdate = new Date();
    renderAge();
  }

  function renderError(message) {
    setState("unavailable");
    el.errorText.textContent = message;
    el.error.classList.remove("d-none");
    renderAge();
  }

  function renderAge() {
    if (!lastUpdate) {
      el.updated.textContent = "";
      return;
    }
    var seconds = Math.max(0, Math.round((Date.now() - lastUpdate.getTime()) / 1000));
    el.updated.textContent =
      seconds < 2 ? "Updated just now" : "Updated " + seconds + "s ago";
  }

  function poll() {
    if (inFlight) {
      return;
    }
    inFlight = true;
    root.classList.add("pg-loading");
    fetch(api + "?window=" + encodeURIComponent(window_), {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (result) {
        if (result.ok && result.body && result.body.success) {
          render(result.body.data);
        } else {
          var errors = (result.body && result.body.errors) || {};
          renderError(
            errors.playground || errors.window || "The stats endpoint answered with an error."
          );
        }
      })
      .catch(function () {
        renderError("CTFd could not be reached.");
      })
      .finally(function () {
        inFlight = false;
        root.classList.remove("pg-loading");
      });
  }

  function start() {
    stop();
    if (refresh > 0) {
      timer = setInterval(poll, refresh * 1000);
    }
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  }

  // window picker
  root.querySelectorAll(".pg-window-picker [data-window]").forEach(function (button) {
    button.addEventListener("click", function () {
      if (button.dataset.window === window_) {
        return;
      }
      window_ = button.dataset.window;
      root.querySelectorAll(".pg-window-picker [data-window]").forEach(function (other) {
        var active = other === button;
        other.classList.toggle("btn-primary", active);
        other.classList.toggle("btn-outline-secondary", !active);
      });
      el.windowLabel.textContent = button.dataset.label;
      poll();
      start();
    });
  });

  // the numbers rendered into the page count as an update
  var initial = document.getElementById("playground-stats-initial");
  try {
    if (initial && JSON.parse(initial.textContent) !== null) {
      lastUpdate = new Date();
    }
  } catch (e) {
    // no initial numbers; the first poll fills them in
  }
  renderAge();
  setInterval(renderAge, 1000);

  // poll only while someone is looking, and catch up as soon as they are back
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      stop();
    } else {
      poll();
      start();
    }
  });

  if (!document.hidden) {
    if (!lastUpdate) {
      poll();
    }
    start();
  }
})();
