// Scroll: the gold progress line and the sections assembling as they arrive.
// Decorative only. Content is visible in the HTML; the hidden starting state of the
// assembly exists only while this script runs with motion allowed. Nothing here
// holds, snaps or redirects the scroll.

(() => {
  "use strict";

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const root = document.documentElement;
  const svg = document.querySelector("[data-progress]");
  const main = document.getElementById("main");
  const sections = [...document.querySelectorAll(".section")];
  const nodes = sections.map((section) => section.querySelector(".section__node"));
  const navLinks = new Map(
    [...document.querySelectorAll("[data-nav-link]")].map((link) => [link.getAttribute("href").slice(1), link]),
  );
  const READ = 0.6; // the tip sits at 60 % of the viewport height
  const TURN = 24; // radius of the rounded turns, like the monogram's corners
  const TRAILS = [14, 28, 48]; // fading trail behind the tip, in px

  // 1. Section assembly ----------------------------------------------------------

  // Number and node first, then the title, the text, and the cards, entries or the
  // About chat (js/chat.js starts typing only once the chat is in place).
  const ITEMS = ".chat, .feature, .card, .entry, .skills__group, .contact > li";
  const TEXT = ".section__lead, .prose p, .subhead";

  function assemble() {
    if (reduce.matches || !("IntersectionObserver" in window)) return;
    const pending = [];
    sections.forEach((section) => {
      section.querySelectorAll(`.section__num, .section__label, ${TEXT}, ${ITEMS}`).forEach((el) => {
        const kind = el.matches(".section__num") ? "num"
          : el.matches(".section__label") ? "title"
            : el.matches(TEXT) ? "text"
              : el.matches(".feature, .card") ? "card" : "item";
        pending.push([el, kind]);
      });
    });
    const viewH = window.innerHeight;
    const order = { num: 0, title: 1, text: 2, card: 3, item: 3 };
    const observer = new IntersectionObserver((entries) => {
      const arriving = entries.filter((entry) => entry.isIntersecting).map((entry) => entry.target)
        .sort((a, b) => order[a.dataset.reveal] - order[b.dataset.reveal]
          || (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1));
      let items = 0;
      arriving.forEach((el) => {
        const kind = el.dataset.reveal;
        const delay = kind === "num" ? 0 : kind === "title" ? 80 : kind === "text" ? 160 : 240 + 70 * Math.min(items++, 6);
        el.style.setProperty("--reveal-delay", `${delay}ms`);
        el.classList.add("is-in");
        observer.unobserve(el);
      });
    }, { threshold: 0 });

    pending.forEach(([el, kind]) => {
      // Whatever is already on screen stays as it is: no flash, no replay.
      const box = el.getBoundingClientRect();
      if (box.top < viewH && box.bottom > 0) return;
      el.dataset.reveal = kind;
      observer.observe(el);
    });
    root.classList.add("is-assembling");
  }

  // 2. Progress line ----------------------------------------------------------------

  if (!svg || !main || !nodes.every(Boolean)) {
    assemble();
    return;
  }

  const line = svg.querySelector(".progress__line");
  const trails = [...svg.querySelectorAll(".progress__trail")];
  const tip = svg.querySelector(".progress__tip");
  let samples = []; // [length, y] along the path, y never decreasing
  let marks = []; // y of every node, in svg coordinates
  let total = 0;
  let top = 0; // svg top in document coordinates
  let ticking = false;
  let scrollTimeline = false;
  const lit = new Set();
  let quiet = false; // the About chat animation is playing on screen: the line keeps still

  function point(el) {
    const box = el.getBoundingClientRect();
    const host = svg.getBoundingClientRect();
    return { x: box.left + box.width / 2 - host.left, y: box.top + box.height / 2 - host.top };
  }

  // One monoline path through every node; between two nodes on different sides it
  // crosses with two rounded turns in the empty band above the next heading.
  function geometry() {
    svg.style.height = `${main.offsetHeight}px`;
    const host = svg.getBoundingClientRect();
    top = host.top + window.scrollY;
    const points = nodes.map(point);
    const tops = sections.map((section) => section.getBoundingClientRect().top - host.top);
    let d = `M${points[0].x} ${tops[0]}V${points[0].y}`;
    for (let i = 1; i < points.length; i += 1) {
      const a = points[i - 1];
      const b = points[i];
      if (Math.abs(a.x - b.x) < 1) {
        d += `V${b.y}`;
        continue;
      }
      const band = tops[i] + Math.max(TURN * 2, (b.y - tops[i]) * 0.4);
      const dir = b.x > a.x ? 1 : -1;
      d += `V${band - TURN}Q${a.x} ${band} ${a.x + dir * TURN} ${band}`
        + `H${b.x - dir * TURN}Q${b.x} ${band} ${b.x} ${band + TURN}V${b.y}`;
    }
    const last = sections[sections.length - 1].querySelector(".section__title").getBoundingClientRect();
    d += `V${last.bottom - host.top}`;

    line.setAttribute("d", d);
    trails.forEach((trail) => trail.setAttribute("d", d));
    total = line.getTotalLength();
    line.setAttribute("stroke-dasharray", `${total} ${total}`);
    trails.forEach((trail, i) => trail.setAttribute("stroke-dasharray", `${TRAILS[i]} ${total + TRAILS[i]}`));
    svg.style.setProperty("--total", total);
    tip.style.offsetPath = `path("${d}")`;

    samples = [];
    let maxY = -Infinity;
    for (let len = 0; len <= total; len += 6) {
      maxY = Math.max(maxY, line.getPointAtLength(len).y);
      samples.push([len, maxY]);
    }
    samples.push([total, Math.max(maxY, line.getPointAtLength(total).y)]);
    marks = points.map((p) => p.y);

    if (scrollTimeline) timeline();
    update();
  }

  // The drawn length for a tip at height y (binary search, linear between samples).
  function lengthAt(y) {
    if (y <= samples[0][1]) return 0;
    if (y >= samples[samples.length - 1][1]) return total;
    let lo = 0;
    let hi = samples.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (samples[mid][1] < y) lo = mid;
      else hi = mid;
    }
    const [l0, y0] = samples[lo];
    const [l1, y1] = samples[hi];
    return y1 === y0 ? l1 : l0 + ((y - y0) / (y1 - y0)) * (l1 - l0);
  }

  // Where CSS scroll timelines exist, the line itself is drawn by the browser from
  // keyframes that map scroll position to length; this script then only keeps the
  // numbers and the navigation in step.
  function timeline() {
    const range = root.scrollHeight - window.innerHeight;
    if (range <= 0) return;
    const stops = [];
    for (let i = 0; i < samples.length; i += 4) {
      const [len, y] = samples[i];
      const scroll = y + top - window.innerHeight * READ;
      if (scroll <= 0 || scroll >= range) continue;
      stops.push(`${((scroll / range) * 100).toFixed(3)}%{--len:${len.toFixed(1)}}`);
    }
    const start = lengthAt(window.innerHeight * READ - top);
    const end = lengthAt(range + window.innerHeight * READ - top);
    let style = document.getElementById("progress-keyframes");
    if (!style) {
      style = document.createElement("style");
      style.id = "progress-keyframes";
      document.head.append(style);
    }
    style.textContent = `@keyframes progress-draw{0%{--len:${start.toFixed(1)}}${stops.join("")}100%{--len:${end.toFixed(1)}}}`;
  }

  function update() {
    ticking = false;
    const y = window.scrollY + window.innerHeight * READ - top;
    const len = reduce.matches ? total : lengthAt(y);
    if (!quiet) {
      if (!scrollTimeline || reduce.matches) svg.style.setProperty("--len", len);
      svg.toggleAttribute("data-empty", len < 1);
    }

    // Numbers light up when the tip reaches them and stay lit; the navigation's
    // current section is the last number the tip has passed.
    let current = null;
    marks.forEach((mark, i) => {
      if (y >= mark) {
        current = sections[i].id;
        if (!reduce.matches && !quiet && !lit.has(i)) {
          lit.add(i);
          nodes[i].parentElement.classList.add("is-lit");
        }
      }
    });
    navLinks.forEach((link, id) => {
      if (id === current) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  }

  function onScroll() {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }
  }

  scrollTimeline = !reduce.matches && Boolean(window.CSS) && CSS.supports("animation-timeline: scroll()")
    && "registerProperty" in CSS;
  if (scrollTimeline) {
    try {
      CSS.registerProperty({ name: "--len", syntax: "<number>", inherits: true, initialValue: "0" });
      svg.classList.add("is-timeline");
    } catch {
      scrollTimeline = false;
    }
  }
  svg.style.setProperty("--trail-1", TRAILS[0]);
  svg.style.setProperty("--trail-2", TRAILS[1]);
  svg.style.setProperty("--trail-3", TRAILS[2]);
  root.classList.add("has-progress");

  window.addEventListener("scroll", onScroll, { passive: true });
  if ("ResizeObserver" in window) new ResizeObserver(() => requestAnimationFrame(geometry)).observe(main);
  else window.addEventListener("resize", geometry);
  if (document.fonts) document.fonts.ready.then(geometry);
  geometry();
  assemble();

  // The line never competes with the chat animation: while it plays on screen the
  // line holds its length, without trail or glow, and catches up afterwards.
  document.addEventListener("chat:motion", (event) => {
    if (event.detail === quiet) return;
    quiet = event.detail;
    if (quiet) svg.style.setProperty("--len", lengthAt(window.scrollY + window.innerHeight * READ - top));
    svg.toggleAttribute("data-quiet", quiet);
    svg.classList.toggle("is-timeline", scrollTimeline && !quiet && !reduce.matches);
    update();
  });

  reduce.addEventListener("change", () => {
    svg.classList.toggle("is-timeline", scrollTimeline && !quiet && !reduce.matches);
    update();
  });
})();
