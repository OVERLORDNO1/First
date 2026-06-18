/* =================================================================
   ANA — Khaleesi of the Wind  ·  main.js
   three.js ember field · roaring lion · GSAP scroll · interactions
   ----------------------------------------------------------------
   EDIT THESE FIRST — your real details live here:
   ================================================================= */
const CONFIG = {
  bookingEmail: "contact@khaleesianahita.com",   // ← Ana's booking inbox
  socials: {
    tiktok: "https://www.tiktok.com/@khaleesianahita",
    instagram: "https://www.instagram.com/khaleesianahita/",
  },
  // Indicative GBP pricing — edit freely
  bundles: [
    { tag:"Entry", name:"The Gust", price:"£75", unit:"per live shout-out", feature:false,
      blurb:"A genuine, in-stream moment for your brand.",
      perks:["Live shout-out on a nightly stream","Product shown on camera","Link / code dropped in chat","Same-week scheduling"] },
    { tag:"Most booked", name:"The Spotlight", price:"£250", unit:"feature package", feature:true,
      blurb:"Content that lives on after the stream ends.",
      perks:["1 dedicated TikTok video","Instagram post + story set","Live shout-out included","Usage rights for 30 days","Draft review before posting"] },
    { tag:"Campaign", name:"The Tempest", price:"£600+", unit:"full campaign", feature:false,
      blurb:"A storm of coverage across every channel.",
      perks:["Live takeover / themed stream","3 pieces of content (TikTok + IG)","Story series across the campaign","Extended usage rights","Priority calendar + reporting"] },
  ],
  // Gallery tiles render as on-brand gold/obsidian posters (no external images).
  // To use Ana's real photos later, add an `img` to any item, e.g.
  //   { cls:"big", cap:"Opening the night", emoji:"🎙️", img:"assets/opening.jpg" }
  // and it will show with the same styling (graceful fallback if it fails).
  gallery: [
    { cls:"big",  cap:"Opening the night", emoji:"🎙️" },
    { cls:"",     cap:"Chat going feral",  emoji:"💬" },
    { cls:"tall", cap:"The roar",          emoji:"🦁" },
    { cls:"",     cap:"Golden hour",       emoji:"💛" },
    { cls:"",     cap:"Coffee & co-hosts", emoji:"☕" },
    { cls:"tall", cap:"Fit check",         emoji:"✨" },
    { cls:"",     cap:"Late-night talks",  emoji:"🌙" },
    { cls:"big",  cap:"The gifts rain in", emoji:"🌬️" },
  ],
};

