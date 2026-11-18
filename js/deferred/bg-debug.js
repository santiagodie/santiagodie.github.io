// ?debug=bg only (main.js loads it for that URL, nobody else gets it): a small box in a
// corner of the chat saying what the living background (js/near/chat-field.js) is doing, so the
// owner can check it on a phone. chat-field.js reports through window.__bg(key, value).
(() => {
  const panel = document.querySelector(".chat__panel");
  if (!panel) return;
  const box = document.createElement("pre");
  box.className = "bg-debug";
  box.setAttribute("aria-hidden", "true");
  Object.assign(box.style, { position: "absolute", top: "8px", right: "8px", zIndex: 5, margin: 0, maxWidth: "calc(100% - 16px)", padding: "6px 8px", borderRadius: "6px", background: "rgb(0 0 0 / 0.72)", color: "#F5F0E1", font: "11px/1.35 ui-monospace, monospace", whiteSpace: "pre-wrap", pointerEvents: "none" });
  const net = navigator.connection;
  const state = {
    module: "not loaded yet (it loads when the chat is a screen away)",
    webgl: "-",
    shader: "-",
    state: "-",
    fps: "-",
    "reduced motion": matchMedia("(prefers-reduced-motion: reduce)").matches ? "yes" : "no",
    "data saver": net?.saveData ? "on (does not stop the background)" : "off",
    dpr: `${devicePixelRatio} (drawn at ${Math.min(devicePixelRatio, 1.5)})`,
  };
  const show = () => { box.textContent = Object.entries(state).map(([k, v]) => `${k}: ${v}`).join("\n"); };
  window.__bg = (k, v) => { state[k] = v; show(); };
  Object.assign(state, window.__bgSaid);
  if (!("IntersectionObserver" in window)) state.module = "not loaded: no IntersectionObserver";
  show();
  panel.append(box);
})();
