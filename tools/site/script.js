// The Geometry of Everything: small reading aids. Works without it.
(function () {
  "use strict";
  var root = document.documentElement;

  // theme: remembered per reader, falls back to the system setting
  try {
    var saved = localStorage.getItem("goe-theme-v2");
    if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  } catch (e) { /* storage unavailable */ }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.querySelector(".theme-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var dark = root.getAttribute("data-theme") === "dark" ||
          (!root.getAttribute("data-theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
        var next = dark ? "light" : "dark";
        root.setAttribute("data-theme", next);
        try { localStorage.setItem("goe-theme-v2", next); } catch (e) { /* ignore */ }
      });
    }

    // reading progress
    var bar = document.querySelector(".progress");
    if (bar) {
      var update = function () {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        bar.style.transform = "scaleX(" + (max > 0 ? h.scrollTop / max : 0) + ")";
      };
      document.addEventListener("scroll", update, { passive: true });
      update();
    }

    // ← and → turn the page
    document.addEventListener("keydown", function (ev) {
      if (ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
      var t = ev.target && ev.target.tagName;
      if (t === "INPUT" || t === "TEXTAREA") return;
      var link = null;
      if (ev.key === "ArrowLeft") link = document.querySelector('link[rel="prev"]');
      if (ev.key === "ArrowRight") link = document.querySelector('link[rel="next"]');
      if (link) window.location.href = link.getAttribute("href");
    });
  });
})();
