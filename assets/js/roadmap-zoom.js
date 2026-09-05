/* Zoom the SIDM roadmap into a full-screen, scrollable view.
   On narrow screens the inline SVG is a static, non-interactive preview
   (node links disabled via CSS pointer-events: none); tapping the preview or
   the "Enlarge" button opens this lightbox showing the diagram at a
   comfortable, readable width. */
(function () {
  "use strict";

  var BUTTON_SELECTOR = ".roadmap-zoom";
  var SRC_SELECTOR = ".roadmap-svg";
  var SCROLL_SELECTOR = ".roadmap-scroll";
  var LIGHTBOX_WIDTH = "1500px";

  function ensureBox() {
    var box = document.getElementById("roadmap-lightbox");
    if (box) return box;

    box = document.createElement("div");
    box.id = "roadmap-lightbox";
    box.className = "fig-lightbox roadmap-lightbox";
    box.setAttribute("hidden", "");
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Full-size roadmap");
    box.innerHTML =
      '<button type="button" class="fig-lightbox-close" aria-label="Close">&times;</button>' +
      '<div class="fig-lightbox-svg-wrap"></div>' +
      '<p class="fig-lightbox-hint">Scroll to pan &middot; click outside or press Esc to close</p>';
    document.body.appendChild(box);

    box.addEventListener("click", function (e) {
      if (e.target === box || e.target.classList.contains("fig-lightbox-close")) {
        closeBox();
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !box.hasAttribute("hidden")) closeBox();
    });

    return box;
  }

  function openBox() {
    var src = document.querySelector(SRC_SELECTOR);
    if (!src) return;

    var box = ensureBox();
    var wrap = box.querySelector(".fig-lightbox-svg-wrap");
    wrap.innerHTML = "";

    var clone = src.cloneNode(true);
    clone.classList.add("roadmap-svg--lightbox");
    clone.style.width = LIGHTBOX_WIDTH;
    clone.style.maxWidth = "none";
    clone.style.height = "auto";
    wrap.appendChild(clone);

    box.removeAttribute("hidden");
    document.body.classList.add("fig-lightbox-open");
    box.scrollTop = 0;
    box.scrollLeft = 0;
  }

  function closeBox() {
    var box = document.getElementById("roadmap-lightbox");
    if (!box) return;
    box.setAttribute("hidden", "");
    document.body.classList.remove("fig-lightbox-open");
    var wrap = box.querySelector(".fig-lightbox-svg-wrap");
    if (wrap) wrap.innerHTML = "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.querySelector(BUTTON_SELECTOR);
    if (btn) btn.addEventListener("click", openBox);

    // On narrow screens the preview SVG is static (pointer-events: none), so a
    // tap anywhere in the scroll wrapper opens the lightbox.
    document.querySelectorAll(SCROLL_SELECTOR).forEach(function (w) {
      w.addEventListener("click", function () {
        if (window.matchMedia("(max-width: 760px)").matches) openBox();
      });
    });
  });
})();
