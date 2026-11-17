// The hero's monogram travels to the header's logo as the page starts to scroll (lot 10,
// R4), tied to the scroll and back on the way up. Loaded after the page by main.js: with
// GSAP's ScrollTrigger when it is there, otherwise (data saver, slow connection, GSAP
// failed) with one update per frame; the path and timing are the same.
//
// Path: from the monogram's place to the header logo, over the first 30 % of the hero's
// height; x eases out and y eases in, so it travels in an arc. The stroke turns from navy
// to gold as it crosses into the (navy) header. At the end the header's own logo (the
// real, focusable link) takes over in place. While it travels it has no
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
  const easeX = (p) => 1 - (1 - p) ** 2; // out
  const easeY = (p) => p * p; // in: with x, an arc
  let g; // geometry, measured at rest

  function measure() {
    const t = mark.style.transform;
    mark.style.transform = "";
    const m = mark.getBoundingClientRect();
    const b = brand.getBoundingClientRect();
    mark.style.transform = t;
    // Where the logo sits once the header is stuck at the top.
    const stuckTop = b.top - header.getBoundingClientRect().top;
    g = { x0: m.left, y0: m.top + scrollY, w: m.width, h: m.height, bx: b.left, by: stuckTop, k: b.width / m.width, range: hero.offsetHeight * 0.3, head: header.offsetHeight };
  }

  // Everything at progress p (0 at the top, 1 at the end of the range).
  function at(p) {
    const s = g.range * p; // the scroll that brings it there
    const k = 1 + (g.k - 1) * easeX(p);
    const y = g.y0 + (g.by - g.y0) * easeY(p); // its top on screen
    // Gold as its middle crosses into the header (40px either side of the edge).
    const gold = Math.min(1, Math.max(0, (g.head + 40 - (y + (g.h * k) / 2)) / 80));
    return {
      tx: (g.bx - g.x0) * easeX(p),
      ty: y - (g.y0 - s), // the monogram scrolls with the page: make up the rest
      k,
      colour: `rgb(${NAVY.map((v, i) => Math.round(v + (GOLD[i] - v) * gold))})`,
      hand: p >= 0.98,
    };
  }

  let drawn = false;
  function apply(p) {
    if (p > 0 && !drawn) {
      drawn = true;
      path.getAnimations().forEach((a) => a.finish()); // still drawing: complete it, then travel
    }
    const v = at(p);
    mark.style.transform = p > 0 ? `translate(${v.tx}px, ${v.ty}px) scale(${v.k})` : "";
    path.style.stroke = p > 0 ? v.colour : "";
    // Hand-off: the header's logo (the link) takes over exactly where the mark lands.
    mark.style.opacity = v.hand ? 0 : "";
    mark.style.viewTransitionName = p > 0 ? "none" : "";
    root.style.setProperty("--brand", v.hand ? 1 : 0);
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
  }

  // GSAP: ScrollTrigger scrubs a 0→1 progress over the same range.
  function gsapEngine() {
    const { gsap, ScrollTrigger } = window;
    gsap.registerPlugin(ScrollTrigger);
    const state = { p: 0 };
    gsap.to(state, {
      p: 1,
      ease: "none",
      onUpdate: () => apply(state.p),
      scrollTrigger: { start: 0, end: () => g.range, scrub: true, invalidateOnRefresh: true, onRefresh: measure },
    });
  }

  root.classList.add("logo-travels");
  measure();
  (window.gsap && window.ScrollTrigger ? gsapEngine : native)();
})();
