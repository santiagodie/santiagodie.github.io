// Based on "Prismveil" by Originkit, adapted to vanilla JS.
// The About chat's navy panel as slow, folded silk (lot 10, R1): a WebGL2 fragment
// shader of domain-warped fbm noise, vertical bands and dark troughs. With the owner's
// preset every colour is navy #0B1F3A, so the palette, tint, saturation, grain and
// vignette of the original reduce to navy scaled by the sheen and darkened in the
// troughs; the shader keeps only that (checked pixel for pixel against the original).
// Loaded by main.js when the chat is a screen away. It draws only while the chat is on
// screen and the tab visible; at most 1.5 device pixels per CSS pixel; the pointer
// pushes the folds only with a fine pointer. Reduced motion: one still frame. If the
// shader does not compile, or without WebGL2, a GLSL ES 1.0 version (WebGL1 too); if
// that fails as well, the plain navy panel stays. At most 60 frames a second;
// a lost context is restored. ?debug=bg shows what it is doing (js/deferred/bg-debug.js).
(() => {
  const scene = document.querySelector(".chat__panel"); // the navy panel, not the scene the camera zooms
  if (!scene) return;
  const OCT = 3; // octaves: 3 is not told apart from the original's 5 (≤ 4/255; .audit/l10)
  const FRAG = `#version 300 es
precision highp float;
uniform vec2 uRes, uMouse;
uniform float uTime, uHover;
uniform int uOct;
out vec4 o;
const vec3 NAVY = vec3(11.0, 31.0, 58.0) / 255.0;
float hash2(vec2 c) {
  uvec2 q = uvec2(ivec2(floor(c)) + ivec2(65536)) * uvec2(1597334673u, 3812015801u);
  uint n = (q.x ^ q.y) * 1597334673u;
  n ^= n >> 16u; n *= 2246822519u; n ^= n >> 13u;
  return float(n) * (1.0 / 4294967295.0);
}
float vnoise(vec2 p) {
  vec2 i = floor(p), f = fract(p), w = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash2(i), hash2(i + vec2(1, 0)), w.x), mix(hash2(i + vec2(0, 1)), hash2(i + vec2(1, 1)), w.x), w.y);
}
float fbmN(vec2 p, int oct) {
  float s = 0.0, a = 0.5, n = 0.0;
  for (int i = 0; i < 6; i++) {
    if (i >= oct) break;
    s += a * vnoise(p); n += a;
    p = mat2(1.6, 1.2, -1.2, 1.6) * p + vec2(3.1, 7.7);
    a *= 0.5;
  }
  return s / max(n, 1e-4);
}
void main() {
  float H = max(uRes.y, 1.0);
  vec2 p = (gl_FragCoord.xy - 0.5 * uRes) / H;
  vec2 mp = (uMouse * uRes - 0.5 * uRes) / H;
  float t = uTime;
  vec2 d = p - mp;
  float fall = exp(-dot(d, d) / 0.09);
  p.x -= uHover * 0.5 * d.x * fall;
  float travel = 0.29 * (t + 0.15 * 3.0 / 6.2832 * sin(6.2832 * t / 3.0));
  vec2 q = vec2((p.x - travel) * 3.0, p.y * 3.0 / 3.0) + vec2(7.0 * 17.3, 7.0 * 9.1);
  float tm = t * 0.9;
  vec2 k = vec2(2.0, 0.3);
  vec2 w1 = vec2(fbmN(q + vec2(tm * 0.6, 0.0), uOct), fbmN(q + vec2(5.2, 1.3) + vec2(-tm * 0.45, tm * 0.05), uOct));
  vec2 q1 = q + k * (w1 - 0.5) * 2.0;
  vec2 w2 = vec2(fbmN(q1 + vec2(1.7, 9.2) + vec2(-tm * 0.4, 0.0), uOct), fbmN(q1 + vec2(8.3, 2.8) + vec2(tm * 0.3, -tm * 0.05), uOct));
  vec2 wq = q + k * (w2 - 0.5) * 2.0;
  vec3 col = NAVY * (1.0 + 0.85 * 0.25 * (w2.x - 0.5) * 1.2);
  float g = fbmN(vec2(wq.x * 1.3, wq.y * 2.6) + vec2(13.7, 4.1) + vec2(0.0, tm * 0.1), 3);
  float shade = smoothstep(0.29, 0.47, g);
  col = mix(col, mix(NAVY, col, 0.22), (1.0 - shade) * 0.8);
  col *= 1.0 + 0.12 * uHover * fall;
  o = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

  // ?debug=bg (js/deferred/bg-debug.js draws the box): what it is doing, for a phone.
  const said = (window.__bgSaid = {}); // kept in case the box loads after this module
  const say = (k, v) => { said[k] = v; window.__bg?.(k, v); };
  say("module", "loaded");
  const canvas = document.createElement("canvas");
  canvas.className = "chat__field";
  canvas.setAttribute("aria-hidden", "true");
  let gl, u, raf = 0, seen = false, ok = false;
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
  let clock = 0, last = -1, due = 0, frames = 0, since = 0;
  let mx = 0.5, my = 0.5, hov = 0, tx = 0.5, ty = 0.5, over = 0;

  // The same shader in GLSL ES 1.0 for GPUs where the one above does not compile, and
  // for WebGL1: no unsigned integers, so a float hash on the same lattice (the pattern
  // differs, its look does not); mediump only where highp is missing.
  const es1 = (src) => src
    .replace("#version 300 es\nprecision highp float;", "#ifdef GL_FRAGMENT_PRECISION_HIGH\nprecision highp float;\n#else\nprecision mediump float;\n#endif")
    .replace("out vec4 o;\n", "")
    .replace(/float hash2[^}]*}/, "float hash2(vec2 c) {\n  vec3 p = fract(vec3(floor(c).xyx) * 0.1031);\n  p += dot(p, p.yzx + 33.33);\n  return fract((p.x + p.y) * p.z);\n}")
    .replace("o = vec4", "gl_FragColor = vec4");
  const VERT = (v3) => `${v3 ? "#version 300 es\nin" : "attribute"} vec2 aPos;void main(){gl_Position=vec4(aPos,0.0,1.0);}`;

  // Compile and link: WebGL2 with the original shader, else the GLSL ES 1.0 one (on
  // WebGL2 or WebGL1). Again after a lost context. False, and the plain navy stays.
  function link(v3) {
    const shader = (type, src) => {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh) || "compile");
      return sh;
    };
    const prog = gl.createProgram();
    gl.attachShader(prog, shader(gl.VERTEX_SHADER, VERT(v3)));
    gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, v3 ? FRAG : es1(FRAG)));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog) || "link");
    return prog;
  }
  function init() {
    ok = false;
    const opts = { alpha: false, antialias: false, depth: false };
    gl = canvas.getContext("webgl2", opts);
    const v2 = !!gl;
    gl ||= canvas.getContext("webgl", opts);
    say("webgl", v2 ? "WebGL2" : gl ? "WebGL1 only" : "none");
    if (!gl) return false;
    let prog, err = "";
    for (const v3 of v2 ? [true, false] : [false]) {
      try {
        prog = link(v3);
        say("shader", `ok (${v3 ? "GLSL ES 3.0" : "GLSL ES 1.0"})${err ? `; 3.0 failed: ${err}` : ""}`);
        break;
      } catch (e) {
        err = String(e.message || e).slice(0, 160);
      }
    }
    if (!prog) return say("shader", `error: ${err}`), false;
    gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const pos = gl.getAttribLocation(prog, "aPos");
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);
    u = {};
    for (const n of ["uRes", "uMouse", "uTime", "uHover", "uOct"]) u[n] = gl.getUniformLocation(prog, n);
    gl.uniform1i(u.uOct, OCT);
    return (ok = true);
  }

  const size = () => {
    const dpr = Math.min(devicePixelRatio || 1, 1.5);
    canvas.width = Math.round(scene.clientWidth * dpr);
    canvas.height = Math.round(scene.clientHeight * dpr);
  };
  const draw = (now) => {
    if (!ok) return;
    const dt = last < 0 ? 0 : Math.min((now - last) / 1000, 1 / 20);
    last = now;
    clock = (clock + dt * 0.64) % 3600; // the original's speed, 32 of 50; real time
    const k = 1 - Math.exp(-dt * 6);
    mx += (tx - mx) * k; my += (ty - my) * k; hov += (over - hov) * k;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(u.uRes, canvas.width, canvas.height);
    gl.uniform1f(u.uTime, clock);
    gl.uniform2f(u.uMouse, mx, my);
    gl.uniform1f(u.uHover, hov);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    frames += 1;
    if (now - since >= 1000) {
      say("fps", Math.round((frames * 1000) / (now - since)));
      frames = 0;
      since = now;
    }
  };
  // At most 60 frames a second, whatever the screen's rate (a frame comes 3 ms early
  // at most); the clock follows real time, so the speed is the same.
  const loop = (now) => {
    raf = requestAnimationFrame(loop);
    if (now < due - 3) return;
    due = now - due > 50 ? now + 1000 / 60 : due + 1000 / 60;
    draw(now);
  };
  const run = () => {
    cancelAnimationFrame(raf);
    raf = 0;
    last = -1;
    if (!ok) return;
    if (still) {
      say("state", "reduced motion: one still frame");
      return draw(0);
    }
    if (!seen) say("state", "paused: chat off screen");
    else if (document.hidden) say("state", "paused: tab hidden");
    else {
      say("state", "drawing");
      due = since = performance.now();
      frames = 0;
      raf = requestAnimationFrame(loop);
    }
  };

  if (!init()) return;
  scene.prepend(canvas);
  size();
  canvas.addEventListener("webglcontextlost", (e) => {
    e.preventDefault(); // allows it to be restored
    cancelAnimationFrame(raf);
    raf = 0;
    ok = false;
    say("state", "context lost");
  });
  canvas.addEventListener("webglcontextrestored", () => { if (init()) run(); });
  new ResizeObserver(() => { size(); if (!raf) draw(performance.now()); }).observe(scene);
  new IntersectionObserver(([e]) => { seen = e.isIntersecting; run(); }).observe(scene);
  document.addEventListener("visibilitychange", run);
  if (fine && !still) {
    scene.addEventListener("pointermove", (e) => {
      const r = scene.getBoundingClientRect();
      tx = (e.clientX - r.left) / r.width;
      ty = 1 - (e.clientY - r.top) / r.height;
      over = 1;
    });
    scene.addEventListener("pointerleave", () => { over = 0; });
  }
  scene.classList.add("has-field");
})();
