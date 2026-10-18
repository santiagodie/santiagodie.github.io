// About chat: press send and watch the question become an answer, token by token.
// The question and the answer are already in the HTML (tools/build.py); this script
// only animates them, with the Web Animations API (transform, opacity and
// stroke-dashoffset). Skip, Escape, scrolling the panel away or the end of the run
// all lead to the same finished chat. Without it, the chat is shown finished.

(() => {
  "use strict";

  const chat = document.querySelector("[data-chat]");
  if (!chat || !chat.animate) return;

  const panel = chat.querySelector(".chat__panel");
  const scene = chat.querySelector(".chat__scene");
  const log = chat.querySelector(".chat__log");
  const bubble = chat.querySelector(".chat__bubble");
  const question = bubble.querySelector("span");
  const answer = chat.querySelector(".chat__answer");
  const outs = [...answer.querySelectorAll(".t")];
  const composer = chat.querySelector(".chat__composer");
  const typed = chat.querySelector(".chat__typed");
  const send = chat.querySelector(".chat__send");
  const ring = chat.querySelector(".chat__ring");
  const skip = chat.querySelector("[data-chat-skip]");
  const replay = chat.querySelector("[data-chat-replay]");
  const live = chat.querySelector("[data-chat-live]");
  const stage = chat.querySelector(".chat__stage");
  const clock = chat.querySelector(".chat__clock");
  const data = JSON.parse(chat.querySelector("[data-chat-model]").textContent);
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  // Curves (emil-design-eng). The camera has mass: it leaves gently and glides a
  // long way into place. Things that arrive use a strong ease-out; things that move
  // across the panel, a strong ease-in-out.
  const CAMERA = "cubic-bezier(0.65, 0, 0.2, 1)";
  const OUT = "cubic-bezier(0.23, 1, 0.32, 1)";
  const MOVE = "cubic-bezier(0.77, 0, 0.175, 1)";
  const DRAWER = "cubic-bezier(0.32, 0.72, 0, 1)";

  // Every animation of a run, so a hidden tab can pause them and Skip can drop them.
  // Waits are animations too (on an invisible clock), so pausing stops the timeline.
  const anims = new Set();
  const ABORT = Symbol("abort");
  let gen = 0;
  let running = false;
  let keyboard = false;

  function play(node, frames, options) {
    const animation = node.animate(frames, { fill: "both", ...options });
    anims.add(animation);
    animation.finished.catch(() => {});
    if (document.hidden) animation.pause();
    return animation;
  }
  const done = (animation) => animation.finished;
  const wait = (ms) => done(play(clock, { opacity: [0, 0] }, { duration: ms }));

  // Geometry relative to the panel, read while the camera is at rest.
  function box(node) {
    const r = node.getBoundingClientRect();
    const p = panel.getBoundingClientRect();
    return { x: r.left - p.left, y: r.top - p.top, w: r.width, h: r.height };
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  // What a chip shows: the token without its leading space.
  const chipText = (t) => (t.trim() ? t.trim() : t).replace(/\n/g, "\\n");
  const ids = (token) => (Array.isArray(token.id) ? token.id.join(" ") : String(token.id));

  // Six illustrative embedding values, stable per token id, nudged by position.
  function vector(id, position) {
    const seed = Array.isArray(id) ? id[0] : id;
    return Array.from({ length: 6 }, (_, j) => {
      const x = Math.sin(seed * 12.9898 + j * 78.233 + position * 0.37) * 43758.5453;
      return 0.12 + 0.78 * (x - Math.floor(x));
    });
  }

  // While the run plays, the scroll progress line keeps still (js/scroll.js).
  const signal = (on) => document.dispatchEvent(new CustomEvent("chat:motion", { detail: on }));

  // A tiny mono label names each stage, in the top-left corner.
  let label = null;
  async function setLabel(text) {
    if (!label) {
      label = el("span", "stage__label");
      stage.append(label);
    } else {
      await done(play(label, { opacity: [1, 0] }, { duration: 140 }));
    }
    label.textContent = text;
    play(label, { opacity: [0, 1], transform: ["translateY(3px)", "none"] }, { duration: 300, easing: OUT });
  }

  // The run ---------------------------------------------------------------------

  async function start(event) {
    if (running) return;
    const id = ++gen;
    const step = async (promise) => {
      await promise;
      if (id !== gen) throw ABORT;
    };
    running = true;
    keyboard = Boolean(event) && event.detail === 0; // Enter or Space on the button
    const lift = getComputedStyle(composer).transform;
    chat.dataset.state = "run";
    skip.hidden = false;
    replay.hidden = true;
    scene.inert = true;
    if (keyboard) skip.focus({ preventScroll: true });
    signal(true);

    try {
      if (reduce.matches) await quiet(step);
      else await full(step, lift);
      finish();
    } catch (error) {
      if (error !== ABORT && error?.name !== "AbortError") {
        finish();
        throw error;
      }
    }
  }

  // Reduced motion: the bubble and the answer fade in; nothing moves or zooms.
  async function quiet(step) {
    play(typed, { opacity: [1, 0] }, { duration: 150 });
    play(composer, { opacity: [0, 1] }, { duration: 200 });
    await step(done(play(bubble, { opacity: [0, 1] }, { duration: 220 })));
    outs.forEach((t) => play(t, { opacity: [1, 1] }, { duration: 1 }));
    await step(done(play(answer, { opacity: [0, 1] }, { duration: 320, delay: 120 })));
  }

  async function full(step, lift) {
    const W = panel.clientWidth;
    const H = panel.clientHeight;
    const narrow = W < 420;
    const targets = outs.map(box);
    const fsBubble = parseFloat(getComputedStyle(bubble).fontSize);
    const stages = data.stages;

    // a. The box settles at the bottom; the message leaves it and rises as a bubble.
    play(composer, { transform: [lift, "none"] }, { duration: 820, easing: DRAWER });
    const from = box(typed);
    const to = box(question);
    play(send, { transform: ["scale(0.92)", "none"] }, { duration: 260, easing: OUT });
    play(typed, { opacity: [1, 0], transform: ["none", "translateY(-6px)"] }, { duration: 180, easing: OUT });
    await step(done(play(bubble, [
      { opacity: 0, transform: `translate(${from.x - to.x}px, ${from.y - to.y}px) scale(0.94)` },
      { opacity: 1, offset: 0.3 },
      { opacity: 1, transform: "none" },
    ], { duration: 700, easing: DRAWER })));
    await step(wait(200));

    // b. The camera pushes into the bubble until its words fill the panel.
    const q = box(question);
    const b = box(bubble);
    const s = Math.max(1.3, Math.min((W * 0.84) / q.w, (narrow ? 30 : 46) / fsBubble));
    const chipTop = Math.round(H * 0.25);
    const fs = fsBubble * s;
    const tx = W / 2 - s * (q.x + q.w / 2);
    const ty = chipTop + (fs * 1.3) / 2 - s * (q.y + q.h / 2);
    const camera = `translate(${tx}px, ${ty}px) scale(${s})`;
    const zoom = play(scene, { transform: ["none", camera] }, { duration: 1350, easing: CAMERA });

    // The same words on the stage, at their zoomed size, fade in as the camera lands.
    stage.replaceChildren();
    label = null;
    const bg = el("span", "stage__bg");
    bg.style.width = `${b.w}px`;
    bg.style.height = `${b.h}px`;
    bg.style.transform = `translate(${tx + s * b.x}px, ${ty + s * b.y}px) scale(${s})`;
    const row = el("div", "stage__row");
    row.style.fontSize = `${fs}px`;
    const toks = data.prompt.map((token, i) => {
      const tok = el("span", "stage__tok");
      const chip = el("span", "stage__chip");
      const edge = el("span", "stage__ring");
      const ink = el("span", "stage__ink", token.t);
      const bone = el("span", "stage__ink stage__ink--bone", token.t);
      chip.append(edge, ink, bone);
      const idEl = el("span", "stage__id", ids(token));
      const vec = el("span", "stage__vec");
      const cells = vector(token.id, i).map((v) => {
        const cell = el("i");
        cell.dataset.v = v.toFixed(2);
        vec.append(cell);
        return cell;
      });
      tok.append(chip, idEl, vec);
      row.append(tok);
      return { chip, edge, ink, bone, idEl, vec, cells, token };
    });
    stage.append(bg, row);
    row.style.left = `${tx + s * q.x}px`;
    row.style.top = `${ty + s * q.y + (q.h * s - fs * 1.3) / 2}px`;
    [bg, row].forEach((node) => play(node, [{ opacity: 0 }, { opacity: 0, offset: 0.84 }, { opacity: 1 }], { duration: 1350 }));
    await step(done(zoom));
    play(scene, { opacity: [1, 0] }, { duration: 240 });
    await step(wait(160));

    // c. Tokens: the words come apart into chips (FLIP), each with its real id.
    setLabel(stages[0]);
    const first = toks.map(({ chip }) => chip.getBoundingClientRect());
    row.classList.add("is-chips");
    toks.forEach(({ ink, bone, token }) => { ink.textContent = bone.textContent = chipText(token.t); });
    let fc = Math.min(fs, narrow ? 17 : 22);
    let idSize = 12;
    const fit = () => {
      row.style.fontSize = `${fc}px`;
      row.style.setProperty("--id-size", `${idSize}px`);
      row.style.setProperty("--cell", `${Math.max(14, Math.min(24, fc * 1.1))}px`);
      return row.getBoundingClientRect().width;
    };
    for (let k = 0; k < 12 && fit() > W * 0.9; k += 1) {
      fc *= 0.94;
      idSize = Math.max(9, idSize * 0.95);
    }
    row.style.left = `${(W - row.getBoundingClientRect().width) / 2}px`;
    row.style.top = `${chipTop}px`;
    const last = toks.map(({ chip }) => chip.getBoundingClientRect());
    toks.forEach(({ chip }, i) => {
      const f = first[i];
      const l = last[i];
      play(chip, {
        transform: [`translate(${f.left - l.left}px, ${f.top - l.top}px) scale(${f.height / l.height})`, "none"],
      }, { duration: 900, easing: MOVE, delay: i * 40 });
    });
    play(bg, { opacity: [1, 0] }, { duration: 450, easing: OUT });
    toks.forEach(({ ink, bone, edge, idEl }, i) => {
      play(ink, { opacity: [1, 0] }, { duration: 360, delay: 140 });
      play(bone, { opacity: [0, 1] }, { duration: 360, delay: 140 });
      play(edge, { opacity: [0, 1] }, { duration: 380, delay: 560 + i * 60, easing: OUT });
      play(idEl, { opacity: [0, 1], transform: ["translateY(-4px)", "none"] }, { duration: 380, delay: 760 + i * 70, easing: OUT });
    });
    await step(wait(760 + toks.length * 70 + 700)); // long enough to read an id or two

    // d. Embeddings: every chip unfolds its vector, cell by cell.
    setLabel(stages[1]);
    toks.forEach(({ cells }, i) => cells.forEach((cell, j) =>
      play(cell, { opacity: [0, Number(cell.dataset.v)], transform: ["scaleX(0.3)", "none"] },
        { duration: 340, delay: i * 65 + j * 45, easing: OUT })));
    await step(wait(toks.length * 65 + 6 * 45 + 550));

    // e. Attention: arcs from the last token to the others, then a pulse down the layers.
    setLabel(stages[2]);
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "stage__arcs");
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const tops = toks.map(({ chip }) => {
      const r = box(chip);
      return { x: r.x + r.w / 2, y: r.y - 3 };
    });
    const query = tops[tops.length - 1];
    const weights = data.attention;
    const peak = Math.max(...weights.slice(0, -1));
    const arcs = tops.slice(0, -1).map((c, i) => {
      const w = weights[i] / peak;
      const reach = 14 + (46 * Math.abs(query.x - c.x)) / W;
      const path = document.createElementNS(svgNS, "path");
      path.setAttribute("d", `M${query.x} ${query.y}C${query.x} ${query.y - reach} ${c.x} ${c.y - reach} ${c.x} ${c.y}`);
      path.setAttribute("pathLength", "1");
      path.style.strokeWidth = (0.8 + 1.6 * w).toFixed(2);
      path.style.opacity = (0.3 + 0.7 * w).toFixed(2);
      svg.append(path);
      return path;
    }).reverse();
    stage.append(svg);
    arcs.forEach((path, i) => play(path, { strokeDashoffset: [1, 0] }, { duration: 680, delay: i * 100, easing: OUT }));

    const firstVec = box(toks[0].vec);
    const lastVec = box(toks[toks.length - 1].vec);
    const stack = el("div", "stage__stack");
    const blocks = Array.from({ length: 4 }, () => {
      const block = el("span", "stage__block");
      const lit = el("span", "stage__lit");
      block.append(lit);
      stack.append(block);
      return { block, lit };
    });
    const pulse = el("span", "stage__pulse");
    stack.append(pulse);
    const sw = Math.min(lastVec.x + lastVec.w - firstVec.x, W * 0.7);
    stack.style.left = `${(W - sw) / 2}px`;
    stack.style.top = `${firstVec.y + firstVec.h + 22}px`;
    stack.style.width = `${sw}px`;
    stage.append(stack);
    const arcsEnd = arcs.length * 100 + 680;
    blocks.forEach(({ block }, i) => play(block, { opacity: [0, 1], transform: ["translateY(-6px)", "none"] },
      { duration: 380, delay: arcsEnd - 200 + i * 70, easing: OUT }));
    await step(wait(arcsEnd + 4 * 70 + 380));
    const sh = stack.getBoundingClientRect().height;
    play(pulse, [
      { opacity: 0, transform: "translateY(-10px)" },
      { opacity: 1, offset: 0.15 },
      { opacity: 1, offset: 0.85 },
      { opacity: 0, transform: `translateY(${sh + 8}px)` },
    ], { duration: 1050, easing: MOVE });
    toks.forEach(({ cells }) => cells.forEach((cell) => {
      const v = Number(cell.dataset.v);
      play(cell, { opacity: [v, v * 0.35] }, { duration: 700, easing: OUT });
    }));
    blocks.forEach(({ lit }, i) => play(lit, { opacity: [0, 1, 0.3] }, { duration: 600, delay: 180 + i * 190, easing: "ease-out" }));
    await step(wait(180 + 4 * 190 + 600));

    // f. Softmax: the candidates for the next token share out the probability; one wins.
    setLabel(stages[3]);
    [svg, stack, ...toks.map((t) => t.vec)].forEach((node) => play(node, { opacity: [1, 0] }, { duration: 300, easing: OUT }));
    const cands = data.next;
    const pmax = Math.max(...cands.map((c) => c.p));
    const dist = el("ol", "stage__dist");
    dist.style.setProperty("--word", `${Math.max(3, ...cands.map((c) => chipText(c.t).length)) + 1}ch`);
    dist.style.setProperty("--bar", narrow ? "6.5rem" : "10rem");
    const rows = cands.map((c) => {
      const li = el("li", "stage__cand");
      const word = el("span", "stage__word", chipText(c.t));
      const glow = el("i", null, chipText(c.t));
      word.append(glow);
      const bar = el("span", "stage__bar");
      const fill = el("i");
      bar.append(fill);
      li.append(word, bar, el("span", "stage__p", `${Math.round(c.p * 100)}%`));
      dist.append(li);
      return { li, glow, bar, fill, c };
    });
    stage.append(dist);
    dist.style.left = `${(W - dist.getBoundingClientRect().width) / 2}px`;
    dist.style.top = `${firstVec.y + 6}px`;
    rows.forEach(({ li, bar, c }, i) => {
      play(li, { opacity: [0, 1], transform: ["translateY(6px)", "none"] }, { duration: 380, delay: 160 + i * 80, easing: OUT });
      play(bar, { transform: ["scaleX(0)", `scaleX(${(c.p / pmax).toFixed(3)})`] }, { duration: 800, delay: 240 + i * 80, easing: OUT });
    });
    await step(wait(240 + rows.length * 80 + 800 + 350)); // the shares settle, then one wins
    const [chosen] = rows; // the first candidate is the chosen token
    rows.forEach((r) => { if (r !== chosen) play(r.li, { opacity: [1, 0.35] }, { duration: 360, easing: OUT }); });
    play(chosen.fill, { opacity: [0, 1] }, { duration: 300, easing: OUT });
    play(chosen.glow, { opacity: [0, 1] }, { duration: 300, easing: OUT });
    play(chosen.li, { transform: ["none", "scale(1.04)", "none"] }, { duration: 460, easing: OUT });
    await step(wait(560));

    // g. The chosen token flies to its place in the answer as the camera pulls out.
    const word = box(chosen.glow);
    const fsAnswer = parseFloat(getComputedStyle(answer).fontSize);
    const fly = el("span", "stage__fly", chipText(outs[0].textContent));
    fly.style.fontSize = `${fsAnswer}px`;
    stage.append(fly);
    const k0 = word.h / fly.getBoundingClientRect().height;
    const t0 = targets[0];
    const pull = play(scene, [
      { transform: camera, opacity: 0 },
      { opacity: 1, offset: 0.35 },
      { transform: "none", opacity: 1 },
    ], { duration: 1400, easing: CAMERA });
    play(chosen.glow, { opacity: [0, 0] }, { duration: 1 });
    [row, dist, label].forEach((node) => play(node, { opacity: [1, 0] }, { duration: 320, easing: OUT }));
    play(fly, { transform: [`translate(${word.x}px, ${word.y}px) scale(${k0})`, `translate(${t0.x}px, ${t0.y}px) scale(1)`] },
      { duration: 1400, easing: CAMERA });
    await step(done(pull));
    play(outs[0], { opacity: [0, 1] }, { duration: 200 });
    play(fly, { opacity: [1, 0] }, { duration: 260, easing: OUT });
    await step(wait(160));

    // The next tokens: a flash of the cycle each, faster and faster, then the stream.
    const ghost = el("span", "chat__ghost");
    const bars = Array.from({ length: 4 }, () => {
      const bar = el("i");
      ghost.append(bar);
      return bar;
    });
    log.append(ghost);
    const flashes = Math.min(8, outs.length - 1);
    const logBox = box(log);
    play(ghost, { opacity: [0, 1] }, { duration: 140 });
    for (let k = 1; k <= flashes; k += 1) {
      const d = Math.round(300 * 0.8 ** (k - 1));
      const r = targets[k];
      ghost.style.transform = `translate(${r.x - logBox.x}px, ${r.y - logBox.y + r.h * 0.18}px)`;
      bars.forEach((bar, j) => {
        const h = j === bars.length - 1 ? 1 : 0.35 + ((k * 7 + j * 3) % 5) / 10;
        play(bar, { transform: ["scaleY(0.2)", `scaleY(${h})`, "scaleY(0.2)"] }, { duration: d, easing: "ease-out" });
      });
      await step(wait(d));
      play(outs[k], { opacity: [0, 1], transform: ["translateY(3px)", "none"] }, { duration: 180, easing: OUT });
    }
    play(ghost, { opacity: [1, 0] }, { duration: 180 });
    const rest = outs.slice(flashes + 1);
    rest.forEach((t, i) => play(t, { opacity: [0, 1] }, { duration: 200, delay: i * 24, easing: OUT }));
    await step(wait(rest.length * 24 + 240));
  }

  // h. The finished chat, however we got here: end of the run, Skip, Escape or
  // the panel leaving the screen.
  function finish() {
    gen += 1;
    running = false;
    const refocus = keyboard || document.activeElement === skip;
    chat.dataset.state = "done";
    anims.forEach((animation) => animation.cancel());
    anims.clear();
    stage.replaceChildren();
    chat.querySelector(".chat__ghost")?.remove();
    scene.inert = false;
    send.disabled = true;
    skip.hidden = true;
    replay.hidden = false;
    live.textContent = answer.textContent.trim();
    if (refocus) replay.focus({ preventScroll: true });
    signal(false);
  }

  function reset() {
    anims.forEach((animation) => animation.cancel());
    anims.clear();
    chat.dataset.state = "idle";
    send.disabled = false;
    live.textContent = "";
  }

  // At rest the box waits mid-panel, like a new conversation.
  const setLift = () => chat.style.setProperty("--lift", `${-Math.round(log.clientHeight / 2 - 8)}px`);
  setLift();
  if ("ResizeObserver" in window) new ResizeObserver(setLift).observe(panel);

  // The section assembles first (js/scroll.js holds back what starts off screen):
  // number, title, then this panel. The question waits until the panel is in place.
  function assembled() {
    if (!chat.dataset.reveal) return Promise.resolve();
    const reveal = chat.getAnimations().find((animation) => animation.animationName === "reveal");
    if (reveal) return reveal.finished.catch(() => {});
    if (chat.classList.contains("is-in")) return Promise.resolve();
    return new Promise((resolve) => {
      chat.addEventListener("animationend", function ended(event) {
        if (event.target !== chat) return;
        chat.removeEventListener("animationend", ended);
        resolve();
      });
    });
  }

  // When the panel comes into view (once): the question types itself, then the
  // send button pulses once.
  let entered = false;
  async function enter() {
    entered = true;
    if (reduce.matches) return;
    await assembled();
    if (running || chat.dataset.state !== "idle") return;
    const text = typed.textContent;
    typed.textContent = "";
    const chars = [...text].map((ch) => {
      const c = el("span", null, ch);
      typed.append(c);
      return c;
    });
    chars.forEach((c, i) => play(c, { opacity: [0, 1] }, { duration: 60, delay: 250 + i * 34 }));
    play(ring, { opacity: [0.7, 0], transform: ["scale(1)", "scale(1.7)"] },
      { duration: 900, delay: 250 + chars.length * 34 + 300, easing: OUT });
  }

  send.addEventListener("click", start);
  skip.addEventListener("click", () => { if (running) finish(); });
  replay.addEventListener("click", (event) => {
    reset();
    start(event);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && running) finish();
  });
  document.addEventListener("visibilitychange", () => {
    anims.forEach((animation) => {
      if (document.hidden) {
        if (animation.playState === "running") animation.pause();
      } else if (animation.playState === "paused") {
        animation.play();
      }
    });
  });
  // Typing starts once a good part of the panel is visible; a run that scrolls
  // fully out of view completes itself instead of playing on unseen.
  new IntersectionObserver(([entry]) => {
    if (!entered && entry.intersectionRatio >= 0.35) enter();
    if (!entry.isIntersecting && running) finish();
  }, { threshold: [0, 0.35] }).observe(panel);

  chat.dataset.state = "idle";
})();
