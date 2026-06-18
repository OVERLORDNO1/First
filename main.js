/* =================================================================
   ANA — Khaleesi of the Wind  ·  main.js
   ----------------------------------------------------------------
   EDIT THESE FIRST — everything personal lives in CONFIG:
   ================================================================= */
const CONFIG = {
  bookingEmail: "contact@khaleesianahita.com",
  socials: {
    tiktok: "https://www.tiktok.com/@khaleesianahita",
    instagram: "https://www.instagram.com/khaleesianahita/",
  },

  /* --- PHOTOS ---------------------------------------------------
     Upload images to assets/gallery/ named 01.jpg … 10.jpg and a
     portrait at assets/ana.jpg. They power BOTH the main gallery and
     the floating background. Missing files fall back gracefully.    */
  portrait: "assets/ana.jpg",
  photos: [
    "assets/gallery/01.jpg","assets/gallery/02.jpg","assets/gallery/03.jpg",
    "assets/gallery/04.jpg","assets/gallery/05.jpg","assets/gallery/06.jpg",
    "assets/gallery/07.jpg","assets/gallery/08.jpg","assets/gallery/09.jpg",
    "assets/gallery/10.jpg",
  ],

  /* --- STATS (views & achievements, not money) ----------------- */
  stats: [
    { to:314, dec:0, suffix:"K",  label:"Followers · TikTok" },
    { to:50,  dec:0, suffix:"M+", label:"Total video views" },
    { to:1.2, dec:1, suffix:"K+", label:"Live streams" },
    { to:120, dec:0, suffix:"K",  label:"Peak live viewers" },
  ],
  badges: [
    "TikTok LIVE Fest","LIVE Subscription creator","Top UK lifestyle live",
    "Self-love advocate","Performer & broadcaster",
  ],

  /* --- TIKTOK VIDEOS (real video IDs to embed) ----------------- */
  tiktokVideos: ["7533595737632869654","7509104230767152406","7505108315974700310"],

  /* --- BUNDLES ------------------------------------------------- */
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
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isTouch = matchMedia("(pointer: coarse)").matches;
  const $  = (s,r=document)=>r.querySelector(s);
  const $$ = (s,r=document)=>[...r.querySelectorAll(s)];

  /* ============ BUILD CONTENT ============ */
  // gallery tiles
  const gg = $("#galleryGrid");
  CONFIG.gallery.forEach((g,i)=>{
    const t=document.createElement("div"); t.className=`tile ${g.cls}`.trim();
    const src=CONFIG.photos[i];
    const shot=src?`<img class="shot" src="${src}" alt="${g.cap}" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`:"";
    t.innerHTML=`<span class="tile-num">${String(i+1).padStart(2,"0")}</span><div class="ph">${g.emoji}</div>${shot}<div class="cap">${g.cap}</div>`;
    gg.appendChild(t);
  });

  // bundles
  const bg=$("#bundleGrid");
  CONFIG.bundles.forEach(b=>{
    const c=document.createElement("article"); c.className=`bundle lg${b.feature?" feature":""}`;
    c.innerHTML=`<span class="tier-tag">${b.tag}</span><h3>${b.name}</h3><p class="blurb">${b.blurb}</p>
      <div class="price">${b.price}<small>${b.unit}</small></div>
      <ul>${b.perks.map(p=>`<li>${p}</li>`).join("")}</ul>
      <button class="btn line pick" data-bundle="${b.name}" data-cursor>Book ${b.name}</button>`;
    bg.appendChild(c);
  });

  // stats
  const sg=$("#statGrid");
  CONFIG.stats.forEach(s=>{
    const c=document.createElement("div"); c.className="stat-card lg";
    c.innerHTML=`<div class="num"><span class="val" data-to="${s.to}" data-dec="${s.dec}">0</span><span class="suf">${s.suffix}</span></div><div class="lbl">${s.label}</div>`;
    sg.appendChild(c);
  });
  // badges
  const bd=$("#badges");
  CONFIG.badges.forEach(b=>{ const e=document.createElement("span"); e.className="badge"; e.innerHTML=`<i>✦</i>${b}`; bd.appendChild(e); });

  // portrait
  const portrait=$("#anaPortrait"), pWrap=$("#storyPortrait");
  portrait.addEventListener("load",()=>pWrap.classList.add("has-photo"));
  portrait.addEventListener("error",()=>{ portrait.removeAttribute("src"); });
  portrait.src=CONFIG.portrait;

  $("#year").textContent=new Date().getFullYear();

  /* ============ LION MANE ============ */
  (function(){const m=$("#lionMane"),cx=100,cy=104,N=30;
    for(let i=0;i<N;i++){const a=(i/N)*Math.PI*2-Math.PI/2,r1=38,r2=i%2?70:60;
      const l=document.createElementNS("http://www.w3.org/2000/svg","line");
      l.setAttribute("x1",(cx+Math.cos(a)*r1).toFixed(1));l.setAttribute("y1",(cy+Math.sin(a)*r1).toFixed(1));
      l.setAttribute("x2",(cx+Math.cos(a)*r2).toFixed(1));l.setAttribute("y2",(cy+Math.sin(a)*r2).toFixed(1));
      l.setAttribute("stroke-width",i%2?"1":"1.6");m.appendChild(l);}})();

  /* ============ FLOATING BACKGROUND GALLERY ============ */
  function initFloat(){
    if(reduced) return;
    const wrap=$("#floatGallery"); const N=isTouch?6:10;
    for(let i=0;i<N;i++){
      const card=document.createElement("div"); card.className="float-card";
      const src=CONFIG.photos[i%CONFIG.photos.length];
      card.innerHTML=`<img src="${src}" alt="" referrerpolicy="no-referrer" onerror="this.parentNode.innerHTML='<div class=&quot;fc-fallback&quot;>🦁</div>'">`;
      const depth=0.4+Math.random()*0.8;
      card.style.left=(Math.random()*90)+"vw";
      card.style.top=(Math.random()*90)+"vh";
      card.style.transform=`scale(${depth})`;
      card.dataset.depth=depth;
      wrap.appendChild(card);
      if(window.gsap){
        gsap.to(card,{y:`+=${30+Math.random()*40}`,x:`+=${-20+Math.random()*40}`,rotation:-6+Math.random()*12,
          duration:6+Math.random()*6,repeat:-1,yoyo:true,ease:"sine.inOut",delay:Math.random()*4});
      }
    }
    if(!isTouch){
      addEventListener("mousemove",e=>{
        const dx=(e.clientX/innerWidth-0.5),dy=(e.clientY/innerHeight-0.5);
        wrap.style.transform=`translate(${dx*-30}px,${dy*-22}px)`;
      });
    }
  }

  /* ============ WEBGL EMBER FIELD ============ */
  let renderer,scene,camera,embers; const ptr={x:0,y:0,tx:0,ty:0};
  function initWebGL(){
    if(reduced||typeof THREE==="undefined") return;
    const canvas=$("#webgl");
    renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true});
    renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setSize(innerWidth,innerHeight);
    scene=new THREE.Scene(); scene.fog=new THREE.FogExp2(0x0a0a0b,0.055);
    camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,0.1,100); camera.position.z=24;
    const COUNT=isTouch?500:1300;
    const geo=new THREE.BufferGeometry(); const pos=new Float32Array(COUNT*3),spd=new Float32Array(COUNT),off=new Float32Array(COUNT);
    for(let i=0;i<COUNT;i++){pos[i*3]=(Math.random()-.5)*60;pos[i*3+1]=(Math.random()-.5)*60;pos[i*3+2]=(Math.random()-.5)*40;
      spd[i]=.4+Math.random()*1.4;off[i]=Math.random()*Math.PI*2;}
    geo.setAttribute("position",new THREE.BufferAttribute(pos,3));
    const c=document.createElement("canvas");c.width=c.height=64;const g=c.getContext("2d");
    const gr=g.createRadialGradient(32,32,0,32,32,32);
    gr.addColorStop(0,"rgba(255,225,150,1)");gr.addColorStop(.3,"rgba(232,184,75,.7)");gr.addColorStop(1,"rgba(232,184,75,0)");
    g.fillStyle=gr;g.fillRect(0,0,64,64);
    const mat=new THREE.PointsMaterial({size:.5,map:new THREE.CanvasTexture(c),transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,opacity:.9});
    embers=new THREE.Points(geo,mat); embers.userData={spd,off}; scene.add(embers);
    addEventListener("resize",()=>{renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();});
    if(!isTouch) addEventListener("mousemove",e=>{ptr.tx=e.clientX/innerWidth-.5;ptr.ty=e.clientY/innerHeight-.5;});
    (function loop(t){requestAnimationFrame(loop);const time=t*.001;const{spd,off}=embers.userData;
      const a=embers.geometry.attributes.position.array;
      for(let i=0;i<spd.length;i++){a[i*3+1]+=spd[i]*.02;a[i*3]+=Math.sin(time*.5+off[i])*.01;
        if(a[i*3+1]>30){a[i*3+1]=-30;a[i*3]=(Math.random()-.5)*60;}}
      embers.geometry.attributes.position.needsUpdate=true;embers.rotation.y=time*.02;
      ptr.x+=(ptr.tx-ptr.x)*.04;ptr.y+=(ptr.ty-ptr.y)*.04;camera.position.x=ptr.x*6;camera.position.y=-ptr.y*4;camera.lookAt(0,0,0);
      renderer.render(scene,camera);})(0);
  }

  /* ============ 2D FX — roar ============ */
  const fx=$("#fx"),fxc=fx.getContext("2d");let sparks=[],rings=[];
  const sizeFx=()=>{fx.width=innerWidth;fx.height=innerHeight;};sizeFx();addEventListener("resize",sizeFx);
  function roar(){
    const r=$("#lion").getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;
    rings.push({x,y,rad:10,life:1});
    for(let i=0;i<(reduced?0:90);i++){const a=Math.random()*Math.PI*2,s=2+Math.random()*10;
      sparks.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s-2,g:.12,size:1+Math.random()*3,life:1,decay:.008+Math.random()*.02});}
    if(window.gsap){gsap.fromTo("#lion",{scale:.9},{scale:1,duration:1.1,ease:"elastic.out(1,.35)"});
      document.body.animate([{transform:"translate(0,0)"},{transform:"translate(-6px,3px)"},{transform:"translate(5px,-4px)"},{transform:"translate(0,0)"}],{duration:380,easing:"ease-out"});}
    playRoar();
  }
  (function draw(){requestAnimationFrame(draw);fxc.clearRect(0,0,fx.width,fx.height);
    for(let i=rings.length-1;i>=0;i--){const r=rings[i];r.rad+=14;r.life-=.025;if(r.life<=0){rings.splice(i,1);continue;}
      fxc.beginPath();fxc.arc(r.x,r.y,r.rad,0,7);fxc.strokeStyle=`rgba(232,184,75,${r.life*.6})`;fxc.lineWidth=2*r.life;fxc.stroke();}
    fxc.globalCompositeOperation="lighter";
    for(let i=sparks.length-1;i>=0;i--){const p=sparks[i];p.vy+=p.g;p.x+=p.vx;p.y+=p.vy;p.life-=p.decay;if(p.life<=0){sparks.splice(i,1);continue;}
      fxc.beginPath();fxc.arc(p.x,p.y,p.size,0,7);fxc.fillStyle=`rgba(255,${200+(Math.random()*40|0)},120,${p.life})`;fxc.shadowBlur=10;fxc.shadowColor="rgba(232,184,75,.8)";fxc.fill();}
    fxc.globalCompositeOperation="source-over";fxc.shadowBlur=0;})();
  let actx;
  function playRoar(){if(reduced)return;try{actx=actx||new(AudioContext||webkitAudioContext)();const t=actx.currentTime;
    const o=actx.createOscillator(),g=actx.createGain(),f=actx.createBiquadFilter();
    o.type="sawtooth";o.frequency.setValueAtTime(90,t);o.frequency.exponentialRampToValueAtTime(38,t+.5);
    f.type="lowpass";f.frequency.value=420;g.gain.setValueAtTime(.0001,t);
    g.gain.exponentialRampToValueAtTime(.32,t+.05);g.gain.exponentialRampToValueAtTime(.0001,t+.85);
    o.connect(f);f.connect(g);g.connect(actx.destination);o.start(t);o.stop(t+.9);}catch(e){}}
  const lion=$("#lion");
  lion.addEventListener("click",roar);
  lion.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();roar();}});

  /* ============ LIQUID-GLASS POINTER SHEEN ============ */
  if(!isTouch){
    document.addEventListener("mousemove",e=>{
      const el=e.target.closest(".lg"); if(!el)return;
      const r=el.getBoundingClientRect();
      el.style.setProperty("--mx",((e.clientX-r.left)/r.width*100)+"%");
      el.style.setProperty("--my",((e.clientY-r.top)/r.height*100)+"%");
    });
  }

  /* ============ CUSTOM CURSOR ============ */
  if(!isTouch&&!reduced){
    const cur=$("#cursor");let cx=innerWidth/2,cy=innerHeight/2,x=cx,y=cy;
    addEventListener("mousemove",e=>{cx=e.clientX;cy=e.clientY;});
    (function t(){x+=(cx-x)*.2;y+=(cy-y)*.2;cur.style.transform=`translate(${x}px,${y}px) translate(-50%,-50%)`;requestAnimationFrame(t);})();
    document.addEventListener("mouseover",e=>{if(e.target.closest("[data-cursor],a,button,.lion,.tile"))cur.classList.add("grow");});
    document.addEventListener("mouseout",e=>{if(e.target.closest("[data-cursor],a,button,.lion,.tile"))cur.classList.remove("grow");});
  }

  /* ============ NAV ============ */
  const nav=$("#nav"),burger=$("#burger");
  addEventListener("scroll",()=>nav.classList.toggle("scrolled",scrollY>40),{passive:true});
  burger.addEventListener("click",()=>nav.classList.toggle("open"));
  $$("#navLinks a").forEach(a=>a.addEventListener("click",()=>nav.classList.remove("open")));

  /* ============ TIKTOK EMBEDS ============ */
  function initTikTok(){
    const wrap=$("#ttEmbeds"); const u=CONFIG.socials.tiktok;
    CONFIG.tiktokVideos.forEach(id=>{
      const bq=document.createElement("blockquote");
      bq.className="tiktok-embed"; bq.cite=`${u}/video/${id}`; bq.setAttribute("data-video-id",id);
      bq.style.maxWidth="325px"; bq.style.minWidth="280px";
      bq.innerHTML=`<section><a target="_blank" rel="noopener" href="${u}">@khaleesianahita on TikTok</a></section>`;
      wrap.appendChild(bq);
    });
    const s=document.createElement("script"); s.src="https://www.tiktok.com/embed.js"; s.async=true; document.body.appendChild(s);
  }

  /* ============ BOOKING FORM ============ */
  const form=$("#bookForm"),hint=$("#formHint"),sel=$("#f-bundle");
  document.addEventListener("click",e=>{const b=e.target.closest(".pick");if(!b)return;
    const n=b.dataset.bundle;[...sel.options].forEach(o=>{if(o.text.startsWith(n))sel.value=o.value;});
    scrollToEl("#contact");setTimeout(()=>$("#f-name").focus(),700);});
  form.addEventListener("submit",e=>{e.preventDefault();
    const f=Object.fromEntries(new FormData(form).entries());
    if(!f.name||!f.email){hint.textContent="Please add your name and email.";return;}
    const sub=encodeURIComponent(`Booking — ${f.bundle} — ${f.name}`);
    const body=encodeURIComponent(`Name: ${f.name}\nEmail: ${f.email}\nBundle: ${f.bundle}\nBudget: ${f.budget||"—"}\n\n${f.message||""}\n`);
    location.href=`mailto:${CONFIG.bookingEmail}?subject=${sub}&body=${body}`;
    hint.textContent="Opening your email app… if nothing happens, write to "+CONFIG.bookingEmail;});

  /* ============ SMOOTH SCROLL (Lenis) + SCROLLTRIGGER ============ */
  let lenis;
  function initSmooth(){
    if(window.gsap&&window.ScrollTrigger) gsap.registerPlugin(ScrollTrigger);
    if(window.gsap&&window.ScrollToPlugin) gsap.registerPlugin(ScrollToPlugin);
    if(typeof Lenis!=="undefined"&&!reduced){
      lenis=new Lenis({lerp:.1,smoothWheel:true});
      lenis.on("scroll",()=>window.ScrollTrigger&&ScrollTrigger.update());
      if(window.gsap){gsap.ticker.add(t=>lenis.raf(t*1000));gsap.ticker.lagSmoothing(0);}
      else (function raf(t){lenis.raf(t);requestAnimationFrame(raf);})();
    }
  }
  function scrollToEl(id){const t=$(id);if(!t)return;
    if(lenis)lenis.scrollTo(t,{duration:1.1});
    else if(window.gsap&&window.ScrollToPlugin)gsap.to(window,{duration:1,scrollTo:{y:t},ease:"power2.inOut"});
    else t.scrollIntoView({behavior:"smooth"});}

  function initScroll(){
    if(!window.gsap||!window.ScrollTrigger||reduced) return;
    $$(".section-head").forEach(h=>gsap.from(h,{yPercent:16,opacity:0,duration:1,ease:"power3.out",scrollTrigger:{trigger:h,start:"top 86%"}}));
    $$(".section-eyebrow,.muted,.story-body p,.bundle-note,.badge").forEach(el=>gsap.from(el,{opacity:0,y:22,duration:.85,ease:"power2.out",scrollTrigger:{trigger:el,start:"top 90%"}}));
    // stat cards with clip reveal
    gsap.utils.toArray(".stat-card").forEach((c,i)=>gsap.from(c,{opacity:0,y:50,scale:.95,duration:.9,ease:"power3.out",
      scrollTrigger:{trigger:c,start:"top 88%",onEnter:()=>animateCount(c)}}));
    gsap.utils.toArray(".tile").forEach(t=>gsap.from(t,{opacity:0,y:60,scale:.96,duration:.9,ease:"power3.out",scrollTrigger:{trigger:t,start:"top 92%"}}));
    gsap.from(".bundle",{opacity:0,y:70,duration:.9,stagger:.12,ease:"power3.out",scrollTrigger:{trigger:".bundle-grid",start:"top 82%"}});
    gsap.from(".story-portrait",{opacity:0,x:-40,duration:1,ease:"power3.out",scrollTrigger:{trigger:".story-grid",start:"top 80%"}});
    gsap.to("#storyMark",{yPercent:-26,ease:"none",scrollTrigger:{trigger:".story",start:"top bottom",end:"bottom top",scrub:true}});
    gsap.from(".tt-embeds blockquote, .tt-card-fallback",{opacity:0,y:40,stagger:.1,duration:.8,ease:"power2.out",scrollTrigger:{trigger:".tt-embeds",start:"top 85%"}});
    gsap.from(".field,.contact-side",{opacity:0,y:30,duration:.8,stagger:.06,ease:"power2.out",scrollTrigger:{trigger:".contact-wrap",start:"top 84%"}});
    gsap.from(".footer-big,.footer-lion,.footer-socials",{opacity:0,y:30,duration:.9,stagger:.1,scrollTrigger:{trigger:".footer",start:"top 88%"}});
    $$('a[href^="#"]').forEach(a=>a.addEventListener("click",e=>{const id=a.getAttribute("href");if(id.length<2)return;e.preventDefault();scrollToEl(id);}));
  }

  function animateCount(card){
    $$(".val",card).forEach(el=>{
      if(el.dataset.done)return; el.dataset.done="1";
      const to=+el.dataset.to,dec=+el.dataset.dec,o={v:0};
      if(!window.gsap){el.textContent=to.toFixed(dec);return;}
      gsap.to(o,{v:to,duration:1.6,ease:"power2.out",onUpdate(){el.textContent=o.v.toFixed(dec);}});
    });
  }

  /* ============ LOADER / INTRO ============ */
  function startReveal(){
    const loader=$("#loader");
    if(window.gsap)gsap.to("#loader .loader-bar span",{width:"100%",duration:1,ease:"power2.inOut"});
    setTimeout(()=>{loader.classList.add("done");heroIntro();},1100);
  }
  function heroIntro(){
    if(!window.gsap||reduced)return;
    const strokes=$$("#lion line,#lion path,#lion circle");
    strokes.forEach(s=>{const len=s.getTotalLength?(s.getTotalLength()||60):60;s.style.strokeDasharray=len;s.style.strokeDashoffset=len;});
    gsap.timeline()
      .to(strokes,{strokeDashoffset:0,duration:1.1,stagger:.012,ease:"power2.out"})
      .from(".hero-title .word",{yPercent:115,duration:1,ease:"expo.out"},"-=.5")
      .from(".hero-eyebrow",{opacity:0,y:10,duration:.6},"-=.8")
      .from(".hero-sub",{opacity:0,y:20,duration:.7},"-=.5")
      .from(".hero-cta .btn",{opacity:0,y:20,stagger:.1,duration:.6},"-=.4")
      .from(".roar-hint",{opacity:0,duration:.6},"-=.2");
  }

  /* ============ BOOT ============ */
  addEventListener("load",()=>{
    initSmooth(); initWebGL(); initFloat(); initTikTok(); initScroll(); startReveal();
    if(reduced) $$(".val").forEach(el=>el.textContent=(+el.dataset.to).toFixed(+el.dataset.dec));
    // refresh triggers once TikTok iframes change layout
    setTimeout(()=>window.ScrollTrigger&&ScrollTrigger.refresh(),2500);
  });
})();
