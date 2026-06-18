# ANA — *Khaleesi of the Wind* 🦁🌬️

A high-end, cinematic creator site built for **Ana** ([@khaleesianahita](https://www.tiktok.com/@khaleesianahita)) — a surprise to launch her next chapter. Molten-obsidian luxury: gold on near-black, a roaring lion sigil, WebGL embers, and GSAP scroll storytelling. Built mobile-first.

## ✨ Highlights
- **Roaring lion sigil** — tap it for a shockwave, ember burst, screen shake and a low roar (the page's signature moment)
- **WebGL ember/wind field** (three.js) drifting behind everything, with cursor parallax
- **GSAP scroll choreography** — staggered reveals, parallax watermark, animated stat counters
- **Glassmorphism** panels with gold hairline borders, film grain + vignette atmosphere
- **The Story of Ana** — an editorial long-form section
- **From the Live** — a gallery wall ready for real stream clips/photos
- **Work with Ana** — a creator media-kit / rate card with three bookable bundles (The Gust · The Spotlight · The Tempest)
- **Booking form** that composes an email, plus direct TikTok & Instagram links
- Fully **responsive** + respects `prefers-reduced-motion`; custom cursor on desktop only

## 🛠 Make it hers — edit `main.js` → `CONFIG`
Everything personalisable lives in one object at the top of `main.js`:
- `bookingEmail` — **set Ana's real booking inbox** (currently a placeholder)
- `socials` — TikTok / Instagram URLs
- `bundles` — names, prices (GBP, indicative), and perks
- `gallery` — captions/emoji per tile (swap in real images by giving each `.tile` a background image)

Follower numbers (314K TikTok / 13K IG) are public estimates — tweak them in `index.html` if needed.

## ▶️ View it
Open `index.html` in any modern browser (the animation libraries load from a CDN, so you need internet).

```bash
python3 -m http.server 8000   # then open http://localhost:8000
```

## 🗂 Files
| File | Purpose |
|------|---------|
| `index.html` | Structure & content |
| `styles.css` | Theme, layout & responsive design |
| `main.js` | WebGL embers, roaring lion, GSAP scroll, form & config |

Made with fire & wind. 🔥🌬️
