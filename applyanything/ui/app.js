/* Apply Anything UI. Plain JS, no build step.
   Every piece of data reaches the DOM through text nodes (h() below), never innerHTML:
   titles and org names come from public feeds and are untrusted. */
"use strict";
(() => {
  const TOKEN = document.querySelector('meta[name="aa-token"]').content;
  const DEMO = !!document.querySelector('meta[name="aa-demo"]').content;
  const $ = (sel, el = document) => el.querySelector(sel);
  const view = $("#view");
  let META = { labels: {}, statuses: [] };
  let current = { page: "", params: new URLSearchParams() };

  // ---------------------------------------------------------------- helpers
  const SAFE = /^(https?:|mailto:|#)/i;
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
      else if (k === "href") el.setAttribute("href", SAFE.test(String(v)) ? v : "#");
      else el.setAttribute(k, v === true ? "" : String(v));
    }
    for (const kid of kids.flat(Infinity)) {
      if (kid == null || kid === false) continue;
      el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
    }
    return el;
  }
  const ICONS = {
    plus: '<path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    out: '<path d="M14 4h6v6M20 4l-9 9M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    x: '<path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    layers: '<path d="M4 7l8-4 8 4-8 4zm0 5l8 4 8-4M4 17l8 4 8-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
  };
  function icon(name) {  // constant markup only
    const t = document.createElement("template");
    t.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[name]}</svg>`;
    return t.content.firstChild;
  }

  async function api(path, opts = {}) {
    const init = { method: opts.method || "GET", headers: {} };
    if (opts.body !== undefined) {
      init.body = JSON.stringify(opts.body);
      init.headers["Content-Type"] = "application/json";
    }
    if (init.method !== "GET") init.headers["X-AA-Token"] = TOKEN;
    const res = await fetch(path, init);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }

  function toast(msg, err = false) {
    const t = h("div", { class: "toast" + (err ? " err" : "") }, msg);
    $("#toasts").append(t);
    setTimeout(() => t.remove(), err ? 6500 : 3800);
  }
  const fail = (e) => toast(e.message || String(e), true);

  const now = () => Date.now() / 1000;
  function ago(ts) {
    if (!ts) return "never";
    const s = now() - ts;
    if (s < 90) return "just now";
    if (s < 3600) return `${Math.round(s / 60)} min ago`;
    if (s < 86400) return `${Math.round(s / 3600)}h ago`;
    if (s < 86400 * 45) return `${Math.round(s / 86400)}d ago`;
    return fmtDate(ts);
  }
  function fmtDate(ts) {
    if (!ts) return "";
    const d = new Date(ts * 1000), y = new Date().getFullYear();
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", ...(d.getFullYear() !== y ? { year: "numeric" } : {}) });
  }
  function until(ts) {
    const days = Math.round((ts - now()) / 86400);
    if (days === 0) return "today";
    if (days === 1) return "tomorrow";
    return days > 0 ? `in ${days} days` : `${-days} days ago`;
  }
  const isoDay = (ts) => { const d = new Date(ts * 1000); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  const pct = (a, b) => (b ? Math.round((100 * a) / b) : 0);
  const label = (s) => META.labels[s || ""] || s || "Not started";

  const statusChip = (s) => h("span", { class: `chip st-${s || "new"}` }, h("span", { class: "dot" }), label(s));
  const FILL = { agent: "Agent fills", account: "Account first", check: "Check portal" };
  const fillChip = (f) => f ? h("span", { class: "chip fill " + (f === "agent" ? "fill-agent" : "ghost"), title: f === "agent" ? "No account needed: the agent can fill the whole form" : f === "account" ? "You create an account or sign in, then the agent fills it" : "The organization's own portal: open it once to see the form" }, FILL[f] || f) : "";
  const FLAG = { citizen: "Citizens only", "no-sponsor": "No sponsorship", location: "Outside your countries", closed: "Deadline passed" };
  const flagChips = (flags) => (flags || []).map((f) => h("span", { class: "chip flag" }, FLAG[f] || f));
  const ghost = (t) => (t ? h("span", { class: "chip ghost" }, t) : "");
  function meter(e) {
    if (e == null) return "";
    return h("span", { class: "meter", title: "Effort: higher means more work and longer odds" },
      h("span", { class: "track" }, h("span", { class: "fill", style: `width:${Math.max(2, e)}%` })), String(e));
  }

  // tooltip that works on hover and keyboard focus
  const tip = $("#tooltip");
  function attachTip(el, lines) {
    const show = (x, y) => {
      tip.replaceChildren(h("strong", {}, lines[0]), ...lines.slice(1).map((l) => h("span", {}, l, h("br"))));
      tip.hidden = false;
      const r = tip.getBoundingClientRect();
      tip.style.left = Math.min(window.innerWidth - r.width - 8, x + 14) + "px";
      tip.style.top = Math.max(8, y - r.height - 10) + "px";
    };
    el.addEventListener("pointermove", (e) => show(e.clientX, e.clientY));
    el.addEventListener("pointerleave", () => (tip.hidden = true));
    el.addEventListener("focus", () => { const r = el.getBoundingClientRect(); show(r.left + r.width / 2, r.top); });
    el.addEventListener("blur", () => (tip.hidden = true));
  }

  function card(title, sub, ...body) {
    return h("section", { class: "card" }, h("div", { class: "card-head" }, h("h2", {}, title), sub ? h("div", { class: "sub" }, sub) : ""), ...body);
  }
  function empty(title, text, ...actions) {
    return h("div", { class: "empty" }, h("h3", {}, title), h("p", {}, text), actions.length ? h("div", { class: "actions", style: "justify-content:center" }, actions) : "");
  }
  function itemRow(r, right, meta) {
    const el = h("div", { class: "item", tabindex: "0", role: "button", onclick: () => openDrawer(r.id),
      onkeydown: (e) => e.key === "Enter" && openDrawer(r.id) },
      h("div", { class: "t" }, h("span", { class: "org" }, r.org), h("span", { class: "ink2" }, " · ", r.title)),
      right || statusChip(r.status), meta ? h("div", { class: "m" }, meta) : "");
    return el;
  }
  const addButton = () => h("button", { class: "btn", type: "button", onclick: openAdd }, icon("plus"), "Track opportunity");

  // ---------------------------------------------------------------- charts
  /* Ordinal horizontal bars (funnel stages, tiers): one hue, darker = later step. */
  function hbars(items, { of } = {}) {
    const max = Math.max(1, ...items.map((i) => i.n));
    const chart = h("div", { class: "hbars" }, items.map((it, k) => {
      const bar = h("div", { class: `bar ord-${Math.min(4, k + 1)}`, style: `width:${(100 * it.n) / max}%`, tabindex: "0",
        role: "img", "aria-label": `${it.label}: ${it.n}` });
      attachTip(bar, [`${it.n} ${it.label.toLowerCase()}`, ...(it.tip || [])]);
      return h("div", { class: "hbar" }, h("div", { class: "lab" }, it.label),
        h("div", { class: "lane" }, bar, h("span", { class: "val" }, String(it.n), it.note ? h("small", {}, it.note) : "")));
    }));
    const table = h("table", { class: "tbl plain", hidden: true }, h("thead", {}, h("tr", {}, h("th", {}, of || "Step"), h("th", { class: "num" }, "Count"), h("th", { class: "num" }, "Share"))),
      h("tbody", {}, items.map((it) => h("tr", {}, h("td", {}, it.label), h("td", { class: "num" }, String(it.n)), h("td", { class: "num" }, it.note || "")))));
    return { chart, table };
  }
  function withTable(title, sub, built) {
    const btn = h("button", { class: "btn btn-quiet btn-sm chart-toggle", type: "button", "aria-pressed": "false" }, "Table");
    btn.addEventListener("click", () => {
      const on = btn.getAttribute("aria-pressed") !== "true";
      btn.setAttribute("aria-pressed", String(on));
      btn.textContent = on ? "Chart" : "Table";
      built.chart.hidden = on;
      built.table.hidden = !on;
    });
    return h("section", { class: "card" }, h("div", { class: "card-head" }, h("div", {}, h("h2", {}, title), sub ? h("div", { class: "sub" }, sub) : ""), btn), built.chart, built.table);
  }
  function funnel(f) {
    const base = f[0].n;
    return hbars(f.map((s, k) => ({
      label: s.label, n: s.n, note: k ? `${pct(s.n, base)}%` : "",
      tip: k ? [`${pct(s.n, base)}% of submitted`, `${pct(s.n, f[k - 1].n)}% of ${f[k - 1].label.toLowerCase()}`] : ["applications that went out"],
    })), { of: "Stage" });
  }
  /* Single-series weekly columns with clean ticks and a per-column tooltip. */
  function weeklyColumns(weeks) {
    const max = Math.max(...weeks.map((w) => w.n), 1);
    const step = max <= 5 ? 1 : max <= 10 ? 2 : max <= 25 ? 5 : Math.ceil(max / 50) * 10;
    const top = Math.ceil(max / step) * step;
    const plot = h("div", { class: "cols-plot" });
    for (let v = step; v <= top; v += step) plot.append(h("div", { class: "gl", style: `bottom:${(100 * v) / top}%` }, h("span", {}, String(v))));
    weeks.forEach((w) => {
      const slot = h("div", { class: "slot", tabindex: "0", role: "img", "aria-label": `Week of ${fmtDate(w.week)}: ${w.n}` },
        h("div", { class: "col", style: `height:${(100 * w.n) / top}%` }));
      attachTip(slot, [`${w.n} submitted`, `week of ${fmtDate(w.week)}`]);
      plot.append(slot);
    });
    const x = h("div", { class: "cols-x" }, weeks.map((w, k) => h("span", {}, k % 2 === weeks.length % 2 ? "" : fmtDate(w.week))));
    const chart = h("div", { class: "cols-chart" }, plot, x);
    const table = h("table", { class: "tbl plain", hidden: true }, h("thead", {}, h("tr", {}, h("th", {}, "Week of"), h("th", { class: "num" }, "Submitted"))),
      h("tbody", {}, weeks.map((w) => h("tr", {}, h("td", {}, fmtDate(w.week)), h("td", { class: "num" }, String(w.n))))));
    return { chart, table };
  }

  // ---------------------------------------------------------------- pages
  async function overview() {
    const s = await api("/api/summary");
    updateSync(s.sync);
    const st = s.counts.byStatus, f = s.funnel, sub = f[0].n;
    const fast = s.scoreboard.reduce((a, r) => a + r.fastRejected, 0);
    const pending = st.applied || 0;
    const head = h("div", { class: "head" },
      h("div", {}, h("h1", {}, "Overview"),
        h("p", {}, `${s.counts.total} tracked · ${s.counts.open} open and eligible · ${syncText(s.sync)}`)),
      h("div", { class: "actions" }, addButton()));
    const kpi = (lab, val, note) => h("div", { class: "card kpi" }, h("div", { class: "label" }, lab), h("div", { class: "value" }, String(val)), h("div", { class: "note" }, note));
    const kpis = h("div", { class: "kpis" },
      kpi("Open and eligible", s.counts.open, "not started, no flags"),
      kpi("Submitted", sub, `${pending} waiting to hear back`),
      kpi("Assessments", f[1].n, sub ? `${pct(f[1].n, sub)}% of submitted` : "—"),
      kpi("Interviews", f[2].n, sub ? `${pct(f[2].n, sub)}% of submitted` : "—"),
      kpi("Offers / accepted", f[3].n, sub ? `${pct(f[3].n, sub)}% of submitted` : "—"),
      kpi("Rejected", st.rejected || 0, `${fast} within 3 days (likely knockouts)`));

    let sitting;
    if (s.next) {
      const n = s.next, p = n.progress, saved = n.rows.filter((r) => r.status === "saved").length;
      sitting = card("Current sitting", `Batch ${n.n}${n.round ? ` · round ${n.round}` : ""} · about ${n.mins} min of your time`,
        h("div", { class: "progress", role: "img", "aria-label": `${p.done} of ${p.total} submitted, ${saved} filled` },
          h("span", { class: "p-done", style: `width:${pct(p.done, p.total)}%` }), h("span", { class: "p-saved", style: `width:${pct(saved, p.total)}%` })),
        h("div", { class: "muted", style: "font-size:12.5px;margin:6px 0 8px" }, `${p.done} of ${p.total} submitted · ${saved} filled and waiting on you`),
        h("div", { class: "list" }, n.rows.map((r) => itemRow(r, h("span", { class: "chips" }, fillChip(r.filler), statusChip(r.status))))),
        h("div", { class: "row-end", style: "margin-top:12px;align-items:center" }, h("span", { class: "muted", style: "font-size:12.5px;margin-right:auto" }, "In Claude Code, run /apply to fill this batch."),
          h("a", { class: "btn btn-sm", href: "#/batches" }, "All batches")));
    } else {
      sitting = card("Current sitting", "", empty("No batch yet", "Sync your sources, then build batches.",
        h("button", { class: "btn btn-primary", type: "button", onclick: () => rebuild() }, "Build batches")));
    }
    const needs = [];
    if (s.saved.length) needs.push(h("h3", { class: "muted", style: "margin:2px 0 4px" }, "Filled, waiting for your review"), h("div", { class: "list" }, s.saved.map((r) => itemRow(r))));
    if (s.deadlines.length) needs.push(h("h3", { class: "muted", style: "margin:14px 0 4px" }, "Deadlines in the next 3 weeks"),
      h("div", { class: "list" }, s.deadlines.map((r) => itemRow(r, h("span", { class: "chip ghost" }, until(r.deadline)), `${r.kind} · due ${fmtDate(r.deadline)}`))));
    const recent = s.recent.slice(0, 8);
    view.replaceChildren(head, kpis, h("div", { class: "grid cols" },
      h("div", { class: "stack" }, sitting, withTable("Funnel", "furthest step each submitted application reached", funnel(f))),
      h("div", { class: "stack" },
        card("Needs you", "", needs.length ? needs : h("p", { class: "muted", style: "margin:0" }, "Nothing is waiting on you.")),
        card("Recent activity", "", recent.length ? h("div", { class: "list" }, recent.map((e) => itemRow({ id: e.opp_id, org: e.org, title: e.title, status: e.status }, statusChip(e.status), `${fmtDate(e.at)} · ${e.text}`))) : h("p", { class: "muted", style: "margin:0" }, "No events yet. /refresh records replies from your inbox."),
          h("div", { class: "row-end", style: "margin-top:10px" }, h("a", { class: "btn btn-sm", href: "#/activity" }, "All activity"))))));
  }

  const SORTS = [["effort", "Least effort"], ["-effort", "Most effort"], ["newest", "Newest"], ["deadline", "Deadline"], ["org", "Organization"], ["updated", "Recently updated"]];
  const KINDS = ["internship", "job", "hackathon", "fellowship", "scholarship", "grant", "program", "event", "other"];
  const TIERS = ["reach", "competitive", "solid", "accessible", "ineligible"];
  let oppState = { offset: 0, rows: [], total: 0 };

  async function opportunities(params) {
    const val = (k, d = "") => params.get(k) || d;
    const sel = (name, opts, value, aria) => {
      const s = h("select", { name, "aria-label": aria }, opts.map(([v, t]) => h("option", { value: v }, t)));
      s.value = value;
      s.addEventListener("change", () => setParam(name, s.value));
      return s;
    };
    const search = h("input", { class: "search", type: "search", placeholder: "Search org, title, location, notes", value: val("q"), "aria-label": "Search" });
    let deb;
    search.addEventListener("input", () => { clearTimeout(deb); deb = setTimeout(() => setParam("q", search.value), 220); });
    const box = (name, text) => {
      const c = h("input", { type: "checkbox" });
      c.checked = params.get(name) === (name === "flagged" ? "hide" : "all");
      c.addEventListener("change", () => setParam(name, c.checked ? (name === "flagged" ? "hide" : "all") : ""));
      return h("label", { class: "check" }, c, text);
    };
    const filters = h("div", { class: "filters" }, search,
      sel("status", [["", "Any status"], ["open", "Not started"], ...META.statuses.map((s) => [s, label(s)])], val("status"), "Status"),
      sel("kind", [["", "All kinds"], ...KINDS.map((k) => [k, k[0].toUpperCase() + k.slice(1)])], val("kind"), "Kind"),
      sel("tier", [["", "All tiers"], ...TIERS.map((t) => [t, t[0].toUpperCase() + t.slice(1)])], val("tier"), "Tier"),
      sel("filler", [["", "Anyone fills"], ["agent", "Agent fills"], ["account", "Account first"], ["check", "Check portal"]], val("filler"), "Who fills"),
      sel("sort", SORTS, val("sort", "effort"), "Sort"), box("flagged", "Hide flagged"), box("show", "Include unlisted"));
    const count = h("p", {}, "Loading…");
    const tbody = h("tbody");
    const more = h("div", { class: "more" });
    view.replaceChildren(h("div", { class: "head" }, h("div", {}, h("h1", {}, "Opportunities"), count), h("div", { class: "actions" }, addButton())), filters,
      h("div", { class: "tbl-wrap" }, h("table", { class: "tbl rows" }, h("thead", {}, h("tr", {},
        h("th", {}, "Organization"), h("th", {}, "Title"), h("th", { class: "c-opt" }, "Kind"), h("th", { class: "c-opt" }, "Tier"),
        h("th", { class: "c-opt" }, "Effort"), h("th", { class: "c-opt" }, "Who fills"), h("th", { class: "c-opt" }, "Due / posted"), h("th", {}, "Status"))), tbody)), more);
    oppState = { offset: 0, rows: [], total: 0 };
    const load = async () => {
      const q = new URLSearchParams(params);
      q.set("limit", "100");
      q.set("offset", String(oppState.offset));
      const d = await api("/api/opportunities?" + q);
      oppState.total = d.total;
      oppState.offset += d.rows.length;
      count.textContent = `${d.total} matching`;
      for (const r of d.rows) tbody.append(oppRow(r));
      if (!d.total) tbody.append(h("tr", {}, h("td", { colspan: "8" }, empty("Nothing matches", DEMO ? "Try clearing the filters." : "Clear the filters, run a sync, or track one by URL."))));
      more.replaceChildren(oppState.offset < d.total ? h("button", { class: "btn", type: "button", onclick: () => load().catch(fail) }, `Show more (${d.total - oppState.offset} left)`) : "");
    };
    await load();
  }
  function oppRow(r) {
    const due = r.deadline ? `due ${fmtDate(r.deadline)}` : r.posted_at ? `posted ${fmtDate(r.posted_at)}` : "";
    return h("tr", { tabindex: "0", onclick: () => openDrawer(r.id), onkeydown: (e) => e.key === "Enter" && openDrawer(r.id) },
      h("td", { class: "c-org" }, h("div", { class: "org" }, r.org), h("div", { class: "cell-meta" }, (r.locations || []).slice(0, 2).join(" · "))),
      h("td", { class: "c-title" }, h("div", { class: "cell-title" }, r.title), h("div", { class: "cell-meta" }, [r.platform, ...flagLabels(r.flags)].filter(Boolean).join(" · "))),
      h("td", { class: "c-opt" }, r.kind), h("td", { class: "c-opt" }, r.tier || ""), h("td", { class: "c-opt" }, meter(r.effort)),
      h("td", { class: "c-opt" }, fillChip(r.filler)), h("td", { class: "c-opt muted nowrap" }, due), h("td", { class: "c-status" }, statusChip(r.status)));
  }
  const flagLabels = (flags) => (flags || []).map((f) => FLAG[f] || f);
  function setParam(k, v) {
    const p = new URLSearchParams(current.params);
    v ? p.set(k, v) : p.delete(k);
    location.hash = `#/${current.page}${p.toString() ? "?" + p : ""}`;
  }

  async function batches() {
    const p = await api("/api/batches");
    const mode = p.mode || META.batch?.mode || "prestige";
    const seg = h("div", { class: "seg", role: "group", "aria-label": "Batch order" });
    const modes = [["prestige", "Prestige first"], ["mixed", "Mixed odds"], ["deadline", "Deadline first"]];
    let chosen = mode;
    for (const [m, t] of modes) {
      const b = h("button", { type: "button", "aria-pressed": String(m === mode), title: { prestige: "Reach tier first, then competitive, solid, accessible", mixed: "Each batch mixes tiers (2/3/3/2 by default)", deadline: "Soonest deadline first" }[m] }, t);
      b.addEventListener("click", () => { chosen = m; seg.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b))); });
      seg.append(b);
    }
    const head = h("div", { class: "head" },
      h("div", {}, h("h1", {}, "Batches"), h("p", {}, "One batch is one sitting with the agent. Started batches stay frozen; the rest are re-planned on every sync.")),
      h("div", { class: "actions" }, seg, h("button", { class: "btn btn-primary", type: "button", onclick: () => rebuild(chosen) }, icon("layers"), "Rebuild")));
    if (!p.batches.length) {
      return view.replaceChildren(head, h("div", { class: "card" }, empty("No batches yet", "Sync sources, then rebuild.")));
    }
    view.replaceChildren(head, h("div", { class: "batches" }, p.batches.map((b) => {
      const saved = b.rows.filter((r) => r.status === "saved").length;
      return h("section", { class: "card batch" + (b.current ? " current" : "") },
        h("div", { class: "card-head", style: "margin-bottom:0" }, h("h2", {}, `Batch ${b.n}`),
          h("div", { class: "chips" }, b.round ? h("span", { class: "badge gray" }, `Round ${b.round}`) : "", b.current ? h("span", { class: "badge" }, "Current") : "")),
        h("div", { class: "meta" }, h("span", {}, `${b.ids.length} items`), h("span", {}, `~${b.mins} min`), h("span", {}, `${b.progress.done} submitted`), saved ? h("span", {}, `${saved} filled`) : "", b.progress.skipped ? h("span", {}, `${b.progress.skipped} skipped`) : ""),
        h("div", { class: "progress", role: "img", "aria-label": `${b.progress.done} of ${b.progress.total} submitted` },
          h("span", { class: "p-done", style: `width:${pct(b.progress.done, b.progress.total)}%` }), h("span", { class: "p-saved", style: `width:${pct(saved, b.progress.total)}%` })),
        h("div", { class: "list", style: "margin-top:8px" }, b.rows.map((r) => itemRow(r))));
    })));
  }
  async function rebuild(mode) {
    try {
      const d = await api("/api/actions/batch", { method: "POST", body: { mode } });
      const s = d.summary;
      toast(`${d.batches} batches (${d.mode}): ${s.rebuilt} rebuilt from ${s.open} open, ${s.kept + s.rounds} kept`);
      route();
    } catch (e) { fail(e); }
  }

  async function activity(params) {
    const st = params.get("status") || "";
    const evs = await api("/api/events?limit=1000" + (st ? `&status=${encodeURIComponent(st)}` : ""));
    const s = h("select", { "aria-label": "Status" }, [["", "All events"], ...META.statuses.map((x) => [x, label(x)])].map(([v, t]) => h("option", { value: v }, t)));
    s.value = st;
    s.addEventListener("change", () => setParam("status", s.value));
    const head = h("div", { class: "head" }, h("div", {}, h("h1", {}, "Activity"), h("p", {}, `${evs.length} events: confirmations, assessments, interviews and decisions`)), h("div", { class: "actions" }, s));
    if (!evs.length) return view.replaceChildren(head, h("div", { class: "card" }, empty("No events yet", "Run /refresh in Claude Code to record replies from your inbox, or add events by hand from an opportunity.")));
    const days = new Map();
    for (const e of evs) {
      const k = isoDay(e.at);
      if (!days.has(k)) days.set(k, []);
      days.get(k).push(e);
    }
    view.replaceChildren(head, ...[...days].map(([k, list]) => h("div", { class: "day" },
      h("h3", {}, new Date(list[0].at * 1000).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" })),
      h("div", { class: "card", style: "padding:4px 6px" }, list.map((e) => h("div", { class: "ev item", tabindex: "0", role: "button", onclick: () => openDrawer(e.opp_id), onkeydown: (ev) => ev.key === "Enter" && openDrawer(e.opp_id) },
        statusChip(e.status), h("div", { class: "what" }, h("div", { class: "t" }, e.org, h("span", { class: "ink2", style: "font-weight:400" }, " · ", e.title)),
          h("div", { class: "x" }, e.text, e.source && e.source !== "manual" ? h("span", { class: "muted" }, ` · from ${e.source}`) : ""))))))));
  }

  async function insights() {
    const s = await api("/api/summary");
    const sb = s.scoreboard;
    const rate = (a, b) => (b ? ` (${pct(a, b)}%)` : "");
    const table = sb.length ? h("div", { class: "tbl-wrap", style: "box-shadow:none" }, h("table", { class: "tbl plain" },
      h("thead", {}, h("tr", {}, ["Iteration", "Submitted", "Rejected ≤3 days", "Rejected later", "Assessment", "Interview", "Offer", "Pending"].map((t, k) => h("th", { class: k ? "num" : "" }, t)))),
      h("tbody", {}, sb.map((r) => h("tr", {}, h("td", {}, String(r.iteration)), h("td", { class: "num" }, String(r.submitted)),
        h("td", { class: "num" }, `${r.fastRejected}${rate(r.fastRejected, r.submitted)}`), h("td", { class: "num" }, String(r.laterRejected)),
        h("td", { class: "num" }, `${r.assessment}${r.autoAssessment ? ` (${r.autoAssessment} auto)` : ""}`),
        h("td", { class: "num" }, `${r.interview}${rate(r.interview, r.submitted)}`), h("td", { class: "num" }, String(r.offer)), h("td", { class: "num" }, String(r.pending))))))) :
      empty("No submissions yet", "The scoreboard fills in as applications go out.");
    const tiers = hbars(s.openByTier.map((t) => ({ label: t.tier[0].toUpperCase() + t.tier.slice(1), n: t.n, tip: ["open and eligible"] })), { of: "Tier" });
    view.replaceChildren(
      h("div", { class: "head" }, h("div", {}, h("h1", {}, "Insights"), h("p", {}, "Every round is an experiment: compare iterations before changing anything."))),
      h("div", { class: "grid cols" },
        h("div", { class: "full" }, card("Scoreboard by iteration", "tag apps with --iteration; /retro reads this", table)),
        h("div", { class: "stack" },
          withTable("Submitted per week", "last 12 weeks", weeklyColumns(s.weekly))),
        h("div", { class: "stack" },
          withTable("Funnel", "furthest step reached", funnel(s.funnel)),
          withTable("Open queue by tier", "not started, eligible, no flags", tiers),
          card("Reading the signals", "", h("ul", { class: "signal" },
            h("li", {}, "A rejection within about 3 days almost always comes from an automated knockout question, not a person."),
            h("li", {}, "Assessment invites that arrive within minutes go to everyone; they are counted as auto, not as a screen pass."),
            h("li", {}, "A rejection after two weeks or more usually means a person, or the ranking, passed on it."),
            h("li", {}, "One rejection is noise. Act on a pattern across three or more."))))));
  }

  // ---------------------------------------------------------------- drawer
  const drawer = $("#drawer"), scrim = $("#scrim");
  let drawerId = null, lastFocus = null;
  async function openDrawer(id) {
    try {
      const r = await api(`/api/opportunities/${encodeURIComponent(id)}`);
      if (!drawerId) lastFocus = document.activeElement;
      drawerId = id;
      renderDrawer(r);
      scrim.hidden = false;
      drawer.classList.add("open");
      drawer.setAttribute("aria-hidden", "false");
      drawer.focus();
    } catch (e) { fail(e); }
  }
  function closeDrawer() {
    if (current.params.has("open")) {
      const p = new URLSearchParams(current.params);
      p.delete("open");
      current.params = p;
      history.replaceState(null, "", `#/${current.page}${p.toString() ? "?" + p : ""}`);
    }
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    scrim.hidden = true;
    drawerId = null;
    if (lastFocus) lastFocus.focus();
  }
  scrim.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && drawerId) closeDrawer(); });

  function renderDrawer(r) {
    const after = (row) => { renderDrawer(row); softRefresh(); };
    const status = h("select", { name: "status", "aria-label": "Status" }, [["", "Not started"], ...META.statuses.map((s) => [s, label(s)])].map(([v, t]) => h("option", { value: v }, t)));
    status.value = r.status || "";
    const num = (name, v, lab) => h("label", {}, lab, h("input", { name, type: "number", min: "0", value: v ?? "" }));
    const notes = h("textarea", { name: "notes", placeholder: "Anything worth remembering: what's left, who you talked to, why you skipped it" }, r.notes || "");
    const form = h("form", { class: "form", onsubmit: async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target), n = (k) => (fd.get(k) === "" ? null : Number(fd.get(k)));
      try {
        after(await api(`/api/opportunities/${encodeURIComponent(r.id)}/application`, { method: "PATCH",
          body: { status: fd.get("status"), round: n("round"), iteration: n("iteration"), variant: fd.get("variant") || null, notes: fd.get("notes") } }));
        toast("Saved");
      } catch (err) { fail(err); }
    } },
      h("div", { class: "grid2" }, h("label", {}, "Status", status), h("label", {}, "Resume variant", h("input", { name: "variant", value: r.variant || "", placeholder: "e.g. swe, ml" }))),
      h("div", { class: "grid2" }, num("round", r.round, "Round (sitting)"), num("iteration", r.iteration, "Iteration")),
      h("label", {}, "Notes", notes),
      h("div", { class: "row-end" }, h("button", { class: "btn btn-primary", type: "submit" }, "Save")));

    const answers = Object.entries(r.answers || {});
    const qIn = h("input", { placeholder: "Question, e.g. Graduation date", "aria-label": "Question" });
    const aIn = h("input", { placeholder: "What you answered", "aria-label": "Answer" });
    const patchAnswers = async (obj) => { try { after(await api(`/api/opportunities/${encodeURIComponent(r.id)}/application`, { method: "PATCH", body: { answers: obj } })); } catch (e) { fail(e); } };
    const answerBox = h("div", { class: "answers" },
      answers.length ? answers.map(([q, a]) => h("div", { class: "answer" }, h("span", { class: "q" }, q), h("span", { class: "a" }, a),
        h("button", { class: "btn btn-quiet btn-sm", type: "button", "aria-label": `Remove answer to ${q}`, onclick: () => patchAnswers({ [q]: "" }) }, icon("x")))) :
        h("p", { class: "muted", style: "margin:0;font-size:13px" }, "None recorded. Knockout answers (graduation, work authorization, start date, GPA) are what /retro needs to explain a fast rejection."),
      h("div", { class: "answer" }, qIn, aIn, h("button", { class: "btn btn-sm", type: "button", onclick: () => qIn.value.trim() && patchAnswers({ [qIn.value.trim()]: aIn.value.trim() || "(blank)" }) }, "Add")));

    const evStatus = h("select", { "aria-label": "Event status" }, [["", "Note only"], ...META.statuses.map((s) => [s, label(s)])].map(([v, t]) => h("option", { value: v }, t)));
    const evText = h("input", { placeholder: "What happened, e.g. Recruiter call booked for Tue", "aria-label": "Event text" });
    const evDate = h("input", { type: "date", value: isoDay(now()), "aria-label": "Event date" });
    const timeline = h("ul", { class: "tl" }, (r.events || []).map((e) => h("li", {},
      h("div", { class: "when" }, fmtDate(e.at), e.source && e.source !== "manual" ? ` · ${e.source}` : "",
        h("button", { class: "del", type: "button", title: "Delete event", "aria-label": "Delete event", onclick: async () => {
          try { await api(`/api/events/${e.id}`, { method: "DELETE" }); after(await api(`/api/opportunities/${encodeURIComponent(r.id)}`)); } catch (err) { fail(err); }
        } }, "delete")),
      h("div", { class: "chips", style: "margin-top:3px;align-items:center" }, e.status ? statusChip(e.status) : "", h("span", {}, e.text)),
      e.link ? h("a", { href: e.link, target: "_blank", rel: "noopener noreferrer", style: "font-size:12.5px" }, "Open email") : "")));
    const addEv = h("form", { class: "form", style: "margin-top:8px", onsubmit: async (e) => {
      e.preventDefault();
      try {
        after(await api(`/api/opportunities/${encodeURIComponent(r.id)}/events`, { method: "POST", body: { status: evStatus.value, text: evText.value, date: evDate.value } }));
      } catch (err) { fail(err); }
    } }, h("div", { class: "grid3" }, evDate, evStatus, h("button", { class: "btn", type: "submit" }, "Add event")), evText);

    const facts = [
      ["Locations", (r.locations || []).join(" · ") || "—"],
      ["Deadline", r.deadline ? `${fmtDate(r.deadline)} (${until(r.deadline)})` : "—"],
      ["Posted", r.posted_at ? fmtDate(r.posted_at) : "—"],
      ["Effort", r.effort ?? "—"],
      ["Platform", r.platform || "own portal"],
      ["Source", `${r.source}${r.active ? "" : " (no longer listed)"}`],
      ["Applied", r.applied_at ? fmtDate(r.applied_at) : "—"],
      ["Id", r.id],
    ];
    drawer.replaceChildren(
      h("button", { class: "btn btn-quiet x-btn", type: "button", "aria-label": "Close", onclick: closeDrawer }, icon("x")),
      h("h2", { class: "org-name" }, r.org), h("div", { class: "title" }, r.title),
      h("div", { class: "chips" }, statusChip(r.status), ghost(r.kind), ghost(r.tier), fillChip(r.filler), ...flagChips(r.flags)),
      h("div", { class: "actions", style: "margin-top:14px" }, h("a", { class: "btn btn-primary", href: r.url, target: "_blank", rel: "noopener noreferrer" }, "Open posting", icon("out"))),
      r.note ? h("section", {}, h("h3", {}, "What it needs"), h("div", { class: "callout" }, r.note)) : "",
      h("section", {}, h("dl", { class: "facts" }, facts.flatMap(([k, v]) => [h("dt", {}, k), h("dd", {}, String(v))]))),
      h("section", {}, h("h3", {}, "Your application"), form),
      h("section", {}, h("h3", {}, "Answers given"), answerBox),
      h("section", {}, h("h3", {}, "Timeline"), r.events?.length ? timeline : h("p", { class: "muted", style: "margin:0 0 4px;font-size:13px" }, "No events yet."), addEv));
  }

  // ---------------------------------------------------------------- add dialog
  const dlg = $("#add-dialog"), addForm = $("#add-form");
  function openAdd() { addForm.reset(); dlg.showModal(); }
  $("#add-cancel").addEventListener("click", () => dlg.close());
  addForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(addForm));
    const btn = addForm.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = "Looking it up…";
    try {
      const d = await api("/api/opportunities", { method: "POST", body });
      dlg.close();
      toast(d.added ? `Tracking ${d.row.org}: ${d.row.title}` : "Already tracked");
      softRefresh();
      openDrawer(d.id);
    } catch (err) { fail(err); } finally { btn.disabled = false; btn.textContent = "Add"; }
  });

  // ---------------------------------------------------------------- sync + theme
  function syncText(sync) {
    const ats = Object.values(sync || {}).map((x) => x.at).filter(Boolean);
    return ats.length ? `synced ${ago(Math.max(...ats))}` : "not synced yet";
  }
  function updateSync(sync) {
    const t = syncText(sync);
    $("#sync-state").textContent = t[0].toUpperCase() + t.slice(1);
  }
  const syncBtn = $("#sync-btn"), log = $("#job-log");
  if (DEMO) { syncBtn.disabled = true; syncBtn.title = "Sources are off in demo mode"; }
  syncBtn.addEventListener("click", async () => {
    try {
      await api("/api/actions/sync", { method: "POST", body: {} });
    } catch (e) { if (!/409|running/i.test(e.message)) return fail(e); }
    syncBtn.disabled = true;
    log.hidden = false;
    log.textContent = "Syncing…";
    const poll = async () => {
      const j = await api("/api/job");
      log.textContent = (j.log || []).join("\n") || "Syncing…";
      log.scrollTop = log.scrollHeight;
      if (j.state === "running") return setTimeout(() => poll().catch(fail), 1000);
      syncBtn.disabled = false;
      if (j.state === "error") return fail(new Error("Sync failed: " + j.error));
      toast(`Sync done: ${j.result?.new ?? 0} new`);
      setTimeout(() => (log.hidden = true), 8000);
      route();
    };
    poll().catch(fail);
  });

  const themeBtn = $("#theme-btn");
  const THEMES = ["auto", "light", "dark"];
  function applyTheme(t) {
    if (t === "auto") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = t;
    themeBtn.textContent = `Theme: ${t}`;
  }
  let theme = "auto";
  try { theme = localStorage.getItem("aa-theme") || "auto"; } catch { /* storage may be blocked */ }
  applyTheme(theme);
  themeBtn.addEventListener("click", () => {
    theme = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
    applyTheme(theme);
    try { localStorage.setItem("aa-theme", theme); } catch { /* ignore */ }
  });

  // ---------------------------------------------------------------- router
  const PAGES = { overview, opportunities, batches, activity, insights };
  let refreshTimer;
  function softRefresh() { clearTimeout(refreshTimer); refreshTimer = setTimeout(() => route(true), 150); }
  async function route(soft = false) {
    const [path, query] = (location.hash.slice(2) || "overview").split("?");
    const page = PAGES[path] ? path : "overview";
    current = { page, params: new URLSearchParams(query || "") };
    document.querySelectorAll(".nav a").forEach((a) => a.classList.toggle("on", a.dataset.page === page));
    if (soft && page === "opportunities") return;  // keep the table and scroll position
    try {
      view.style.opacity = soft ? "0.6" : "";
      await PAGES[page](current.params);
    } catch (e) {
      view.replaceChildren(h("div", { class: "card" }, empty("Something went wrong", e.message)));
    } finally { view.style.opacity = ""; }
    if (!soft) $("#main").focus({ preventScroll: true });
    const open = current.params.get("open");
    if (open && open !== drawerId) openDrawer(open);
  }
  window.addEventListener("hashchange", () => route());

  (async () => {
    $("#demo-banner").hidden = !DEMO;
    try { META = await api("/api/meta"); } catch (e) { fail(e); }
    try { updateSync((await api("/api/summary")).sync); } catch { /* shown on the page */ }
    route();
  })();
})();
