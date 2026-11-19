// The hero's monogram travels to the header's logo as the page starts to scroll (lot 10,
// R4), tied to the scroll and back on the way up. Loaded after the page by main.js: with
// GSAP's ScrollTrigger when it is there, otherwise (data saver, slow connection, GSAP
// failed) with one update per frame; the path and timing are the same.
//
// Path (fix L10 móvil): it never touches the hero's text. First it rises and shrinks in
// its own column (on phones from the first pixel of scroll: it sits right above the
// name), then, on wide screens, it slides along the header's row to the logo's place.
// The range is the longest (up to 150px on phones, 140 on wide screens) for which no
// sampled frame overlaps a word of the name or the role (on wide screens: in sight, not
// under the navy band, buttons included), 10px kept clear.
// The header's navy slides down from the top in the same progress (.head-band, --head),
// under the monogram, which stays under the header and its menus. The stroke is gold
// over the band and navy over the hero, cut at its edge. At the end the header's own
// logo (the real, focusable link) takes over in place. While it travels it has no
// view-transition-name: changing language mid-way cross-fades it instead of moving it.
(() => {
  const root = document.documentElement;
  const mark = document.querySelector(".hero__logo");
  const path = mark?.querySelector("path");
  const header = document.querySelector("[data-header]");
  const brand = header?.querySelector(".brand");
  const hero = document.querySelector(".hero");
  if (!mark || !brand || !hero || matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const NAVY = [11, 31, 58], GOLD = [201, 162, 39];
  const out = (t) => 1 - (1 - t) ** 2;
  const inOut = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
  const clamp = (t) => Math.min(1, Math.max(0, t));
  const CLEAR = 10; // px kept between the monogram and the text
  const DESK = 140; // the travel's length on wide screens (shortened if the text needs it)
  let g; // geometry, measured at rest

  function measure() {
    const t = mark.style.transform;
    mark.style.transform = "";
    const m = mark.getBoundingClientRect();
    const b = brand.getBoundingClientRect();
    mark.style.transform = t;
    // Where the logo sits once the header is stuck at the top.
    const stuckTop = b.top - header.getBoundingClientRect().top;
    const lateral = Math.abs(b.left - m.left) > 4;
    g = { x0: m.left, y0: m.top + scrollY, w: m.width, h: m.height, bx: b.left, by: stuckTop, k: b.width / m.width, head: header.offsetHeight, split: lateral ? 0.6 : 1 };
    // The hero's text, in page coordinates (on wide screens the buttons' labels too).
    const text = [...hero.querySelectorAll(lateral ? ".hero__w, .hero__role, .hero__actions :is(a, button)" : ".hero__w, .hero__role")].flatMap((el) => {
      const r = document.createRange();
      r.selectNodeContents(el);
      return [...r.getClientRects()].map((q) => ({ l: q.left, t: q.top + scrollY, r: q.right, b: q.bottom + scrollY }));
    });
    // On wide screens only the text still in sight counts: what the navy band has
    // covered (from the header's top down to head × its share) is hidden.
    const head0 = hero.getBoundingClientRect().top + scrollY - g.head; // the header's place at rest
    const clear = (range) => {
      for (let i = 1; i <= 80; i++) {
        const p = i / 80, v = at(p, range);
        const top = v.y, left = g.x0 + v.tx, w = g.w * v.k, h = g.h * v.k, s = range * p;
        const hidden = lateral ? Math.max(0, head0 - s) + g.head * clamp(p / g.split) : -Infinity;
        if (text.some((q) => {
          const qt = Math.max(q.t - s, hidden), qb = q.b - s;
          return qt < qb && left < q.r + CLEAR && left + w > q.l - CLEAR && top < qb + CLEAR && top + h > qt - CLEAR;
        })) return false;
      }
      return true;
    };
    let range = innerWidth < 1024 ? 150 : DESK;
    while (range > 24 && !clear(range)) range -= 2;
    g.range = range;
  }

  // Everything at progress p (0 at the top, 1 at the end of the range).
  function at(p, range = g.range) {
    const s = range * p; // the scroll that brings it there
    const up = out(clamp(p / g.split)); // rise and shrink first...
    const side = g.split < 1 ? inOut(clamp((p - g.split) / (1 - g.split))) : 1; // ...then sideways
    const k = 1 + (g.k - 1) * up;
    const y = g.y0 + (g.by - g.y0) * up; // its top on screen
    // Gold as its middle crosses into the header (40px either side of the edge).
    return {
      y,
      tx: (g.bx - g.x0) * side,
      ty: y - (g.y0 - s), // the monogram scrolls with the page: make up the rest
      k,
      hand: p >= 0.98,
    };
  }

  // The stroke's gradient: gold above the band's edge, navy below.
  const SVG = "http://www.w3.org/2000/svg";
  const grad = document.createElementNS(SVG, "linearGradient");
  // In the viewBox's units, top to bottom of the whole drawing (the stroke included).
  const vb = mark.viewBox.baseVal;
  Object.entries({ id: "logo-edge", gradientUnits: "userSpaceOnUse", x1: 0, y1: vb.y, x2: 0, y2: vb.y + vb.height }).forEach(([k, v]) => grad.setAttribute(k, v));
  const edge = [[0, GOLD], [0, GOLD], [0, NAVY], [1, NAVY]].map(([o, c]) => {
    const st = document.createElementNS(SVG, "stop");
    st.setAttribute("offset", o);
    st.setAttribute("stop-color", `rgb(${c})`);
    return grad.appendChild(st);
  });
  mark.prepend(Object.assign(document.createElementNS(SVG, "defs"), {}));
  mark.firstChild.append(grad);

  let drawn = false;
  // Arrived from the other language mid-way (index.html, "vt-mid"): shown as arrived
  // until the page is back at the top, then as usual.
  let arrived = root.classList.contains("vt-mid");
  function apply(p) {
    if (arrived && scrollY > 0) {
      mark.style.opacity = 0;
      root.style.setProperty("--brand", 1);
      root.style.setProperty("--head", 1);
      root.style.setProperty("--head-top", `${Math.max(0, header.getBoundingClientRect().top)}px`);
      root.style.setProperty("--head-h", `${g.head}px`);
      header.setAttribute("data-scrolled", "");
      return;
    }
    if (arrived) {
      arrived = false;
      root.classList.remove("vt-mid");
    }
    if (p > 0 && !drawn) {
      drawn = true;
      path.getAnimations().forEach((a) => a.finish()); // still drawing: complete it, then travel
    }
    const v = at(p);
    // The band: with p on phones; on wide screens whole by the time the sideways part
    // starts, so the name it covers is out of sight before the monogram crosses above it.
    const head = clamp(p / g.split);
    const top = Math.max(0, header.getBoundingClientRect().top);
    mark.style.transform = p > 0 ? `translate(${v.tx}px, ${v.ty}px) scale(${v.k})` : "";
    // Gold where it is over the sliding navy band, navy where it is still over the hero:
    // a hard-edged gradient cut at the band's lower edge (head × p below the header's top).
    if (p > 0) {
      const band = top + g.head * head;
      const r = mark.getBoundingClientRect();
      const f = clamp((band - r.top) / Math.max(1, r.height)).toFixed(4);
      edge[1].setAttribute("offset", f);
      edge[2].setAttribute("offset", f);
    }
    path.style.stroke = p > 0 ? "url(#logo-edge)" : "";
    // Hand-off: the header's logo (the link) takes over exactly where the mark lands.
    mark.style.opacity = v.hand ? 0 : "";
    mark.style.viewTransitionName = p > 0 ? "none" : "";
    root.style.setProperty("--brand", v.hand ? 1 : 0);
    // One progress for both (fix, phones): the header's navy slides down as the monogram
    // travels and is whole when it lands; its colours switch half-way.
    root.style.setProperty("--head", head.toFixed(3));
    root.style.setProperty("--head-top", `${top}px`);
    root.style.setProperty("--head-h", `${g.head}px`);
    header.toggleAttribute("data-scrolled", head >= 0.5);
  }

  // Native: one update per frame while scrolling.
  function native() {
    let frame = 0;
    const update = () => {
      frame = 0;
      apply(Math.min(1, Math.max(0, scrollY / g.range)));
    };
    addEventListener("scroll", () => { frame ||= requestAnimationFrame(update); }, { passive: true });
    addEventListener("resize", () => { measure(); update(); });
    update();
    return () => { measure(); update(); };
  }

  // GSAP: ScrollTrigger scrubs a 0→1 progress over the same range.
  function gsapEngine() {
    const { gsap, ScrollTrigger } = window;
    gsap.registerPlugin(ScrollTrigger);
    ScrollTrigger.config({ ignoreMobileResize: true }); // iOS: the address bar must not refresh it mid-scroll
    const state = { p: 0 };
    // A refresh sends the progress to 0 with events and back without them (fix 19):
    // the state is applied again from where the page is once it ends.
    gsap.to(state, {
      p: 1,
      ease: "none",
      onUpdate: () => apply(state.p),
      scrollTrigger: { start: 0, end: () => g.range, scrub: true, invalidateOnRefresh: true, onRefreshInit: measure, onRefresh: (st) => apply(st.progress) },
    });
    return () => ScrollTrigger.refresh();
  }

  const bandEl = document.createElement("div");
  bandEl.className = "head-band";
  bandEl.setAttribute("aria-hidden", "true");
  header.before(bandEl);
  measure();
  // Arriving mid-way through the range (fix 19): the header was already navy with its
  // logo (index.html); it stays so until the top, like coming from the other language.
  arrived ||= scrollY > 0 && scrollY < g.range;
  // Taken over in the same frame, from where the page is (fix 19): never from 0.
  root.classList.add("logo-travels");
  apply(clamp(scrollY / g.range));
  const remeasure = (window.gsap && window.ScrollTrigger ? gsapEngine : native)();
  // The text may still be rising into place (its entrance): measure again once it is.
  const moving = hero.getAnimations({ subtree: true }).filter((an) => !mark.contains(an.effect?.target));
  if (moving.length) Promise.allSettled(moving.map((an) => an.finished)).then(remeasure);
})();
