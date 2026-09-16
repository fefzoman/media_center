(function () {
  "use strict";

  var status = document.getElementById("server-status");
  var button = document.getElementById("check-server");
  var pending = false;

  function checkServer() {
    if (pending) { return; }
    pending = true;
    status.textContent = "Checking media server…";

    var request = new XMLHttpRequest();
    request.open("GET", "/api/v1/health", true);
    request.timeout = 5000;
    request.onload = function () {
      pending = false;
      try {
        if (request.status === 200 && JSON.parse(request.responseText).status === "ok") {
          status.textContent = "Media server connected.";
          return;
        }
      } catch (error) {
        // Malformed responses have the same recovery action as a failed request.
      }
      status.textContent = "Media server unavailable. Check your connection and try again.";
    };
    request.onerror = request.ontimeout = function () {
      pending = false;
      status.textContent = "Media server unavailable. Check your connection and try again.";
    };
    request.send();
  }

  button.onclick = checkServer;
  button.focus();
  checkServer();
}());
