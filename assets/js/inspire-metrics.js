/* Populate publication / citation metrics live from the INSPIRE-HEP API.
   Fetches every paper attributed to this author, then sums citations overall
   and for first-author papers. Values land in elements with data-metric="…". */
(function () {
  var AUTHOR_ID = "1713307";
  var SIZE = 250;
  var API_URL =
    "https://inspirehep.net/api/literature?q=a%20Zhichao.Zeng.1&size=" + SIZE +
    "&fields=citation_count,first_author";

  function fetchAll(url, acc) {
    acc = acc || [];
    return fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        var hits = data.hits.hits || [];
        acc = acc.concat(hits);
        var next = data.links && data.links.next;
        if (next && hits.length === SIZE) return fetchAll(next, acc);
        return acc;
      });
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var root = document.getElementById("inspire-metrics");
    if (!root) return;

    function set(key, value) {
      var el = root.querySelector('[data-metric="' + key + '"]');
      if (el) el.textContent = value.toLocaleString("en-US");
    }

    fetchAll(API_URL)
      .then(function (hits) {
        var papers = hits.length;
        var citations = 0;
        var firstAuthor = 0;
        hits.forEach(function (h) {
          var m = h.metadata || {};
          citations += m.citation_count || 0;
          if (m.first_author && String(m.first_author.recid) === AUTHOR_ID) {
            firstAuthor += m.citation_count || 0;
          }
        });
        set("papers", papers);
        set("citations", citations);
        set("first-author", firstAuthor);
        root.classList.add("is-loaded");
      })
      .catch(function () {
        root.classList.add("is-error");
      });
  });
})();
