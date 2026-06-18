# 📸 How to add Ana's photos

The site automatically uses any photos you drop in here — no code editing needed.

## What to upload

| File | Where it shows |
|------|----------------|
| `assets/ana.jpg` | The portrait frame in the **Story** section |
| `assets/gallery/01.jpg` … `10.jpg` | The **gallery** wall + the **floating background** |

- Until you upload, each slot shows a generated on-brand poster (`art-NN.svg` / `ana-art.svg`). Your real photo automatically takes priority once added — so you can do them one at a time.
- Square or portrait (vertical) photos look best. JPG or PNG both fine.
- Keep each file under ~1–2 MB so the page stays fast (resize big phone photos first).

## Easiest way to upload (no tools needed)

1. Go to the repo on GitHub and switch to the branch **`claude/funny-ritchie-pi6si4`**.
2. Open the **`assets/gallery`** folder.
3. Click **Add file → Upload files**.
4. Drag in Ana's photos. **Rename them** `01.jpg`, `02.jpg`, `03.jpg` … so they match.
5. For the portrait, upload one file named **`ana.jpg`** into the **`assets`** folder.
6. Commit. The live site updates automatically within a minute.

> Want different filenames or more than 10 photos? Tell Claude and the list in
> `main.js → CONFIG.photos` can be changed to match.
