(function () {
  "use strict";
  var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
  var q = document.getElementById("q");
  var n = document.getElementById("n");
  var empty = document.querySelector(".empty");
  var state = { q: "", cat: "all", scheme: "all" };

  function apply() {
    var shown = 0, term = state.q.trim().toLowerCase();
    cards.forEach(function (c) {
      var ok = (state.cat === "all" || c.dataset.cat === state.cat) &&
               (state.scheme === "all" || c.dataset.scheme === state.scheme) &&
               (!term || c.dataset.q.indexOf(term) > -1);
      c.hidden = !ok;
      if (ok) shown++;
    });
    n.textContent = shown;
    empty.hidden = shown > 0;
  }

  q.addEventListener("input", function () { state.q = q.value; apply(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    if (e.key === "Escape" && document.activeElement === q) { q.value = ""; state.q = ""; apply(); q.blur(); }
  });

  function group(attr, key) {
    document.querySelectorAll("[data-" + attr + "]").forEach(function (b) {
      b.addEventListener("click", function () {
        var sibs = b.parentNode.querySelectorAll("[data-" + attr + "]");
        Array.prototype.forEach.call(sibs, function (s) { s.classList.toggle("is-on", s === b); });
        state[key] = b.dataset[attr];
        apply();
      });
    });
  }
  group("cat", "cat");
  group("scheme", "scheme");

  /* theme toggle — remembers per browser, tolerates blocked storage */
  var root = document.documentElement;
  var btn = document.querySelector(".theme");
  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  var saved = load("dl-theme");
  if (saved) root.setAttribute("data-theme", saved);
  function paint() {
    var dark = root.getAttribute("data-theme") === "dark" ||
      (!root.getAttribute("data-theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
    btn.querySelector("i").className = "ph " + (dark ? "ph-sun" : "ph-moon");
    btn.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
  }
  btn.addEventListener("click", function () {
    var dark = root.getAttribute("data-theme") === "dark" ||
      (!root.getAttribute("data-theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next); store("dl-theme", next); paint();
  });
  paint();
  apply();
})();
