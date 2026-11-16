# AutoSum Frontend — Vercel Python Proxy + External FastAPI

កញ្ចប់នេះរក្សា Dashboard Frontend ដើម ហើយប្រើ **Python Vercel Functions** ដើម្បីអាន Backend URL ពី Environment Variable និង Proxy សំណើទៅ FastAPI Server ខាងក្រៅ។ Browser JavaScript **មិនអាន និងមិនទទួល URL របស់ FastAPI Backend ទេ**។

## Architecture

```text
Browser
  | same-origin: /api/groups, /api/analytics, /api/media
  v
Vercel static frontend + Python Functions
  | Python reads os.getenv("AUTOSUM_API_BASE_URL")
  v
External Python FastAPI Server
```

## 1. Vercel Environment Variable

Open **Vercel Dashboard → Project → Settings → Environment Variables** and add:

- **Name:** `AUTOSUM_API_BASE_URL`
- **Value:** `https://YOUR-FASTAPI-SERVER-DOMAIN`
- **Environment:** Production (also Preview/Development when needed)

Use the backend base URL only. Do not append `/api`.

Example:

```env
AUTOSUM_API_BASE_URL=https://api.example.com
```

Save and redeploy. The Python Functions read this variable at request time with `os.getenv()`; it is not inserted into HTML or JavaScript.

## 2. Vercel Project Settings

- Framework Preset: **Other**
- Root Directory: project root (the folder containing `index.html` and `api/`)
- Build Command: **empty**
- Output Directory: **empty**
- Install Command: **empty**

There is no Node build command and no `config.js` generation step. Vercel serves the static `index.html`; Python files under `api/` are deployed as Python Functions.

## 3. Python routes

| Browser request on Vercel | Python forwards to external FastAPI |
|---|---|
| `GET /api/groups` | `GET /api/groups` |
| `POST /api/analytics` | `POST /api/analytics` |
| `GET /api/health` | `GET /api/health` |
| `GET /api/media?path=%2Fimage.png` | `GET /image.png` |
| `GET /api/media?path=%2Fstatic%2Fgroup_photos%2F123.jpg` | `GET /static/group_photos/123.jpg` |

The media route allows only the app logos, PWA icons, welcome audio, and group photo paths. It is not an open proxy.

## 4. External FastAPI server requirements

The backend must expose:

- `GET /api/groups`
- `POST /api/analytics`
- `GET /api/health`

It must also serve the media resources used by the original frontend when those files are present:

- `/image.png`, `/images.png`, `/welcome.mp3`
- `/icon-96.png`, `/icon-128.png`, `/icon-144.png`, `/icon-152.png`, `/icon-180.png`, `/icon-192.png`, `/icon-256.png`, `/icon-384.png`, `/icon-512.png`
- `/apple-touch-icon.png`, `/apple-touch-icon-precomposed.png`
- `/static/group_photos/<filename>`

If your current FastAPI backend doesn't expose these files yet, the dashboard API can still be proxied, but the corresponding logos/audio/group photos won't display until those existing resources are served from the backend. This ZIP does not move or copy your backend data.

The browser communicates only with the Vercel origin, so browser-to-backend CORS is not needed for these proxied requests. The backend must be reachable from Vercel over HTTPS.

## 5. Security and limits

- Keep Telegram tokens, database credentials, and other secrets on the external backend only.
- `AUTOSUM_API_BASE_URL` is read only by Python server-side code.
- The proxy forwards only fixed API paths and an explicit media allowlist.
- Analytics request body limit: 2 MiB.
- Proxy upstream timeout: 25 seconds. The Vercel plan's function execution/response limits still apply.

## 6. Local syntax check

```powershell
py -3.12 -m compileall api proxy_utils.py
```