(() => {
  "use strict";
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isTouch = window.matchMedia("(pointer: coarse)").matches;
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];

  /* ===========================================================
     BUILD DYNAMIC CONTENT (gallery + bundles)
     =========================================================== */
  const galleryGrid = $("#galleryGrid");
  CONFIG.gallery.forEach((g, i) => {
    const t = document.createElement("div");
    t.className = `tile ${g.cls}`.trim();
    const shot = g.img
      ? `<img class="shot" src="${g.img}" alt="${g.cap}" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`
      : "";
    const num = String(i + 1).padStart(2, "0");
    t.innerHTML = `<span class="tile-num">${num}</span><div class="ph">${g.emoji}</div>${shot}<div class="cap">${g.cap}</div>`;
    galleryGrid.appendChild(t);
  });

  const bundleGrid = $("#bundleGrid");
  CONFIG.bundles.forEach(b => {
    const card = document.createElement("article");
    card.className = `bundle${b.feature ? " feature" : ""}`;
    card.innerHTML = `
      <span class="tier-tag">${b.tag}</span>
      <h3>${b.name}</h3>
      <p class="blurb">${b.blurb}</p>
      <div class="price">${b.price}<small>${b.unit}</small></div>
      <ul>${b.perks.map(p => `<li>${p}</li>`).join("")}</ul>
      <button class="btn line pick" data-bundle="${b.name}" data-cursor>Book ${b.name}</button>`;
    bundleGrid.appendChild(card);
  });

  $("#year").textContent = new Date().getFullYear();

  /* ===========================================================
     LION SIGIL — generate the radiant mane
     =========================================================== */
  (function buildMane(){
    const mane = $("#lionMane");
    const cx=100, cy=104, N=30;
    for (let i=0;i<N;i++){
      const a = (i/N)*Math.PI*2 - Math.PI/2;
      const r1 = 38, r2 = i%2 ? 70 : 60;
      const x1 = cx + Math.cos(a)*r1, y1 = cy + Math.sin(a)*r1;
      const x2 = cx + Math.cos(a)*r2, y2 = cy + Math.sin(a)*r2;
      const line = document.createElementNS("http://www.w3.org/2000/svg","line");
      line.setAttribute("x1",x1.toFixed(1)); line.setAttribute("y1",y1.toFixed(1));
      line.setAttribute("x2",x2.toFixed(1)); line.setAttribute("y2",y2.toFixed(1));
      line.setAttribute("stroke-width", i%2 ? "1" : "1.6");
      mane.appendChild(line);
    }
  })();

  /* ===========================================================
     WEBGL EMBER / WIND FIELD (three.js)
     =========================================================== */
  let renderer, scene, camera, embers, raf;
  const pointer = { x:0, y:0, tx:0, ty:0 };

  function initWebGL(){
    if (prefersReduced || typeof THREE === "undefined") return;
    const canvas = $("#webgl");
    renderer = new THREE.WebGLRenderer({ canvas, alpha:true, antialias:true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(innerWidth, innerHeight);
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0a0a0b, 0.055);
    camera = new THREE.PerspectiveCamera(60, innerWidth/innerHeight, 0.1, 100);
    camera.position.z = 24;

    const COUNT = isTouch ? 600 : 1400;
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(COUNT*3);
    const spd = new Float32Array(COUNT);
    const off = new Float32Array(COUNT);
    for (let i=0;i<COUNT;i++){
      pos[i*3]   = (Math.random()-0.5)*60;
      pos[i*3+1] = (Math.random()-0.5)*60;
      pos[i*3+2] = (Math.random()-0.5)*40;
      spd[i] = 0.4 + Math.random()*1.4;
      off[i] = Math.random()*Math.PI*2;
    }
    geo.setAttribute("position", new THREE.BufferAttribute(pos,3));

    // soft round golden sprite
    const c = document.createElement("canvas"); c.width=c.height=64;
    const g = c.getContext("2d");
    const grad = g.createRadialGradient(32,32,0,32,32,32);
    grad.addColorStop(0,"rgba(255,225,150,1)");
    grad.addColorStop(0.3,"rgba(232,184,75,0.7)");
    grad.addColorStop(1,"rgba(232,184,75,0)");
    g.fillStyle=grad; g.fillRect(0,0,64,64);
    const tex = new THREE.CanvasTexture(c);

    const mat = new THREE.PointsMaterial({
      size:0.5, map:tex, transparent:true, depthWrite:false,
      blending:THREE.AdditiveBlending, opacity:0.9,
    });
    embers = new THREE.Points(geo, mat);
    embers.userData = { spd, off, pos };
    scene.add(embers);

    addEventListener("resize", onResize);
    if (!isTouch) addEventListener("mousemove", e=>{
      pointer.tx = (e.clientX/innerWidth - 0.5);
      pointer.ty = (e.clientY/innerHeight - 0.5);
    });
    loop(0);
  }

  function onResize(){
    if(!renderer) return;
    renderer.setSize(innerWidth, innerHeight);
    camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  }

  function loop(t){
    raf = requestAnimationFrame(loop);
    const time = t*0.001;
    const { spd, off, pos } = embers.userData;
    const arr = embers.geometry.attributes.position.array;
    for (let i=0;i<spd.length;i++){
      arr[i*3+1] += spd[i]*0.02;                       // rise like embers
      arr[i*3]   += Math.sin(time*0.5 + off[i])*0.01;  // wind sway
      if (arr[i*3+1] > 30){ arr[i*3+1] = -30; arr[i*3] = (Math.random()-0.5)*60; }
    }
    embers.geometry.attributes.position.needsUpdate = true;
    embers.rotation.y = time*0.02;
    // parallax
    pointer.x += (pointer.tx - pointer.x)*0.04;
    pointer.y += (pointer.ty - pointer.y)*0.04;
    camera.position.x = pointer.x*6;
    camera.position.y = -pointer.y*4;
    camera.lookAt(0,0,0);
    renderer.render(scene, camera);
  }

  /* ===========================================================
     2D FX — roar shockwave + ember burst
     =========================================================== */
  const fx = $("#fx"); const fxc = fx.getContext("2d");
  let sparks = []; let rings = [];
  function sizeFx(){ fx.width=innerWidth; fx.height=innerHeight; }
  sizeFx(); addEventListener("resize", sizeFx);

  function roar(){
    const r = $("#lion").getBoundingClientRect();
    const x = r.left + r.width/2, y = r.top + r.height/2;
    rings.push({ x, y, rad:10, life:1 });
    const n = prefersReduced ? 0 : 90;
    for (let i=0;i<n;i++){
      const a = Math.random()*Math.PI*2, s = 2+Math.random()*10;
      sparks.push({ x, y, vx:Math.cos(a)*s, vy:Math.sin(a)*s - 2,
        g:0.12, size:1+Math.random()*3, life:1, decay:0.008+Math.random()*0.02 });
    }
    if (window.gsap){
      gsap.fromTo("#lion",{scale:0.9},{scale:1,duration:1.1,ease:"elastic.out(1,0.35)"});
      gsap.fromTo("main",{x:0},{x:0,duration:0.5,
        onStart(){ document.body.animate(
          [{transform:"translate(0,0)"},{transform:"translate(-6px,3px)"},{transform:"translate(5px,-4px)"},{transform:"translate(0,0)"}],
          {duration:380,easing:"ease-out"}); }});
    }
    playRoarSound();
  }

  function drawFx(){
    requestAnimationFrame(drawFx);
    fxc.clearRect(0,0,fx.width,fx.height);
    // rings
    for (let i=rings.length-1;i>=0;i--){
      const r=rings[i]; r.rad+=14; r.life-=0.025;
      if(r.life<=0){rings.splice(i,1);continue;}
      fxc.beginPath(); fxc.arc(r.x,r.y,r.rad,0,Math.PI*2);
      fxc.strokeStyle=`rgba(232,184,75,${r.life*0.6})`; fxc.lineWidth=2*r.life; fxc.stroke();
    }
    // sparks
    fxc.globalCompositeOperation="lighter";
    for (let i=sparks.length-1;i>=0;i--){
      const p=sparks[i]; p.vy+=p.g; p.x+=p.vx; p.y+=p.vy; p.life-=p.decay;
      if(p.life<=0){sparks.splice(i,1);continue;}
      fxc.beginPath(); fxc.arc(p.x,p.y,p.size,0,Math.PI*2);
      fxc.fillStyle=`rgba(${255},${200+Math.random()*40|0},${120},${p.life})`;
      fxc.shadowBlur=10; fxc.shadowColor="rgba(232,184,75,.8)"; fxc.fill();
    }
    fxc.globalCompositeOperation="source-over"; fxc.shadowBlur=0;
  }
  drawFx();

  // low rumble via WebAudio (only on user gesture)
  let actx;
  function playRoarSound(){
    if (prefersReduced) return;
    try{
      actx = actx || new (window.AudioContext||window.webkitAudioContext)();
      const t = actx.currentTime;
      const osc = actx.createOscillator(), gain = actx.createGain();
      osc.type="sawtooth"; osc.frequency.setValueAtTime(90,t);
      osc.frequency.exponentialRampToValueAtTime(38,t+0.5);
      const filt = actx.createBiquadFilter(); filt.type="lowpass"; filt.frequency.value=420;
      gain.gain.setValueAtTime(0.0001,t);
      gain.gain.exponentialRampToValueAtTime(0.32,t+0.05);
      gain.gain.exponentialRampToValueAtTime(0.0001,t+0.85);
      osc.connect(filt); filt.connect(gain); gain.connect(actx.destination);
      osc.start(t); osc.stop(t+0.9);
    }catch(e){/* audio not available */}
  }

  const lion = $("#lion");
  lion.addEventListener("click", roar);
  lion.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();roar();} });

  /* ===========================================================
     CUSTOM CURSOR
     =========================================================== */
  if (!isTouch && !prefersReduced){
    const cur = $("#cursor");
    let cx=innerWidth/2, cy=innerHeight/2, x=cx, y=cy;
    addEventListener("mousemove", e=>{ cx=e.clientX; cy=e.clientY; });
    (function tick(){ x+=(cx-x)*0.2; y+=(cy-y)*0.2;
      cur.style.transform=`translate(${x}px,${y}px) translate(-50%,-50%)`; requestAnimationFrame(tick); })();
    const grow = ()=>cur.classList.add("grow"), shrink=()=>cur.classList.remove("grow");
    document.addEventListener("mouseover", e=>{ if(e.target.closest("[data-cursor],a,button,.lion,.tile")) grow(); });
    document.addEventListener("mouseout", e=>{ if(e.target.closest("[data-cursor],a,button,.lion,.tile")) shrink(); });
  }

  /* ===========================================================
     NAV
     =========================================================== */
  const nav = $("#nav"), burger = $("#burger");
  addEventListener("scroll", ()=>nav.classList.toggle("scrolled", scrollY>40), {passive:true});
  burger.addEventListener("click", ()=>nav.classList.toggle("open"));
  $$("#navLinks a").forEach(a=>a.addEventListener("click",()=>nav.classList.remove("open")));

  /* ===========================================================
     BOOKING FORM (mailto) + bundle prefill
     =========================================================== */
  const form = $("#bookForm"), hint = $("#formHint"), bundleSel = $("#f-bundle");
  document.addEventListener("click", e=>{
    const b = e.target.closest(".pick"); if(!b) return;
    const name = b.dataset.bundle;
    [...bundleSel.options].forEach(o=>{ if(o.text.startsWith(name)) bundleSel.value=o.value; });
    $("#contact").scrollIntoView({behavior:"smooth"});
    setTimeout(()=>$("#f-name").focus(), 700);
  });
  form.addEventListener("submit", e=>{
    e.preventDefault();
    const f = Object.fromEntries(new FormData(form).entries());
    if(!f.name || !f.email){ hint.textContent="Please add your name and email."; return; }
    const subject = encodeURIComponent(`Booking — ${f.bundle} — ${f.name}`);
    const body = encodeURIComponent(
      `Name: ${f.name}\nEmail: ${f.email}\nBundle: ${f.bundle}\nBudget: ${f.budget||"—"}\n\n${f.message||""}\n`);
    window.location.href = `mailto:${CONFIG.bookingEmail}?subject=${subject}&body=${body}`;
    hint.textContent = "Opening your email app… if nothing happens, write to " + CONFIG.bookingEmail;
  });

  /* ===========================================================
     LOADER → reveal
     =========================================================== */
  function startReveal(){
    const loader = $("#loader");
    if (window.gsap){
      gsap.to("#loader .loader-bar span",{width:"100%",duration:1,ease:"power2.inOut"});
    }
    setTimeout(()=>{
      loader.classList.add("done");
      heroIntro();
    }, 1100);
  }

  function heroIntro(){
    if (!window.gsap || prefersReduced){ counters(); return; }
    // draw the lion
    const strokes = $$("#lion line, #lion path, #lion circle");
    strokes.forEach(s=>{ const len = s.getTotalLength ? (s.getTotalLength()||60) : 60;
      s.style.strokeDasharray=len; s.style.strokeDashoffset=len; });
    const tl = gsap.timeline();
    tl.to(strokes,{strokeDashoffset:0,duration:1.1,stagger:0.012,ease:"power2.out"})
      .from(".hero-title .word",{yPercent:115,duration:1,ease:"expo.out"},"-=0.5")
      .from(".hero-eyebrow",{opacity:0,y:10,duration:0.6},"-=0.8")
      .from(".hero-sub",{opacity:0,y:20,duration:0.7},"-=0.5")
      .from(".hero-stats .stat",{opacity:0,y:20,stagger:0.08,duration:0.6},"-=0.4")
      .from(".hero-cta .btn",{opacity:0,y:20,stagger:0.1,duration:0.6},"-=0.4")
      .add(counters,"-=0.5")
      .from(".roar-hint",{opacity:0,duration:0.6});
  }

  function counters(){
    $$("[data-count]").forEach(el=>{
      const end = +el.dataset.count; const o = { v:0 };
      if(!window.gsap){ el.textContent=end; return; }
      gsap.to(o,{v:end,duration:1.4,ease:"power2.out",onUpdate(){ el.textContent=Math.round(o.v); }});
    });
  }

  /* ===========================================================
     SCROLL CHOREOGRAPHY (GSAP ScrollTrigger)
     =========================================================== */
  function initScroll(){
    if (!window.gsap || !window.ScrollTrigger || prefersReduced) return;
    gsap.registerPlugin(ScrollTrigger);
    if (window.ScrollToPlugin) gsap.registerPlugin(ScrollToPlugin);

    // headings rise
    $$(".section-head").forEach(h=>{
      gsap.from(h,{yPercent:18,opacity:0,duration:1,ease:"power3.out",
        scrollTrigger:{trigger:h,start:"top 85%"}});
    });
    // eyebrows + intros
    $$(".section-eyebrow,.muted,.story-body p,.bundle-note").forEach(el=>{
      gsap.from(el,{opacity:0,y:24,duration:0.9,ease:"power2.out",
        scrollTrigger:{trigger:el,start:"top 88%"}});
    });
    // gallery tiles
    gsap.utils.toArray(".tile").forEach((t,i)=>{
      gsap.from(t,{opacity:0,y:60,scale:0.96,duration:0.9,ease:"power3.out",
        scrollTrigger:{trigger:t,start:"top 92%"}});
    });
    // bundle cards
    gsap.from(".bundle",{opacity:0,y:70,duration:0.9,stagger:0.12,ease:"power3.out",
      scrollTrigger:{trigger:".bundle-grid",start:"top 82%"}});
    // story watermark parallax
    gsap.to("#storyMark",{yPercent:-30,ease:"none",
      scrollTrigger:{trigger:".story",start:"top bottom",end:"bottom top",scrub:true}});
    // contact form fields
    gsap.from(".field,.contact-side",{opacity:0,y:30,duration:0.8,stagger:0.06,ease:"power2.out",
      scrollTrigger:{trigger:".contact-wrap",start:"top 84%"}});
    // footer
    gsap.from(".footer-big,.footer-lion,.footer-socials",{opacity:0,y:30,duration:0.9,stagger:0.1,
      scrollTrigger:{trigger:".footer",start:"top 88%"}});

    // smooth anchor scrolling
    if (window.ScrollToPlugin){
      $$('a[href^="#"]').forEach(a=>a.addEventListener("click",e=>{
        const id=a.getAttribute("href"); if(id.length<2) return;
        const t=$(id); if(!t) return; e.preventDefault();
        gsap.to(window,{duration:1,scrollTo:{y:t,offsetY:0},ease:"power2.inOut"});
      }));
    }
  }

  /* ===========================================================
     BOOT
     =========================================================== */
  window.addEventListener("load", ()=>{
    initWebGL();
    initScroll();
    startReveal();
  });
})();
