(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* mobile nav ---------------------------------------------------------- */
  var burger = document.querySelector(".nav-burger");
  var panel = document.getElementById("mnav");
  if (burger && panel) {
    burger.addEventListener("click", function () {
      var open = panel.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      burger.querySelector("i").className = "ph " + (open ? "ph-x" : "ph-list");
    });
    panel.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        panel.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
        burger.querySelector("i").className = "ph ph-list";
      }
    });
  }

  /* jump to spec -------------------------------------------------------- */
  /* Publish the height of the sticky chrome (library bar + the design's nav, when
     that nav is sticky) so anchor jumps can land below it instead of behind it.
     Nav height varies by design, so it has to be measured rather than assumed. */
  function chromeHeight() {
    var bar = document.querySelector(".libbar");
    var nav = document.querySelector(".nav");
    var h = bar ? bar.getBoundingClientRect().height : 0;
    if (nav && getComputedStyle(nav).position === "sticky") {
      h += nav.getBoundingClientRect().height;
    }
    document.documentElement.style.setProperty("--chrome-h", Math.round(h) + "px");
  }
  chromeHeight();
  window.addEventListener("resize", chromeHeight);

  var jump = document.querySelector("[data-jump]");
  if (jump) {
    jump.addEventListener("click", function () {
      var t = document.querySelector(jump.getAttribute("data-jump"));
      if (t) t.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    });
  }

  /* scroll reveal ------------------------------------------------------- */
  var items = document.querySelectorAll(".reveal");
  if (reduce || !("IntersectionObserver" in window)) {
    items.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* copy colour tokens -------------------------------------------------- */
  document.querySelectorAll(".sw").forEach(function (sw) {
    sw.addEventListener("click", function () {
      var val = sw.getAttribute("data-copy");
      var done = function () {
        var name = sw.querySelector(".sw-val");
        var old = name.textContent;
        sw.classList.add("copied");
        name.textContent = "copied";
        setTimeout(function () { name.textContent = old; sw.classList.remove("copied"); }, 1100);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(val).then(done).catch(done);
      } else {
        var ta = document.createElement("textarea");
        ta.value = val; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); } catch (e) {}
        document.body.removeChild(ta); done();
      }
    });
  });

  /* demo tabs ----------------------------------------------------------- */
  document.querySelectorAll(".tabs").forEach(function (tabs) {
    tabs.addEventListener("click", function (e) {
      var b = e.target.closest("button");
      if (!b) return;
      tabs.querySelectorAll("button").forEach(function (x) {
        x.setAttribute("aria-selected", String(x === b));
      });
    });
  });
})();
