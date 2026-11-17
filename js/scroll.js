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
  const ITEMS = ".chat, .card, .portrait, .entry, .skills__group, .langs__item, .certs > li, .contact > li";
  const TEXT = ".section__lead, .prose p, .subhead";

  function assemble() {
    // Arriving from the other language (lot 9), the page is already there: it came
    // with the view transition, so it does not assemble again.
    if (reduce.matches || root.classList.contains("vt-in") || !("IntersectionObserver" in window)) return;
    const pending = [];
    sections.forEach((section) => {
      section.querySelectorAll(`.section__num, .section__label, ${TEXT}, ${ITEMS}`).forEach((el) => {
        const kind = el.matches(".section__num") ? "num"
          : el.matches(".section__label") ? "title"
            : el.matches(TEXT) ? "text"
              : el.matches(".card, .portrait") ? "card" : "item";
        if (!el.closest(".more")) pending.push([el, kind]); // the disclosure opens on its own
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
  let keyframesName = ""; // the scroll keyframes' current name (see timeline())
  const lit = new Set();
  let quiet = false; // the About chat animation is playing on screen: the line keeps still
  let menuOpen = false; // the mobile menu covers the page: nothing here reacts

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
    // The line starts in the hero, at the last featured project's node (the stroke
    // through the featured titles above it is CSS), and runs on down to 01.
    const featured = document.querySelector(".hero__featured-list > li:last-child");
    const start = featured
      ? featured.getBoundingClientRect().top + featured.offsetHeight / 2 - host.top
      : tops[0];
    // The path is written and, alongside, kept as its pieces (straight runs and
    // quarter turns), so its samples come from plain arithmetic: sampling the SVG
    // with getPointAtLength() walked the whole path thousands of times (~130 ms a
    // call, every frame while "More projects" changed height).
    let x = points[0].x;
    let y = start;
    let d = `M${x} ${y}`;
    const pieces = [];
    const run = (nx, ny) => {
      pieces.push([x, y, nx, ny]);
      d += nx === x ? `V${ny}` : `H${nx}`;
      x = nx;
      y = ny;
    };
    const turn = (cx, cy, nx, ny) => {
      pieces.push([x, y, nx, ny, cx, cy]);
      d += `Q${cx} ${cy} ${nx} ${ny}`;
      x = nx;
      y = ny;
    };
    run(x, points[0].y);
    for (let i = 1; i < points.length; i += 1) {
      const a = points[i - 1];
      const b = points[i];
      if (Math.abs(a.x - b.x) < 1) {
        run(x, b.y);
        continue;
      }
      const band = tops[i] + Math.max(TURN * 2, (b.y - tops[i]) * 0.4);
      const dir = b.x > a.x ? 1 : -1;
      run(x, band - TURN);
      turn(a.x, band, a.x + dir * TURN, band);
      run(b.x - dir * TURN, band);
      turn(b.x, band, b.x, band + TURN);
      run(b.x, b.y);
    }
    const last = sections[sections.length - 1].querySelector(".section__title").getBoundingClientRect();
    run(x, last.bottom - host.top);

    line.setAttribute("d", d);
    trails.forEach((trail) => trail.setAttribute("d", d));
    total = line.getTotalLength();
    line.setAttribute("stroke-dasharray", `${total} ${total}`);
    trails.forEach((trail, i) => trail.setAttribute("stroke-dasharray", `${TRAILS[i]} ${total + TRAILS[i]}`));
    svg.style.setProperty("--total", total);
    tip.style.offsetPath = `path("${d}")`;

    // A point every ~6 px of length: straight runs are exact; a quarter turn is a
    // quadratic curve, measured on 8 chords (under 0.1 px off for these radii). The
    // lengths are then scaled to the browser's own total, which draws the dashes.
    samples = [];
    let maxY = -Infinity;
    let length = 0;
    const bezier = (p, t) => (1 - t) * (1 - t) * p[0] + 2 * (1 - t) * t * p[1] + t * t * p[2];
    for (const [x0, y0, x1, y1, cx, cy] of pieces) {
      if (cx === undefined) {
        const size = Math.hypot(x1 - x0, y1 - y0);
        for (let s = 0; s < size; s += 6) {
          maxY = Math.max(maxY, y0 + ((y1 - y0) * s) / size);
          samples.push([length + s, maxY]);
        }
        length += size;
      } else {
        let px = x0;
        let py = y0;
        for (let k = 1; k <= 8; k += 1) {
          const qx = bezier([x0, cx, x1], k / 8);
          const qy = bezier([y0, cy, y1], k / 8);
          length += Math.hypot(qx - px, qy - py);
          maxY = Math.max(maxY, qy);
          samples.push([length, maxY]);
          px = qx;
          py = qy;
        }
      }
    }
    samples.push([length, Math.max(maxY, y)]);
    const scale = length > 0 ? total / length : 1;
    samples.forEach((sample) => { sample[0] *= scale; });
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
    // A running animation keeps the keyframes it started with even when the rule is
    // rewritten (Chrome): after the page grew (a disclosure opened), the tip drew the
    // old lengths, hundreds of px behind. A new name each time makes it start afresh.
    keyframesName = keyframesName === "progress-draw-a" ? "progress-draw-b" : "progress-draw-a";
    style.textContent = `@keyframes ${keyframesName}{0%{--len:${start.toFixed(1)}}${stops.join("")}100%{--len:${end.toFixed(1)}}}`;
    svg.style.animationName = keyframesName;
  }

  function update() {
    ticking = false;
    if (menuOpen) return;
    const y = window.scrollY + window.innerHeight * READ - top;
    const len = reduce.matches ? total : lengthAt(y);
    if (!quiet) {
      if (!svg.classList.contains("is-timeline")) svg.style.setProperty("--len", len);
      // Line, tip and trail stay hidden until the stroke is as long as the trail.
      svg.toggleAttribute("data-empty", len < TRAILS[2]);
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
  // Every change of size in one frame (several observer calls) makes one measurement.
  let measuring = 0;
  let measured = ""; // main's size at the last measurement from here
  let folding = false;
  const remeasure = () => {
    measuring ||= requestAnimationFrame(() => {
      measuring = 0;
      if (folding) return;
      timed();
      // The observer and a "toggle" can both ask for the same change, a frame apart.
      const size = `${main.offsetWidth}x${main.offsetHeight}`;
      if (size === measured) return;
      measured = size;
      geometry();
    });
  };
  if ("ResizeObserver" in window) new ResizeObserver(remeasure).observe(main);
  else window.addEventListener("resize", geometry);
  // Any disclosure, now or later ("toggle" does not bubble: caught on the way down).
  document.addEventListener("toggle", remeasure, true);
  if (document.fonts) document.fonts.ready.then(geometry);
  // The hero's featured projects settle in from 10px lower; measure again once they land.
  const featuredNav = document.querySelector(".hero__featured");
  if (featuredNav) {
    featuredNav.addEventListener("animationend", (event) => {
      if (event.target === featuredNav) requestAnimationFrame(geometry);
    });
  }
  geometry();
  assemble();

  // The line never competes with the chat animation: while it plays on screen the
  // line holds its length, without trail or glow, and catches up afterwards.
  document.addEventListener("chat:motion", (event) => {
    if (event.detail === quiet) return;
    quiet = event.detail;
    if (quiet) svg.style.setProperty("--len", lengthAt(window.scrollY + window.innerHeight * READ - top));
    svg.toggleAttribute("data-quiet", quiet);
    timed();
    update();
  });

  // Lot 8: while a disclosure moves the line keeps its geometry, measuring once at the
  // end; when the fold scrolls the page it is drawn from here, in that same frame.
  const timed = () => svg.classList.toggle("is-timeline", scrollTimeline && !quiet && !folding && !reduce.matches);
  document.addEventListener("disclosure:motion", (event) => {
    folding = event.detail;
    if (!folding) {
      measured = "";
      remeasure();
    }
  });
  document.addEventListener("disclosure:frame", () => {
    svg.classList.remove("is-timeline");
    update();
  });

  // While the mobile menu is open the line, the numbers and the navigation's
  // current section stay as they were; they catch up when it closes.
  document.addEventListener("menu:toggle", (event) => {
    menuOpen = event.detail;
    if (!menuOpen) {
      remeasure(); // only if the page changed size meanwhile
      onScroll();
    }
  });

  reduce.addEventListener("change", () => {
    timed();
    update();
  });
})();
