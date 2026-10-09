/* Search for LISQM. search.json (built from the data with the site) is loaded on first use; metrics, standards,
   papers, projects, function names and page sections are matched in the browser. No library, no server.
   - the field in the tab bar (wide screens) shows the results in a panel under it;
   - the Search button in the masthead (narrow screens) opens the same search in a dialog;
   - the filter above the tables of the Projects page hides the rows that do not match.
   Keys: "/" starts a search, the arrow keys move through the results, Enter opens one, Escape closes. */
(function () {
  "use strict";
  var script = document.currentScript;
  var root = (script && script.getAttribute("data-root")) || "";
  var data = null;
  var loading = null;
  var ORDER = ["Metric", "Standard", "Project", "Paper", "Page", "Function"];
  var LABEL = {Metric: "Metrics", Project: "Projects", Standard: "Standards", Paper: "Papers and books",
               Function: "Functions", Page: "Pages"};
  var WEIGHT = {Metric: 8, Project: 6, Standard: 5, Paper: 3, Page: 2, Function: 0};

  /* Lower case, without accents and punctuation: "Jiménez-Caminero" and "jimenez caminero" match. C++ and C# keep
     their names. */
  function norm(s) {
    return (s || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase()
      .replace(/c\+\+/g, "cpp").replace(/c#/g, "csharp").replace(/[^a-z0-9]+/g, " ").trim();
  }

  function load() {
    if (!loading) {
      loading = fetch(root + "search.json").then(function (r) { return r.json(); }).then(function (entries) {
        data = entries.map(function (e) {
          e.nt = norm(e.t);
          e.ct = e.nt.replace(/ /g, "");
          e.nx = norm(e.x + " " + e.s);
          e.cx = e.nx.replace(/ /g, "");
          e.starts = {};
          e.ends = {};
          var at = 0;
          e.nt.split(" ").forEach(function (w) { e.starts[at] = true; at += w.length; e.ends[at] = true; });
          return e;
        });
        return data;
      });
    }
    return loading;
  }

  /* The query without spaces in the name without spaces, from the start of a word: 2 if it also ends at the end of a
     word, 1 if not, 0 if it is not there. "iso5321" is in "ISO 532-1:2017" (2) and in "ISO 532:1975" (1). */
  function joined(e, compact) {
    var found = 0;
    for (var i = e.ct.indexOf(compact); i >= 0; i = e.ct.indexOf(compact, i + 1)) {
      if (e.starts[i]) found = Math.max(found, e.ends[i + compact.length] ? 2 : 1);
    }
    return found;
  }

  /* How well an entry matches: [level, score], or null. Every word must match: a word of the name (level 2), the
     start of one (1.5), inside the name (1, words of three letters or more), or in the other names and the
     description (0); the first word of the name scores more. Written without spaces, "iso5321" still finds
     "ISO 532-1:2017". The whole name is level 3. */
  function score(e, q, words, compact) {
    var s = 0, level = 2;
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if ((" " + e.nt).indexOf(" " + w) >= 0) {
        s += 40 + (e.nt.indexOf(w) === 0 ? 15 : 0);
        if ((" " + e.nt + " ").indexOf(" " + w + " ") >= 0) s += 10;
        else level = Math.min(level, 1.5);
      } else if (w.length > 2 && e.nt.indexOf(w) >= 0) { s += 25; level = Math.min(level, 1); }
      else if ((" " + e.nx).indexOf(" " + w) >= 0) { s += 12; level = 0; }
      else if (w.length > 2 && e.nx.indexOf(w) >= 0) { s += 6; level = 0; }
      else { s = -1; break; }
    }
    var j = compact.length > 2 ? joined(e, compact) : 0;
    if (s < 0) {
      if (j) { s = 50 + 15 * j; level = e.ct.indexOf(compact) === 0 ? 2 : 1; }
      else if (compact.length > 2 && e.cx.indexOf(compact) >= 0) { s = 10; level = 0; }
      else return null;
    } else s += 15 * j;
    if (e.nt === q || e.ct === compact) { s += 100; level = 3; }
    return [level, s + WEIGHT[e.k] + (e.bold ? 3 : 0) - (e.old ? 15 : 0)];
  }

  /* The best matches of each kind. Groups come in the order of ORDER, except that a group with better matches
     (by level) comes first; function names always come last. */
  function search(q, perGroup, total) {
    var nq = norm(q), words = nq.split(" ").filter(Boolean);
    if (!words.length || !data) return [];
    var compact = words.join("");
    var groups = {}, level = {};
    data.forEach(function (e) {
      var m = score(e, nq, words, compact);
      if (!m) return;
      (groups[e.k] = groups[e.k] || []).push([m[1], e]);
      var l = e.k === "Function" ? -1 : m[0];
      level[e.k] = Math.max(level[e.k] === undefined ? -1 : level[e.k], l);
    });
    var n = 0;
    return ORDER.filter(function (k) { return groups[k]; })
      .sort(function (a, b) { return level[b] - level[a] || ORDER.indexOf(a) - ORDER.indexOf(b); })
      .map(function (k) {
        var list = groups[k].sort(function (a, b) { return b[0] - a[0]; })
          .slice(0, Math.max(0, Math.min(perGroup, total - n))).map(function (h) { return h[1]; });
        n += list.length;
        return [k, list];
      })
      .filter(function (g) { return g[1].length; });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c];
    });
  }

  function mark(text, q) {
    var out = esc(text);
    norm(q).split(" ").filter(function (w) { return w.length > 1; }).forEach(function (w) {
      var re = new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "i");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  function item(e, q) {
    var badge = e.lang ? '<span class="lb lang-' + esc(e.cls) + '">' + esc(e.lang) + "</span>" : "";
    var tag = e.tag ? ' <span class="mk mk-' + esc(e.tag) + '">' + esc(e.tag) + "</span>" : "";
    var name = mark(e.t, q);
    if (e.k === "Function") name = "<code>" + name + "</code>";
    else if (e.bold) name = "<strong>" + name + "</strong>";
    return '<a class="sr-item" href="' + esc(root + e.u) + '"><span class="sr-title">' + badge + name + tag +
      '</span><span class="sr-sub">' + esc(e.s) + "</span></a>";
  }

  function render(box, q, perGroup, total) {
    if (!q.trim()) { box.hidden = true; box.innerHTML = ""; return; }
    var groups = search(q, perGroup, total);
    if (!groups.length) {
      box.innerHTML = '<p class="sr-none">Nothing found for “' + esc(q) + "”. Try a metric (roughness), a " +
        "standard (ISO 532-1), a language (Rust) or a function name.</p>";
    } else {
      box.innerHTML = groups.map(function (g) {
        return '<div class="sr-group"><p class="sr-head">' + LABEL[g[0]] + "</p>" +
          g[1].map(function (e) { return item(e, q); }).join("") + "</div>";
      }).join("") + '<p class="sr-foot"><kbd>↑</kbd><kbd>↓</kbd> move · <kbd>Enter</kbd> open · ' +
        "<kbd>Esc</kbd> close</p>";
      box.querySelector(".sr-item").classList.add("active");
    }
    box.hidden = false;
  }

  function wire(input, box, perGroup, total, close) {
    input.addEventListener("focus", load);
    input.addEventListener("input", function () {
      load().then(function () { render(box, input.value, perGroup, total); });
    });
    input.addEventListener("keydown", function (ev) {
      var items = Array.prototype.slice.call(box.querySelectorAll(".sr-item"));
      var i = items.findIndex(function (a) { return a.classList.contains("active"); });
      if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
        ev.preventDefault();
        if (!items.length) return;
        if (i >= 0) items[i].classList.remove("active");
        i = ev.key === "ArrowDown" ? Math.min(items.length - 1, i + 1) : Math.max(0, i - 1);
        items[i].classList.add("active");
        items[i].scrollIntoView({block: "nearest"});
      } else if (ev.key === "Enter") {
        ev.preventDefault();
        if (items[i]) location.href = items[i].href;
      } else if (ev.key === "Escape") {
        ev.preventDefault();  /* keeps the words, which a search field would clear */
        close();
      }
    });
  }

  /* The field in the tab bar. */
  var bar = document.querySelector(".site-search");
  if (bar) {
    var barInput = bar.querySelector("input");
    var barBox = bar.querySelector(".search-results");
    var closeBar = function () { barBox.hidden = true; barInput.blur(); };
    wire(barInput, barBox, 4, 14, closeBar);
    bar.addEventListener("submit", function (ev) { ev.preventDefault(); });
    barInput.addEventListener("focus", function () { if (barInput.value.trim()) barBox.hidden = false; });
    document.addEventListener("click", function (ev) { if (!bar.contains(ev.target)) barBox.hidden = true; });
    bar.addEventListener("focusout", function (ev) {
      if (ev.relatedTarget && !bar.contains(ev.relatedTarget)) barBox.hidden = true;  /* left with the Tab key */
    });
  }

  /* The dialog of narrow screens. */
  var open = document.querySelector(".search-open");
  var dialog = document.querySelector(".search-dialog");
  if (open && dialog && dialog.showModal) {
    var dialogInput = dialog.querySelector("input");
    var dialogBox = dialog.querySelector(".search-results");
    wire(dialogInput, dialogBox, 5, 16, function () { dialog.close(); });
    open.addEventListener("click", function () { dialog.showModal(); dialogInput.focus(); load(); });
    dialog.addEventListener("click", function (ev) { if (ev.target === dialog) dialog.close(); });
    dialog.querySelector("form").addEventListener("submit", function (ev) {
      if (ev.submitter && ev.submitter.classList.contains("dialog-close")) return;
      ev.preventDefault();
    });
  }

  /* "/" starts a search from anywhere, except while typing. */
  document.addEventListener("keydown", function (ev) {
    var active = document.activeElement;
    if (ev.key !== "/" || ev.ctrlKey || ev.metaKey || ev.altKey ||
        (active && /^(input|textarea|select)$/i.test(active.tagName))) return;
    if (bar && bar.offsetParent !== null) { ev.preventDefault(); bar.querySelector("input").focus(); }
    else if (open && open.offsetParent !== null) { ev.preventDefault(); open.click(); }
  });

  /* The filter of the Projects page: hides the rows that do not match, and the groups left empty. */
  var filter = document.querySelector(".table-filter input");
  if (filter) {
    var count = document.querySelector(".table-filter .count");
    var rows = Array.prototype.slice.call(document.querySelectorAll("main table.projects tbody tr"));
    var texts = rows.map(function (tr) { return norm(tr.textContent); });
    var groups = Array.prototype.slice.call(document.querySelectorAll("main h2[id]")).map(function (h) {
      var parts = [], el = h.nextElementSibling;
      while (el && el.tagName !== "H2") { parts.push(el); el = el.nextElementSibling; }
      return [h, parts];
    });
    filter.addEventListener("input", function () {
      var words = norm(filter.value).split(" ").filter(Boolean), shown = 0;
      rows.forEach(function (tr, n) {
        var ok = words.every(function (w) { return texts[n].indexOf(w) >= 0; });
        tr.hidden = !ok;
        if (ok) shown++;
      });
      groups.forEach(function (g) {
        var all = 0, visible = 0;
        g[1].forEach(function (p) {
          all += p.querySelectorAll("table.projects tbody tr").length;
          visible += p.querySelectorAll("table.projects tbody tr:not([hidden])").length;
        });
        if (!all) return;
        var empty = words.length > 0 && visible === 0;
        g[0].hidden = empty;
        g[1].forEach(function (p) { p.hidden = empty; });
      });
      count.textContent = words.length ? shown + " of " + rows.length + " projects" : "";
    });
  }
})();
