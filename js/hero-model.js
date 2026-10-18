// generate(): plays the hero diagram of how a language model turns a prompt into
// an answer. Every word and number is already in the HTML (tools/build.py); this
// script only decides what is visible when, by setting classes and attributes.
// Without it, or with reduced motion, the figure stays a complete static diagram.

(() => {
  "use strict";

  const figure = document.querySelector("[data-llm]");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!figure) return;

  const canvas = figure.querySelector(".llm__canvas");
  const steps = [...figure.querySelectorAll(".llm__step")];
  const controls = figure.querySelector("[data-llm-controls]");
  const toggle = figure.querySelector("[data-llm-pause]");
  const outs = [...figure.querySelectorAll("[data-out]")];
  const dists = [...figure.querySelectorAll("[data-dist]")];
  const detoks = [...figure.querySelectorAll("[data-detok]")];
  const fed = [...figure.querySelectorAll("[data-fed]")];
  const final = figure.querySelector("[data-llm-final]");
  const loopPath = figure.querySelector(".llm__loop path");
  const last = outs.length - 1; // the end token

  // The first token walks through the eight stages slowly; the rest of the answer
  // and the end token then run through the loop one beat each (about 16 s in all).
  const SLOW = [1800, 1600, 1500, 2200, 1900, 1100, 1000, 900];
  const FAST = 330;
  const beats = SLOW.map((duration, index) => ({ stage: index + 1, k: 0, duration }));
  for (let k = 1; k <= last; k += 1) beats.push({ stage: 8, k, duration: FAST, fast: true });

  let index = -1;
  let run = "idle"; // idle | playing | paused | done
  let held = false; // paused by the page (off screen, hidden tab), not by the reader
  let started = false;
  let timer = 0;
  let remaining = 0;
  let beatStart = 0;

  // The loop connector: from the answer back to the slot of the fed-back token. -------

  function drawLoop() {
    const box = canvas.getBoundingClientRect();
    const slot = fed[0];
    const label = figure.querySelector('[data-region="8"]');
    if (!slot || !label || !box.width) return;
    const chip = slot.querySelector(".llm__chip").getBoundingClientRect();
    const pos = slot.querySelector(".llm__pos").getBoundingClientRect();
    const start = label.getBoundingClientRect();
    const x0 = start.right - box.left + 4;
    const y0 = start.top + start.height / 2 - box.top;
    const x1 = Math.max(chip.right, pos.right) - box.left + 6;
    const y1 = chip.top + chip.height / 2 - box.top;
    // Turn up just outside the canvas, inside the panel padding.
    const edge = Math.min(Math.max(x0, x1) + 14, box.width + 10);
    const r = Math.min(10, Math.abs(y0 - y1) / 2);
    loopPath.setAttribute("d",
      `M${x0} ${y0}H${edge - r}Q${edge} ${y0} ${edge} ${y0 - r}V${y1 + r}Q${edge} ${y1} ${edge - r} ${y1}H${x1}`
      + `M${x1 + 5} ${y1 - 4}L${x1} ${y1}L${x1 + 5} ${y1 + 4}`);
  }

  if ("ResizeObserver" in window) new ResizeObserver(drawLoop).observe(canvas);
  else window.addEventListener("resize", drawLoop);
  drawLoop();

  // Rendering one beat -----------------------------------------------------------

  function render({ animate }) {
    const beat = beats[index];
    const reached = beat.stage;
    const k = beat.k;

    figure.dataset.stage = String(reached);
    figure.toggleAttribute("data-fast", Boolean(beat.fast));
    for (let n = 1; n <= 8; n += 1) figure.classList.toggle(`has-${n}`, n <= reached);

    // Restart the stage's entrance animations when playback enters it.
    figure.removeAttribute("data-anim");
    if (animate) {
      void figure.offsetWidth;
      figure.setAttribute("data-anim", "");
    }

    steps.forEach((step, n) => {
      step.classList.toggle("is-current", n + 1 === reached);
      step.classList.toggle("is-done", n + 1 < reached || run === "done");
      const button = step.querySelector("button");
      if (n + 1 === reached) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });

    const visibleOut = reached >= 7 ? k : -1;
    outs.forEach((out, n) => {
      out.classList.toggle("is-on", n <= visibleOut);
      out.classList.toggle("is-last", n === visibleOut);
      out.classList.toggle("is-new", animate && n === visibleOut);
    });
    dists.forEach((dist, n) => dist.classList.toggle("is-current", n === k));
    detoks.forEach((detok, n) => detok.classList.toggle("is-current", n === k));
    // The token fed back into the input is the one generated just before.
    const feedback = reached === 8 ? Math.max(0, k - (beat.fast ? 1 : 0)) : -1;
    fed.forEach((slot, n) => slot.classList.toggle("is-current", n === feedback));
  }

  // While the diagram plays on screen, the progress line keeps still (js/scroll.js).
  function signal() {
    document.dispatchEvent(new CustomEvent("hero:motion", { detail: run === "playing" && !held }));
  }

  function setRun(state) {
    run = state;
    figure.dataset.run = state;
    signal();
    const label = state === "playing" ? toggle.dataset.labelPause : toggle.dataset.labelPlay;
    toggle.setAttribute("aria-label", label);
  }

  // Timeline ---------------------------------------------------------------------

  function schedule(duration) {
    clearTimeout(timer);
    remaining = duration;
    beatStart = performance.now();
    timer = setTimeout(advance, duration);
  }

  function go(target, { animate = run === "playing" } = {}) {
    index = Math.max(0, Math.min(target, beats.length - 1));
    render({ animate });
    if (run === "playing" && !held) schedule(beats[index].duration);
  }

  function advance() {
    if (index >= beats.length - 1) return finish();
    go(index + 1);
  }

  function finish() {
    clearTimeout(timer);
    index = beats.length - 1;
    setRun("done");
    render({ animate: false });
    final.hidden = false; // announced once by the live region around it
  }

  function play() {
    if (run === "done") return replay();
    final.hidden = true;
    setRun("playing");
    if (index < 0) go(0);
    else if (!held) schedule(remaining || beats[index].duration);
  }

  function pause() {
    if (run !== "playing") return;
    clearTimeout(timer);
    remaining = Math.max(0, remaining - (performance.now() - beatStart));
    setRun("paused");
  }

  function replay() {
    final.hidden = true;
    setRun("playing");
    go(0, { animate: true });
  }

  // The page pauses the timeline while the figure is off screen or the tab is hidden.
  function hold(on) {
    if (on === held) return;
    held = on;
    signal();
    if (run !== "playing") return;
    if (on) {
      clearTimeout(timer);
      remaining = Math.max(0, remaining - (performance.now() - beatStart));
      figure.dataset.run = "paused";
    } else {
      figure.dataset.run = "playing";
      schedule(remaining || beats[index].duration);
    }
  }

  // Controls -----------------------------------------------------------------------

  function stageStart(stage) {
    return beats.findIndex((beat) => beat.stage === stage);
  }

  function seek(target) {
    remaining = 0;
    final.hidden = true;
    if (run === "done" || run === "idle") setRun("paused");
    go(target);
  }

  function enableControls() {
    controls.hidden = false;
    // Each stage of the legend becomes a button that jumps to it. The existing
    // number and label move into the button; no text is added.
    steps.forEach((step, n) => {
      const head = step.querySelector("[data-step-head]");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "llm__step-btn";
      button.append(...head.childNodes);
      head.replaceWith(button);
      button.addEventListener("click", () => seek(stageStart(n + 1)));
    });
    toggle.addEventListener("click", () => (run === "playing" ? pause() : play()));
    figure.querySelector("[data-llm-replay]").addEventListener("click", replay);
    figure.querySelector("[data-llm-next]").addEventListener("click", () => {
      const stage = beats[Math.max(index, 0)].stage;
      if (stage >= 8) finish();
      else seek(stageStart(stage + 1));
    });
    figure.querySelector("[data-llm-prev]").addEventListener("click", () => {
      const beat = beats[Math.max(index, 0)];
      const start = stageStart(beat.stage);
      seek(run !== "done" && index > start ? start : stageStart(Math.max(1, beat.stage - 1)));
    });
  }

  // Start ------------------------------------------------------------------------

  function goLive() {
    document.documentElement.classList.add("motion");
    setRun("idle");
    enableControls();

    if ("IntersectionObserver" in window) {
      // Start only once the diagram itself is well in view (60 % of the canvas, or
      // as much of it as the screen can show), so it never plays below the fold.
      new IntersectionObserver(([entry]) => {
        const fits = Math.min(1, (window.innerHeight * 0.9) / entry.boundingClientRect.height);
        if (!started && entry.intersectionRatio >= 0.6 * fits) {
          started = true;
          play();
        }
      }, { threshold: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] }).observe(canvas);
      new IntersectionObserver(([entry]) => hold(!entry.isIntersecting)).observe(figure);
    } else {
      started = true;
      play();
    }
    document.addEventListener("visibilitychange", () => hold(document.hidden));
  }

  // Reduced motion keeps the static diagram. If the setting changes while the page
  // is open, stop and go back to it.
  function goStatic() {
    clearTimeout(timer);
    run = "idle";
    signal();
    document.documentElement.classList.remove("motion");
    figure.removeAttribute("data-run");
    figure.removeAttribute("data-stage");
    figure.removeAttribute("data-fast");
    controls.hidden = true;
  }

  if (!reduce.matches) goLive();
  reduce.addEventListener("change", () => {
    if (reduce.matches) goStatic();
  });
})();
