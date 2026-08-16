/* Click any research / tracks figure to view it at native (original) size. */
(function () {
  var SELECTOR = ".paper-figs img, .tracks-figure img";

  function ensureLightbox() {
    var box = document.getElementById("fig-lightbox");
    if (box) return box;

    box = document.createElement("div");
    box.id = "fig-lightbox";
    box.className = "fig-lightbox";
    box.setAttribute("hidden", "");
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Full-size figure");
    box.innerHTML =
      '<button type="button" class="fig-lightbox-close" aria-label="Close">&times;</button>' +
      '<img class="fig-lightbox-img" alt="">' +
      '<p class="fig-lightbox-hint">Click outside the image or press Esc to close</p>';
    document.body.appendChild(box);

    box.addEventListener("click", function (e) {
      if (e.target === box || e.target.classList.contains("fig-lightbox-close")) {
        closeLightbox();
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !box.hasAttribute("hidden")) closeLightbox();
    });

    return box;
  }

  function openLightbox(src, alt) {
    var box = ensureLightbox();
    var img = box.querySelector(".fig-lightbox-img");
    img.onload = function () {
      var scale = 1.2;
      img.style.width = Math.round(img.naturalWidth * scale) + "px";
      img.style.height = Math.round(img.naturalHeight * scale) + "px";
    };
    img.src = src;
    img.alt = alt || "";
    // If the image is already cached, onload may have fired; apply size now too.
    if (img.complete && img.naturalWidth) {
      img.style.width = Math.round(img.naturalWidth * 1.2) + "px";
      img.style.height = Math.round(img.naturalHeight * 1.2) + "px";
    }
    box.removeAttribute("hidden");
    document.body.classList.add("fig-lightbox-open");
    box.scrollTop = 0;
    box.scrollLeft = 0;
  }

  function closeLightbox() {
    var box = document.getElementById("fig-lightbox");
    if (!box) return;
    box.setAttribute("hidden", "");
    document.body.classList.remove("fig-lightbox-open");
    var img = box.querySelector(".fig-lightbox-img");
    img.removeAttribute("src");
    img.removeAttribute("style");
    img.alt = "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(SELECTOR).forEach(function (img) {
      img.setAttribute("title", "Click to view full size");
      img.addEventListener("click", function () {
        openLightbox(img.currentSrc || img.src, img.alt);
      });
    });
  });
})();
