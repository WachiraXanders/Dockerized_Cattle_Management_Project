# DairyPro — Mobile Deployment Guide

## What "mobile deployment" means for DairyPro today

DairyPro is a **responsive Progressive Web App (PWA)**, not a native
iOS/Android app built for the App Store or Play Store. As of this guide,
it can be:

1. Opened directly in any mobile browser — works immediately, zero setup.
2. **Installed** to a phone's home screen as a standalone app (its own
   icon, its own window, no visible browser chrome) via each platform's
   "Add to Home Screen" flow — this now works because the app has a real
   web app manifest and icon set (`frontend/public/manifest.json`,
   `frontend/public/icons/`), added specifically to make this possible.

There is no separate mobile codebase to build or publish — the same
frontend that runs on desktop is what mobile installs. This document
covers exactly how to get from "backend + frontend deployed somewhere"
(see the Deployment Guide) to "usable app icon on a phone."

## Prerequisites

- The backend and frontend are already deployed and reachable over
  **HTTPS** (see Deployment Guide §4, Production Deployment).
  **HTTPS is not optional** — browsers refuse to register a service
  worker, and refuse to offer "Install app," over plain HTTP on anything
  other than `localhost`. If you only have a local dev server running
  over `http://`, phones on your network can open it, but they will not
  be able to install it or use offline logging.
- `VITE_API_URL` was set to the backend's public HTTPS URL **at build
  time** (`npm run build`), not left pointing at `localhost`.

If you don't have a deployed HTTPS instance yet and just want to try this
on your own phone right now, see §5 below.

## 1. What was added to make this work

| File | Purpose |
|---|---|
| `frontend/public/manifest.json` | Declares the app's name, icons, theme color, and `display: standalone` — this is what makes "Add to Home Screen" produce a real app-like icon instead of a bookmark |
| `frontend/public/icons/icon-192.png`, `icon-512.png`, `icon-512-maskable.png`, `apple-touch-icon.png` | The actual icon images, generated in the app's brand colors (Obsidian background, Emerald badge) |
| `frontend/index.html` | Links the manifest, sets `theme-color`, and adds the `apple-mobile-web-app-*` meta tags iOS specifically requires (Apple does not read `manifest.json` for most of these) |
| `frontend/public/sw.js` (already existed) | The service worker that makes the app shell load reliably; required for installability on Android/Chrome |

No backend changes were needed for this.

## 2. Deploy steps (assuming you already have a production backend)

```bash
cd frontend
# make sure VITE_API_URL in .env points at your real backend's HTTPS URL
npm run build
```

Deploy the resulting `frontend/dist` folder to any static HTTPS host —
Vercel, Netlify, Cloudflare Pages, S3+CloudFront, or your own nginx/Caddy
server with a TLS certificate. See the Deployment Guide's frontend
section for platform specifics. That's the entire "mobile deployment"
step — there's no separate mobile build.

## 3. Installing on Android (Chrome)

1. Open the deployed HTTPS URL in Chrome on the phone.
2. Log in (or wait — Chrome may show its own "Install app" banner
   automatically after a moment).
3. Tap the **⋮** menu → **Install app** (or **Add to Home screen**,
   depending on Chrome version).
4. Confirm. DairyPro's icon appears on the home screen and app drawer,
   launching in its own standalone window (no address bar).

## 4. Installing on iOS (Safari)

iOS does not support Chrome's automatic install prompt — it must be done
manually in **Safari** specifically (not Chrome-on-iOS, which is just a
Safari wrapper and can't install PWAs):

1. Open the deployed HTTPS URL in Safari.
2. Tap the **Share** icon (square with an arrow pointing up).
3. Scroll down and tap **Add to Home Screen**.
4. Confirm the name ("DairyPro") and tap **Add**.
5. The DairyPro icon appears on the home screen, launching full-screen
   with the dark status bar styling set in `index.html`.

## 5. Trying it on your phone without a real deployment

If you just want to see it on your own phone during development, without
setting up HTTPS hosting yet:

1. Make sure your phone and your development machine are on the **same
   Wi-Fi network**.
2. Start the backend bound to all interfaces:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. Find your machine's local IP (e.g. `192.168.1.42`).
4. Run the frontend dev server, with the API URL pointed at that IP:
   ```bash
   VITE_API_URL=http://192.168.1.42:8000 npm run dev -- --host
   ```
5. On your phone's browser, go to `http://192.168.1.42:5173`.

This lets you use the app on your phone's browser and verify the
responsive layout, but **"Add to Home Screen" installability and the
offline Quick Log feature will not work** over plain HTTP — those
specifically require HTTPS (§1 above). Treat this as a layout/functional
preview only, not a substitute for a real deployment.

## 6. What works once installed

- Every page — Dashboard through Settings — renders using the same
  responsive layout already built for mobile (collapsible sidebar drawer,
  stacked KPI grids, horizontally-scrolling tables).
- **Offline milk and health logging** (see the SRS's offline support
  requirements) works from the installed app exactly as it does in the
  browser — the "Quick Log" flow queues entries locally and syncs
  automatically once back online. This is the main practical benefit of
  installing versus just bookmarking: the offline banner and Quick Log
  button are reachable without a browser address bar in the way.
- Dark ("Obsidian") theme is the default on first launch, matching the
  installed icon's branding; the theme toggle in Settings still works
  from the installed app.

## 7. What does not work / is not included

- **No app store distribution.** This is not published to the Play Store
  or App Store — installation is entirely via the browser's "Add to Home
  Screen" flow described above. There is no `.apk`/`.ipa` build pipeline.
- **No push notifications.** The manifest/service worker added here only
  covers installability and static-asset caching, not a push messaging
  backend.
- **Offline support is scoped to Milk and Health logging only** (see the
  Architecture doc's offline layer notes) — every other page still
  requires a live connection when used from the installed app.
- **No biometric login, camera-based tag scanning, or other native-only
  capabilities** — the installed app has the same feature set as the
  browser tab it came from, just presented full-screen with an icon.

## 8. Verifying the install actually worked

- Android/Chrome: `chrome://inspect/#service-workers` (on desktop Chrome,
  connected to the phone via USB debugging) or Chrome DevTools' remote
  device inspector → **Application** tab → confirm the service worker is
  "activated and running" and the manifest is recognized with no errors.
- iOS/Safari: there's no equivalent inspector for most users; the
  practical check is simply that the home-screen icon launches full-screen
  (no Safari address bar) — if it still opens inside Safari's browser
  chrome, the manifest/meta tags weren't picked up (usually because the
  site isn't served over HTTPS, or `index.html` wasn't rebuilt/redeployed
  after this change).
- Either platform: open the installed app, turn on Airplane Mode, tap
  **Quick Log**, and confirm you can still save a milk entry — this
  exercises the actual offline capability end-to-end, not just the icon.
