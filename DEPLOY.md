# Deploying Smart Cow to Render (free tier)

These files are already in the repo:

- `runtime.txt` — pins **Python 3.11.9** (avoids the PyYAML 6.0 build failure on 3.12+).
- `build.sh` — installs deps, runs `collectstatic`, runs `migrate`.
- `render.yaml` — describes the web service (build/start commands + env vars).
- `requirements.txt` — includes `gunicorn` and `whitenoise`.

The start command runs a **single Gunicorn worker** with threads:
`gunicorn config.wsgi --workers 1 --threads 4 --timeout 120`
(one worker so the in-process recommender cache is shared; the 120s timeout covers the slow LOV lookups).

---

## 1. Push the repo to GitHub
If it isn't on GitHub yet:

```bash
git add .
git commit -m "Add Render deployment config"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

## 2. Create the service on Render
1. Sign up / log in at https://render.com (free, GitHub login is easiest).
2. **New +** → **Blueprint** → connect your GitHub account → pick this repo.
3. Render reads `render.yaml` and shows a service called **smartcow**. Click **Apply**.
   - `DJANGO_SECRET_KEY` is generated automatically.
   - `DJANGO_DEBUG=False` and the Python version are set for you.
4. First build + deploy starts (~3–5 min). Watch the log; it should end with the
   service "Live" and a URL like `https://smartcow.onrender.com`.

## 3. Set the CSRF origin (one-time, after you know the URL)
POST requests (upload, save, convert) need the site's HTTPS origin trusted.
1. In the Render dashboard → your service → **Environment**.
2. Edit **DJANGO_CSRF_TRUSTED_ORIGINS** and set it to your real URL, e.g.
   `https://smartcow.onrender.com`
3. Save — Render redeploys automatically.

(`DJANGO_ALLOWED_HOSTS` is filled from the service hostname automatically.)

## 4. Test
Open the URL and run a full pass: upload a CSV → matches load → edit metadata →
Save → Convert → download the `.nq`. Then share the link.

---

## Good to know
- **Cold start:** the free instance sleeps after ~15 min idle; the next visit
  takes ~50s to wake, then it's responsive.
- **Ephemeral storage:** uploaded files, the SQLite DB, and the recommender cache
  reset when the instance restarts/redeploys. Each user's session is isolated
  (`media/uploads/<session-id>/`), so concurrent evaluators don't collide, but a
  user returning after a cold start should re-upload.
- **Support form submissions** are stored in SQLite, so they are **not durable**
  across restarts. If you need to keep them, add a free Render PostgreSQL
  database and point `DATABASES` at it via a `DATABASE_URL` env var (ask and I'll
  wire it up with `dj-database-url`).
- **Updating the app:** push to the `main` branch → Render auto-deploys.

## Manual setup (without the Blueprint)
If you'd rather create the service by hand: **New + → Web Service**, pick the repo, then set
- Build Command: `./build.sh`
- Start Command: `gunicorn config.wsgi --workers 1 --threads 4 --timeout 120`
- Environment: `DJANGO_SECRET_KEY` (any long random string), `DJANGO_DEBUG=False`,
  `DJANGO_ALLOWED_HOSTS=<app>.onrender.com`,
  `DJANGO_CSRF_TRUSTED_ORIGINS=https://<app>.onrender.com`,
  `PYTHON_VERSION=3.11.9`.
