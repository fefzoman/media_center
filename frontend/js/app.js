(function () {
  "use strict";

  var screens = {
    home: document.getElementById("home-screen"),
    detail: document.getElementById("detail-screen"),
    player: document.getElementById("player-screen")
  };
  var movieGrid = document.getElementById("movie-grid");
  var catalogStatus = document.getElementById("catalog-status");
  var catalogRetry = document.getElementById("catalog-retry");
  var detailBack = document.getElementById("detail-back");
  var detailPoster = document.getElementById("detail-poster");
  var detailTitle = document.getElementById("detail-title");
  var detailMeta = document.getElementById("detail-meta");
  var detailDescription = document.getElementById("detail-description");
  var playButton = document.getElementById("play-movie");
  var playStatus = document.getElementById("play-status");
  var playerBack = document.getElementById("player-back");
  var playerTitle = document.getElementById("player-title");
  var player = document.getElementById("player");
  var playerLoading = document.getElementById("player-loading");
  var playerError = document.getElementById("player-error");
  var playerErrorText = document.getElementById("player-error-text");
  var playerRetry = document.getElementById("player-retry");

  var state = {
    screen: "home",
    movie: null,
    selectedCardId: null,
    playPending: false
  };

  function requestJson(method, path, data, timeout, onSuccess, onFailure) {
    var request = new XMLHttpRequest();
    request.open(method, path, true);
    request.timeout = timeout;
    request.setRequestHeader("Accept", "application/json");
    if (data !== null) {
      request.setRequestHeader("Content-Type", "application/json");
    }
    request.onload = function () {
      var response;
      try {
        response = JSON.parse(request.responseText);
      } catch (error) {
        onFailure("The media server returned an invalid response.");
        return;
      }
      if (request.status >= 200 && request.status < 300) {
        onSuccess(response);
        return;
      }
      onFailure(response.detail || "The media server could not complete the request.");
    };
    request.onerror = function () {
      onFailure("The media server is unavailable. Check the network connection.");
    };
    request.ontimeout = function () {
      onFailure("The media server took too long to respond. Please try again.");
    };
    request.send(data === null ? null : JSON.stringify(data));
  }

  function showScreen(name) {
    var key;
    for (key in screens) {
      if (Object.prototype.hasOwnProperty.call(screens, key)) {
        screens[key].hidden = key !== name;
      }
    }
    state.screen = name;
  }

  function focusLater(element) {
    window.setTimeout(function () {
      if (element && !element.hidden) {
        element.focus();
      }
    }, 0);
  }

  function formatRuntime(seconds) {
    if (!seconds) { return ""; }
    var hours = Math.floor(seconds / 3600);
    var minutes = Math.round((seconds % 3600) / 60);
    if (hours) { return hours + "h " + minutes + "m"; }
    return minutes + "m";
  }

  function makeMovieCard(movie) {
    var card = document.createElement("button");
    var poster = document.createElement("img");
    var copy = document.createElement("span");
    var title = document.createElement("span");
    var year = document.createElement("span");

    card.type = "button";
    card.className = "movie-card";
    card.setAttribute("role", "listitem");
    card.setAttribute("data-focusable", "true");
    card.setAttribute("data-movie-id", movie.id);
    card.setAttribute("aria-label", movie.title + (movie.year ? ", " + movie.year : ""));
    card.onclick = function () { openMovie(movie.id); };

    poster.className = "movie-poster";
    poster.src = movie.poster_url || "/tv/assets/posters/fallback.svg";
    poster.alt = "";
    poster.onerror = function () {
      poster.onerror = null;
      poster.src = "/tv/assets/posters/fallback.svg";
    };

    copy.className = "movie-card-copy";
    title.className = "movie-title";
    title.textContent = movie.title;
    year.className = "movie-year";
    year.textContent = movie.year || "";
    copy.appendChild(title);
    copy.appendChild(year);
    card.appendChild(poster);
    card.appendChild(copy);
    return card;
  }

  function loadCatalog() {
    catalogStatus.textContent = "Loading your library…";
    catalogRetry.hidden = true;
    movieGrid.textContent = "";
    requestJson("GET", "/api/v1/movies", null, 8000, function (movies) {
      var i;
      if (!movies.length) {
        catalogStatus.textContent = "Your movie library is empty.";
        return;
      }
      catalogStatus.textContent = movies.length + (movies.length === 1 ? " movie" : " movies");
      for (i = 0; i < movies.length; i += 1) {
        movieGrid.appendChild(makeMovieCard(movies[i]));
      }
      focusLater(movieGrid.querySelector(".movie-card"));
    }, function (message) {
      catalogStatus.textContent = message;
      catalogRetry.hidden = false;
      focusLater(catalogRetry);
    });
  }

  function openMovie(movieId) {
    state.selectedCardId = movieId;
    playStatus.textContent = "Loading movie details…";
    playButton.disabled = true;
    showScreen("detail");
    focusLater(detailBack);
    requestJson("GET", "/api/v1/movies/" + encodeURIComponent(movieId), null, 8000, function (movie) {
      var meta = [];
      state.movie = movie;
      detailTitle.textContent = movie.title;
      detailPoster.src = movie.poster_url || "/tv/assets/posters/fallback.svg";
      detailPoster.alt = movie.title + " poster";
      detailPoster.onerror = function () {
        detailPoster.onerror = null;
        detailPoster.src = "/tv/assets/posters/fallback.svg";
      };
      if (movie.year) { meta.push(movie.year); }
      if (movie.runtime_seconds) { meta.push(formatRuntime(movie.runtime_seconds)); }
      detailMeta.textContent = meta.join(" · ");
      detailDescription.textContent = movie.description || "No description is available.";
      playStatus.textContent = "";
      playButton.disabled = false;
      focusLater(playButton);
    }, function (message) {
      state.movie = null;
      detailTitle.textContent = "Movie unavailable";
      detailMeta.textContent = "";
      detailDescription.textContent = message;
      playStatus.textContent = "Return to the library and try again.";
    });
  }

  function startPlayback() {
    if (!state.movie || state.playPending) { return; }
    state.playPending = true;
    playButton.disabled = true;
    playStatus.textContent = "Preparing the movie and loading torrent metadata…";
    requestJson(
      "POST",
      "/api/v1/movies/" + encodeURIComponent(state.movie.id) + "/play",
      {
        client_id: "tv-browser",
        capabilities: { h264: true, hevc: true, aac: true, hls: true }
      },
      130000,
      function (playback) {
        state.playPending = false;
        playButton.disabled = false;
        showPlayer(playback.url);
      },
      function (message) {
        state.playPending = false;
        playButton.disabled = false;
        playStatus.textContent = message;
        focusLater(playButton);
      }
    );
  }

  function showPlayer(url) {
    showScreen("player");
    playerTitle.textContent = state.movie ? state.movie.title : "Now playing";
    playerError.hidden = true;
    playerLoading.hidden = false;
    player.src = url;
    player.load();
    focusLater(player);
    var playResult = player.play();
    if (playResult && playResult.catch) {
      playResult.catch(function () {
        playerLoading.textContent = "Press OK to start playback.";
      });
    }
  }

  function stopPlayer() {
    player.pause();
    player.removeAttribute("src");
    player.load();
    playerError.hidden = true;
    playerLoading.hidden = false;
    playerLoading.textContent = "Buffering movie…";
  }

  function returnToDetails() {
    stopPlayer();
    showScreen("detail");
    focusLater(playButton);
  }

  function returnToCatalog() {
    var cards;
    var i;
    showScreen("home");
    cards = movieGrid.querySelectorAll(".movie-card");
    for (i = 0; i < cards.length; i += 1) {
      if (cards[i].getAttribute("data-movie-id") === state.selectedCardId) {
        focusLater(cards[i]);
        return;
      }
    }
    focusLater(cards[0] || catalogRetry);
  }

  function showPlaybackError(message) {
    playerLoading.hidden = true;
    playerErrorText.textContent = message || "Playback could not start. Check source availability and try again.";
    playerError.hidden = false;
    focusLater(playerRetry);
  }

  function seekBy(seconds) {
    if (!isFinite(player.duration)) { return; }
    player.currentTime = Math.max(0, Math.min(player.duration, player.currentTime + seconds));
  }

  function togglePlayback() {
    if (player.paused) {
      var result = player.play();
      if (result && result.catch) {
        result.catch(function () { showPlaybackError("Playback could not resume."); });
      }
    } else {
      player.pause();
    }
  }

  function visibleFocusableElements() {
    var nodes = document.querySelectorAll('[data-focusable="true"]');
    var visible = [];
    var i;
    for (i = 0; i < nodes.length; i += 1) {
      if (!nodes[i].disabled && nodes[i].offsetWidth > 0 && nodes[i].offsetHeight > 0) {
        visible.push(nodes[i]);
      }
    }
    return visible;
  }

  function moveFocus(direction) {
    var elements = visibleFocusableElements();
    var current = document.activeElement;
    var currentRect = current && current.getBoundingClientRect ? current.getBoundingClientRect() : null;
    var best = null;
    var bestScore = Infinity;
    var i;
    var currentX;
    var currentY;
    if (!currentRect) {
      focusLater(elements[0]);
      return;
    }
    currentX = currentRect.left + currentRect.width / 2;
    currentY = currentRect.top + currentRect.height / 2;
    for (i = 0; i < elements.length; i += 1) {
      var rect;
      var dx;
      var dy;
      var primary;
      var secondary;
      if (elements[i] === current) { continue; }
      rect = elements[i].getBoundingClientRect();
      dx = rect.left + rect.width / 2 - currentX;
      dy = rect.top + rect.height / 2 - currentY;
      if (direction === "left" && dx >= -1) { continue; }
      if (direction === "right" && dx <= 1) { continue; }
      if (direction === "up" && dy >= -1) { continue; }
      if (direction === "down" && dy <= 1) { continue; }
      primary = direction === "left" || direction === "right" ? Math.abs(dx) : Math.abs(dy);
      secondary = direction === "left" || direction === "right" ? Math.abs(dy) : Math.abs(dx);
      if (primary + secondary * 2 < bestScore) {
        bestScore = primary + secondary * 2;
        best = elements[i];
      }
    }
    if (best) { best.focus(); }
  }

  function handleKey(event) {
    var code = event.keyCode || event.which;
    var key = event.key;
    var isBack = code === 461 || code === 27 || code === 8 || key === "Escape" || key === "BrowserBack";
    if (isBack && state.screen !== "home") {
      event.preventDefault();
      if (state.screen === "player") { returnToDetails(); } else { returnToCatalog(); }
      return;
    }
    if (state.screen === "player") {
      if (code === 415) { event.preventDefault(); player.play(); return; }
      if (code === 19) { event.preventDefault(); player.pause(); return; }
      if (code === 413) { event.preventDefault(); returnToDetails(); return; }
      if (code === 412 || code === 37 || key === "ArrowLeft") { event.preventDefault(); seekBy(-10); return; }
      if (code === 417 || code === 39 || key === "ArrowRight") { event.preventDefault(); seekBy(10); return; }
      if (code === 13 || code === 32 || key === "Enter") { event.preventDefault(); togglePlayback(); }
      return;
    }
    if (code === 37 || key === "ArrowLeft") { event.preventDefault(); moveFocus("left"); }
    if (code === 38 || key === "ArrowUp") { event.preventDefault(); moveFocus("up"); }
    if (code === 39 || key === "ArrowRight") { event.preventDefault(); moveFocus("right"); }
    if (code === 40 || key === "ArrowDown") { event.preventDefault(); moveFocus("down"); }
  }

  catalogRetry.onclick = loadCatalog;
  detailBack.onclick = returnToCatalog;
  playButton.onclick = startPlayback;
  playerBack.onclick = returnToDetails;
  playerRetry.onclick = function () { returnToDetails(); startPlayback(); };
  player.addEventListener("loadstart", function () { playerLoading.hidden = false; });
  player.addEventListener("waiting", function () { playerLoading.hidden = false; });
  player.addEventListener("seeking", function () { playerLoading.hidden = false; });
  player.addEventListener("canplay", function () { playerLoading.hidden = true; });
  player.addEventListener("playing", function () { playerLoading.hidden = true; });
  player.addEventListener("error", function () { showPlaybackError(); });
  player.addEventListener("ended", returnToDetails);
  document.addEventListener("keydown", handleKey, false);
  window.addEventListener("pagehide", function () {
    if (state.screen === "player") { player.pause(); }
  });

  loadCatalog();
}());
