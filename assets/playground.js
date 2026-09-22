// The one piece of behaviour on the playground page: copying the ssh command.
// The command is on screen and selectable without this, so every failure here
// just leaves the button alone.
(function () {
  "use strict";

  var button = document.getElementById("pg-copy");
  var label = document.getElementById("pg-copy-text");
  if (!button || !label) {
    return;
  }

  var RESTORE_AFTER = 1500;
  var restore = null;

  function say(text) {
    label.textContent = text;
    clearTimeout(restore);
    restore = setTimeout(function () {
      label.textContent = "Copy";
    }, RESTORE_AFTER);
  }

  // The clipboard api is the good path, but it is absent on a page that is not
  // served over https and it rejects where the
  // browser does not credit the click as a user gesture. Either way the
  // selection trick below still works, so it is the fallback rather than a
  // second best.
  function bySelection(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "0";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      return document.execCommand("copy");
    } catch (e) {
      return false;
    } finally {
      document.body.removeChild(area);
    }
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () {
        if (!bySelection(text)) {
          throw new Error("copy refused");
        }
      });
    }

    return bySelection(text)
      ? Promise.resolve()
      : Promise.reject(new Error("copy refused"));
  }

  button.addEventListener("click", function () {
    copy(button.dataset.command).then(
      function () {
        say("Copied");
      },
      function () {
        say("Copy failed");
      }
    );
  });
})();
