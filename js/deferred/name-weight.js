// The name's response to a fine pointer (lot 10, R3), loaded after the page by main.js
// (only with a fine pointer and motion allowed).
(() => {
  // The name (lot 10, R3): with a fine pointer, each letter grows lighter as it comes
  // near (Hubot Sans 750 at rest down to 500, the font's own range), easing back after.
  // Each letter keeps its resting width (no shift); centres are measured once (and on
  // resize); the loop only runs while the pointer is within reach or letters settle.
  const nameEl = document.querySelector(".hero__name");
  const letters = [...document.querySelectorAll(".hero__l")];
  if (letters.length) {
    const REST = 750, NEAR = 500, REACH = 220;
    const weight = letters.map(() => REST);
    let centres = [], area, px = -1e5, py = -1e5, raf = 0;
    const measure = () => {
      nameEl.removeAttribute("data-weighted");
      letters.forEach((l) => { l.style.width = ""; });
      const boxes = letters.map((l) => l.getBoundingClientRect());
      letters.forEach((l, i) => { l.style.width = `${boxes[i].width}px`; });
      nameEl.setAttribute("data-weighted", "");
      centres = boxes.map((b) => [b.left + b.width / 2 + scrollX, b.top + b.height / 2 + scrollY]);
      const r = nameEl.getBoundingClientRect();
      area = [r.left + scrollX - REACH, r.top + scrollY - REACH, r.right + scrollX + REACH, r.bottom + scrollY + REACH];
    };
    const frame = () => {
      raf = 0;
      let settling = false;
      letters.forEach((l, i) => {
        const goal = REST - (REST - NEAR) * Math.max(0, 1 - Math.hypot(px - centres[i][0], py - centres[i][1]) / REACH);
        const next = Math.abs(goal - weight[i]) < 1 ? goal : weight[i] + (goal - weight[i]) * 0.2;
        if (Math.round(next) !== Math.round(weight[i])) l.style.fontWeight = Math.round(next);
        weight[i] = next;
        if (next !== goal) settling = true;
      });
      if (settling) raf = requestAnimationFrame(frame);
    };
    const start = () => {
      measure();
      new ResizeObserver(() => requestAnimationFrame(measure)).observe(nameEl);
      addEventListener("pointermove", (e) => {
        px = e.pageX;
        py = e.pageY;
        const near = px > area[0] && px < area[2] && py > area[1] && py < area[3];
        if (!raf && (near || weight.some((w) => w !== REST))) raf = requestAnimationFrame(frame);
      }, { passive: true });
    };
    // After the name has risen into place (and its font is in).
    Promise.all([document.fonts?.ready, ...nameEl.getAnimations().map((a) => a.finished)]).then(start, start);
  }

})();
