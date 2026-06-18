/* =========================================================
   For Ana 🌬️ — interactive magic
   ========================================================= */
(() => {
  "use strict";
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isTouch = window.matchMedia("(pointer: coarse)").matches;

  /* ---------- Veil / loader ---------- */
  window.addEventListener("load", () => {
    setTimeout(() => document.getElementById("veil").classList.add("hidden"), 900);
  });

  /* =========================================================
     1. Background canvas — drifting wind petals & embers
     ========================================================= */
  const bg = document.getElementById("bgCanvas");
  const bgx = bg.getContext("2d");
  let W, H;
  function resize() {
    W = bg.width = fx.width = window.innerWidth;
    H = bg.height = fx.height = window.innerHeight;
  }

  const PETAL_GLYPHS = ["🌸", "🌺", "✨", "🦋", "🍃"];
  const petals = [];
  const PETAL_COUNT = reduceMotion ? 12 : 46;

  function makePetal(y) {
    return {
      x: Math.random() * window.innerWidth,
      y: y ?? Math.random() * window.innerHeight,
      size: 12 + Math.random() * 22,
      speed: 0.3 + Math.random() * 1.1,
      drift: -0.6 + Math.random() * 1.2,
      rot: Math.random() * Math.PI * 2,
      vr: -0.02 + Math.random() * 0.04,
      glyph: PETAL_GLYPHS[(Math.random() * PETAL_GLYPHS.length) | 0],
      sway: Math.random() * Math.PI * 2,
      alpha: 0.5 + Math.random() * 0.5,
    };
  }

  function drawBg() {
    bgx.clearRect(0, 0, W, H);
    for (const p of petals) {
      p.sway += 0.01;
      p.y += p.speed;
      p.x += p.drift + Math.sin(p.sway) * 0.6;
      p.rot += p.vr;
      if (p.y > H + 40) { Object.assign(p, makePetal(-40)); }
      if (p.x > W + 40) p.x = -40;
      if (p.x < -40) p.x = W + 40;
      bgx.save();
      bgx.globalAlpha = p.alpha;
      bgx.translate(p.x, p.y);
      bgx.rotate(p.rot);
      bgx.font = `${p.size}px serif`;
      bgx.textAlign = "center";
      bgx.textBaseline = "middle";
      bgx.fillText(p.glyph, 0, 0);
      bgx.restore();
    }
    requestAnimationFrame(drawBg);
  }

  /* =========================================================
     2. FX canvas — cursor trail + confetti + fireworks
     ========================================================= */
  const fx = document.getElementById("fxCanvas");
  const fxx = fx.getContext("2d");
  const particles = [];   // confetti / sparks
  const trail = [];       // cursor trail dots

  const COLORS = ["#f6c453", "#ff7eb6", "#ffffff", "#ffd98e", "#c77dff", "#7ee8fa"];
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = (arr) => arr[(Math.random() * arr.length) | 0];

  function spawnConfetti(x, y, n = 26, power = 1) {
    for (let i = 0; i < n; i++) {
      const ang = rand(0, Math.PI * 2);
      const spd = rand(2, 9) * power;
      particles.push({
        x, y,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd - rand(1, 4),
        g: 0.12 + Math.random() * 0.1,
        size: rand(5, 12),
        color: pick(COLORS),
        life: 1,
        decay: rand(0.006, 0.018),
        rot: rand(0, Math.PI * 2),
        vr: rand(-0.2, 0.2),
        shape: Math.random() < 0.5 ? "rect" : "circle",
      });
    }
  }

  function firework(x, y) {
    const hueColors = COLORS;
    for (let i = 0; i < 60; i++) {
      const ang = (Math.PI * 2 * i) / 60;
      const spd = rand(3, 8);
      particles.push({
        x, y,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd,
        g: 0.05,
        size: rand(2, 5),
        color: pick(hueColors),
        life: 1,
        decay: rand(0.01, 0.022),
        rot: 0, vr: 0,
        shape: "circle",
        glow: true,
      });
    }
  }

  function drawFx() {
    fxx.clearRect(0, 0, W, H);

    // cursor trail
    for (let i = trail.length - 1; i >= 0; i--) {
      const t = trail[i];
      t.life -= 0.04;
      if (t.life <= 0) { trail.splice(i, 1); continue; }
      fxx.save();
      fxx.globalAlpha = t.life;
      fxx.globalCompositeOperation = "lighter";
      fxx.beginPath();
      fxx.arc(t.x, t.y, t.size * t.life, 0, Math.PI * 2);
      fxx.fillStyle = t.color;
      fxx.shadowBlur = 14;
      fxx.shadowColor = t.color;
      fxx.fill();
      fxx.restore();
    }

    // confetti / sparks
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.vy += p.g;
      p.x += p.vx;
      p.y += p.vy;
      p.rot += p.vr;
      p.life -= p.decay;
      if (p.life <= 0 || p.y > H + 60) { particles.splice(i, 1); continue; }
      fxx.save();
      fxx.globalAlpha = Math.max(0, p.life);
      fxx.translate(p.x, p.y);
      fxx.rotate(p.rot);
      if (p.glow) { fxx.globalCompositeOperation = "lighter"; fxx.shadowBlur = 12; fxx.shadowColor = p.color; }
      fxx.fillStyle = p.color;
      if (p.shape === "rect") {
        fxx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
      } else {
        fxx.beginPath();
        fxx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
        fxx.fill();
      }
      fxx.restore();
    }
    requestAnimationFrame(drawFx);
  }

  /* =========================================================
     3. Custom cursor
     ========================================================= */
  const dot = document.getElementById("cursorDot");
  const ring = document.getElementById("cursorRing");
  let mx = window.innerWidth / 2, my = window.innerHeight / 2;
  let rx = mx, ry = my;

  if (!isTouch) {
    window.addEventListener("mousemove", (e) => {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = `translate(${mx}px, ${my}px) translate(-50%,-50%)`;
      // trail spawn
      if (!reduceMotion && Math.random() < 0.9) {
        trail.push({ x: mx, y: my, size: rand(3, 7), color: pick(COLORS), life: 1 });
        if (trail.length > 60) trail.shift();
      }
    });

    function followCursor() {
      rx += (mx - rx) * 0.18;
      ry += (my - ry) * 0.18;
      ring.style.transform = `translate(${rx}px, ${ry}px) translate(-50%,-50%)`;
      requestAnimationFrame(followCursor);
    }
    followCursor();

    // hover state on interactive elements
    const hotSel = "a, button, .tilt-card, .orb";
    document.querySelectorAll(hotSel).forEach((el) => {
      el.addEventListener("mouseenter", () => ring.classList.add("hot"));
      el.addEventListener("mouseleave", () => ring.classList.remove("hot"));
    });
  }

  /* =========================================================
     4. Click bursts everywhere
     ========================================================= */
  window.addEventListener("click", (e) => {
    if (reduceMotion) return;
    spawnConfetti(e.clientX, e.clientY, 18, 0.9);
  });

  /* =========================================================
     5. Magnetic buttons
     ========================================================= */
  if (!isTouch && !reduceMotion) {
    document.querySelectorAll(".magnetic").forEach((el) => {
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        el.style.transform = `translate(${x * 0.3}px, ${y * 0.4}px) scale(1.06)`;
      });
      el.addEventListener("mouseleave", () => { el.style.transform = ""; });
    });
  }

  /* =========================================================
     6. 3D tilt on cards + hero title
     ========================================================= */
  if (!isTouch && !reduceMotion) {
    document.querySelectorAll(".tilt-card").forEach((card) => {
      card.addEventListener("mousemove", (e) => {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = `rotateY(${px * 16}deg) rotateX(${-py * 16}deg) translateY(-6px)`;
      });
      card.addEventListener("mouseleave", () => { card.style.transform = ""; });
    });

    // hero title parallax follow
    const title = document.getElementById("anaTitle");
    window.addEventListener("mousemove", (e) => {
      const px = (e.clientX / window.innerWidth - 0.5);
      const py = (e.clientY / window.innerHeight - 0.5);
      title.style.transform = `translate(${px * 22}px, ${py * 14}px)`;
    });
  }

  /* =========================================================
     7. Typewriter
     ========================================================= */
  const lines = [
    "You make the algorithm jealous. 💅",
    "Born to be watched, built to be adored.",
    "Khaleesi by name, icon by nature. 🦁",
    "Press the buttons. Cause chaos. ✨",
  ];
  const typedEl = document.getElementById("typed");
  let li = 0, ci = 0, deleting = false;
  function type() {
    if (reduceMotion) { typedEl.textContent = lines[0]; return; }
    const cur = lines[li];
    typedEl.textContent = cur.slice(0, ci);
    if (!deleting && ci < cur.length) { ci++; setTimeout(type, 55); }
    else if (!deleting && ci === cur.length) { deleting = true; setTimeout(type, 1800); }
    else if (deleting && ci > 0) { ci--; setTimeout(type, 26); }
    else { deleting = false; li = (li + 1) % lines.length; setTimeout(type, 350); }
  }

  /* =========================================================
     8. Reveal on scroll
     ========================================================= */
  document.querySelectorAll(".cards, .play, .finale, .card").forEach((el, i) => {
    el.classList.add("reveal");
    el.style.transitionDelay = `${(i % 4) * 0.08}s`;
  });
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  /* =========================================================
     9. Interactions
     ========================================================= */
  // Orb counter
  let crowns = 0;
  const counter = document.getElementById("counter");
  document.getElementById("orb").addEventListener("click", (e) => {
    crowns++;
    counter.textContent = `crowns collected: ${crowns}`;
    spawnConfetti(e.clientX, e.clientY, 30, 1.2);
    if (crowns === 10) burstWord("👑 QUEEN 👑");
    if (crowns === 25) burstWord("UNSTOPPABLE");
    if (crowns % 50 === 0 && crowns > 0) grandFinale();
  });

  // Petal rain button
  document.getElementById("petalBtn").addEventListener("click", () => {
    for (let i = 0; i < 24; i++) petals.push(makePetal(-Math.random() * 200));
  });

  // Surprise button — confetti cannon from corners
  document.getElementById("surpriseBtn").addEventListener("click", () => {
    spawnConfetti(0, H, 50, 1.6);
    spawnConfetti(W, H, 50, 1.6);
    spawnConfetti(W / 2, 0, 40, 1.3);
    burstWord("SURPRISE, ANA! 🎉");
  });

  // Fireworks finale button
  document.getElementById("fireworksBtn").addEventListener("click", grandFinale);

  function grandFinale() {
    if (reduceMotion) return;
    let bursts = 0;
    const timer = setInterval(() => {
      firework(rand(W * 0.15, W * 0.85), rand(H * 0.15, H * 0.55));
      if (++bursts > 12) clearInterval(timer);
    }, 220);
    setTimeout(() => spawnConfetti(W / 2, H * 0.4, 80, 1.8), 400);
  }

  /* Floating word popup */
  function burstWord(text) {
    const el = document.createElement("div");
    el.textContent = text;
    Object.assign(el.style, {
      position: "fixed",
      left: "50%", top: "42%",
      transform: "translate(-50%,-50%) scale(.4)",
      fontFamily: '"Cinzel", serif',
      fontWeight: "900",
      fontSize: "clamp(2rem, 8vw, 5rem)",
      color: "#f6c453",
      textShadow: "0 0 30px rgba(255,126,182,.9)",
      zIndex: 300,
      pointerEvents: "none",
      opacity: "0",
      transition: "transform .5s cubic-bezier(.2,1.4,.4,1), opacity .5s ease",
      whiteSpace: "nowrap",
    });
    document.body.appendChild(el);
    requestAnimationFrame(() => {
      el.style.opacity = "1";
      el.style.transform = "translate(-50%,-50%) scale(1)";
    });
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translate(-50%,-160%) scale(1.1)";
    }, 1300);
    setTimeout(() => el.remove(), 1900);
  }

  // Konami-ish easter egg: type "ana"
  let keys = "";
  window.addEventListener("keydown", (e) => {
    keys = (keys + e.key.toLowerCase()).slice(-3);
    if (keys === "ana") { grandFinale(); burstWord("💖 ANA 💖"); }
  });

  /* =========================================================
     Boot
     ========================================================= */
  resize();
  window.addEventListener("resize", resize);
  for (let i = 0; i < PETAL_COUNT; i++) petals.push(makePetal());
  drawBg();
  drawFx();
  setTimeout(type, 1400);
})();
