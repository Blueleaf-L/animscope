/**
 * Hash-based router.
 * Uses a dispatch counter to cancel stale navigations (no lock, no silent skip).
 */

var Router = {
  _routes: {},
  _currentPage: null,
  _dispatchId: 0,        // incrementing counter for cancellation

  on: function (pattern, handler) {
    this._routes[pattern] = handler;
  },

  navigate: function (hash) {
    window.location.hash = hash;
  },

  dispatch: function () {
    var self = this;
    var id = ++self._dispatchId;   // capture token for this dispatch

    var hash = window.location.hash.replace("#", "") || "overview";
    var parts = hash.split("?");
    var path = parts[0] || "overview";
    var query = {};

    if (parts[1]) {
      parts[1].split("&").forEach(function (pair) {
        var kv = pair.split("=");
        query[decodeURIComponent(kv[0])] = decodeURIComponent(kv[1] || "");
      });
    }

    // Find matching route
    var matchedHandler = null;
    var matchedParams = {};
    var routes = self._routes;

    for (var pattern in routes) {
      if (!routes.hasOwnProperty(pattern)) continue;
      var result = self._matchPattern(pattern, path);
      if (result) {
        matchedHandler = routes[pattern];
        matchedParams = result;
        break;
      }
    }

    // Update nav highlight
    self._updateNav(path);

    // Dispose old charts
    try { Charts.disposeAll(); } catch (_) {}

    if (!matchedHandler) {
      Views.showError("Page not found: " + path, function () { self.navigate("overview"); });
      return;
    }

    self._currentPage = path;

    // Run the handler (returns a promise)
    var promise = matchedHandler({ params: matchedParams, query: query });

    // Only render result if this dispatch is still the latest
    if (promise && promise.then) {
      promise.catch(function (err) {
        // Only show error for the latest dispatch
        if (id !== self._dispatchId) return;
        console.error("Page render error:", err);
        Views.showError("Page load failed: " + (err.message || "Unknown error"), function () {
          self.dispatch();
        });
      });
    }
  },

  _matchPattern: function (pattern, path) {
    var patternParts = pattern.split("/");
    var pathParts = path.split("/");
    if (patternParts.length !== pathParts.length) return null;
    var params = {};
    for (var i = 0; i < patternParts.length; i++) {
      if (patternParts[i].charAt(0) === ":") {
        params[patternParts[i].slice(1)] = pathParts[i];
      } else if (patternParts[i] !== pathParts[i]) {
        return null;
      }
    }
    return params;
  },

  _updateNav: function (path) {
    var links = document.querySelectorAll(".site-nav a");
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      var href = a.getAttribute("href");
      if (href) href = href.replace("#", "");
      var active = (href === path || (href && path.indexOf(href + "/") === 0));
      if (active) {
        a.classList.add("active");
      } else {
        a.classList.remove("active");
      }
    }
  },
};

// Listen for hash changes
window.addEventListener("hashchange", function () {
  Router.dispatch();
});

// Listen for heatmap click events for drill-down
document.addEventListener("heatmap-click", function (evt) {
  // handled by the trends page itself
});
