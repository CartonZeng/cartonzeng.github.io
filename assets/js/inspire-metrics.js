/* Populate publication / citation metrics live from the INSPIRE-HEP API.
   Fetches every paper attributed to this author, then computes:
     - papers            total paper count
     - citations         total citation count
     - first-author-papers   number of first-authored papers
     - first-author      citations to first-authored papers
   Values land in elements with data-metric="…" inside any container marked
   data-metrics. Runs once per page and fills every matching container. */
(function () {
  var AUTHOR_ID = "1713307";
  var SIZE = 250;
  var API_URL =
    "https://inspirehep.net/api/literature?q=a%20Zhichao.Zeng.1&size=" + SIZE +
    "&fields=citation_count,first_author,document_type";

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
    var roots = Array.prototype.slice.call(document.querySelectorAll("[data-metrics]"));
    if (!roots.length) return;

    function setAll(key, value) {
      roots.forEach(function (root) {
        var el = root.querySelector('[data-metric="' + key + '"]');
        if (el) el.textContent = value.toLocaleString("en-US");
      });
    }

    fetchAll(API_URL)
      .then(function (hits) {
        // Exclude theses and other non-paper records (INSPIRE lists a thesis).
        var papers = hits.filter(function (h) {
          var types = (h.metadata && h.metadata.document_type) || [];
          return types.indexOf("thesis") === -1;
        });
        var citations = 0;
        var firstAuthorPapers = 0;
        var firstAuthorCitations = 0;
        papers.forEach(function (h) {
          var m = h.metadata || {};
          citations += m.citation_count || 0;
          if (m.first_author && String(m.first_author.recid) === AUTHOR_ID) {
            firstAuthorPapers += 1;
            firstAuthorCitations += m.citation_count || 0;
          }
        });
        setAll("papers", papers.length);
        setAll("citations", citations);
        setAll("first-author-papers", firstAuthorPapers);
        setAll("first-author", firstAuthorCitations);
        roots.forEach(function (r) { r.classList.add("is-loaded"); });
      })
      .catch(function () {
        roots.forEach(function (r) { r.classList.add("is-error"); });
      });
  });
})();
