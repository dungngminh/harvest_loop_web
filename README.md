# Harvest Loop Web

Marketing site for **Puzzle Farming: Harvest Loop** — built with [Astro](https://astro.build).

## Development

```bash
npm install
npm run dev
```

Open [http://localhost:4321](http://localhost:4321).

## Build

```bash
npm run build
npm run preview
```

Static output is written to `dist/`.

## Configuration

Edit [`src/data/site.ts`](src/data/site.ts) to update:

- Production URL (`url`) — currently set to Vercel preview placeholder
- App Store link (`appStore`) — update when the listing goes live
- Legal effective dates

Also update `site` in [`astro.config.mjs`](astro.config.mjs) to match.

## Deploy

Deploy `dist/` to Vercel (or any static host). Point the iOS app's Terms and Privacy URLs to:

- `https://<your-domain>/terms`
- `https://<your-domain>/privacy`

## Assets

Brand assets are copied from the iOS app:

- `public/fonts/PressStart2P.ttf`
- `public/icon/app-icon.png`
- `public/og.png` — Open Graph card (1200×630). Regenerate with `npm run generate:og`.

Gameplay screenshots live in `public/screens/`. Cropped game assets (carrots, hero scene, stars, block palette) live in `public/assets/`. Re-capture with the DEBUG launch args documented in the game's `docs/ARCHITECTURE.md`.

## Structure

```
src/
  components/   # Landing sections + brand components
  data/site.ts  # Site-wide config
  layouts/      # Base + Legal shells
  pages/        # index, terms, privacy
```
