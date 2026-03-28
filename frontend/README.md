# Tubee Frontend

AI-powered video editing for creators and videographers. Built with Next.js 14, Tailwind CSS, and TypeScript.

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Tech Stack

- **Next.js 14** — App Router
- **Tailwind CSS** — Styling
- **TypeScript** — Type safety

## Pages

- `/` — Landing page (features, pricing, CTA)
- `/editor` — Upload footage, describe your edit, get a reel

## API

The frontend proxies API calls to the backend at `http://localhost:8000` via Next.js rewrites.

| Endpoint | Method | Description |
|---|---|---|
| `/upload` | POST | Upload video/music files |
| `/edit` | POST | Submit edit job (prompt + style) |
| `/status/{job_id}` | GET | Poll job progress |
| `/download/{job_id}` | GET | Download finished video |

## Environment

Make sure the Tubee backend is running on port 8000 before using the editor.
