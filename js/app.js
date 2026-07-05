/**
 * Application entry point.
 * Initializes: theme -> skeleton -> routing -> render.
 */

(function () {
  "use strict";

  // -- Theme ----------------------------------------------
  var THEME_KEY = "animscope-theme";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
    var btn = document.getElementById("theme-toggle");
    if (btn) btn.textContent = theme === "dark" ? "Sun" : "Moon";
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute("data-theme");
    applyTheme(current === "dark" ? "light" : "dark");
    // Re-render charts on current page after theme change
    Router.dispatch();
  }

  function initTheme() {
    var saved = localStorage.getItem(THEME_KEY);
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(saved || (prefersDark ? "dark" : "light"));

    var btn = document.getElementById("theme-toggle");
    if (btn) btn.addEventListener("click", toggleTheme);
  }

  // -- Responsive chart resize (debounced) ---------------
  var resizeTimer = null;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      Object.values(Charts._instances).forEach(function (inst) { inst.resize(); });
    }, CONFIG.DEBOUNCE_MS);
  });

  // -- Register Routes (bind so 'this' works inside render) --
  Router.on("overview", Pages.Overview.render.bind(Pages.Overview));
  Router.on("companies", Pages.Companies.render.bind(Pages.Companies));
  Router.on("company/:id", Pages.CompanyDetail.render.bind(Pages.CompanyDetail));
  Router.on("rankings", Pages.Rankings.render.bind(Pages.Rankings));
  Router.on("trends", Pages.Trends.render.bind(Pages.Trends));
  Router.on("compare", Pages.Compare.render.bind(Pages.Compare));
  Router.on("search", Pages.Search.render.bind(Pages.Search));
  Router.on("report", Pages.Report.render.bind(Pages.Report));

  // -- Initialize -----------------------------------------
  function init() {
    initTheme();

    // Show skeleton, then dispatch (don't preload — dispatch handles it)
    Views.showSkeleton();

    // Wait for dispatch to complete before accepting nav clicks
    Router.dispatch().catch(function (err) {
      console.error("Initial dispatch failed:", err);
    });
  }

  // Start when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // -- Export Pages namespace (populated by page modules) --
  window.Pages = window.Pages || {};
})();
