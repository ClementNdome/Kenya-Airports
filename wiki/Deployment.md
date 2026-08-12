# Deployment

## Options

| Path | Config | Notes |
|---|---|---|
| **Docker** | `Dockerfile` | `python:3.12-slim` + `libgdal-dev`, `libgeos-dev`, `libproj-dev`, `proj-bin`, `proj-data`, gcc/g++, `libcairo2-dev`, `libpango1.0-dev`, `libjpeg-dev`, `libfreetype6-dev`; `collectstatic --noinput`; gunicorn on `0.0.0.0:8080` |
| **Render / Heroku** | `Procfile` + `build.sh` | `web: gunicorn airports_kenya.wsgi --log-file -`; build = pip install → collectstatic → migrate |
| **Gunicorn** | `gunicorn.conf.py` | Bind `0.0.0.0:8000`, 3 sync workers, 1000 connections, timeout 30 s, `max_requests 1000` + jitter, preload_app |
| **GitLab CI** | `.gitlab-ci.yml` | Includes `Auto-DevOps.gitlab-ci.yml`; test job on `python:3.12-slim` with `postgis/postgis:15-3.3` service; runs `check`, `migrate`, `test`; artifacts `htmlcov/` |
| **GitHub Actions** | `.github/workflows/django.yml` | Push/PR to `main`; Ubuntu; Python 3.7/3.8/3.9 matrix (⚠ needs updating to ≥3.10 for Django 5.1) |

## Production Requirements

- **PostGIS database** (remote) — set `DB_*` / `DATABASE_URL` env vars; managed databases (Aiven, Render, Neon) via `DB_SSLMODE`.
- **DEM bucket** — Cloudflare R2 hosting the SRTM 30 m COG; `DEM_URL` must be reachable by the server (rasterio streams it via GDAL `/vsicurl/`).
- **Mapbox tokens** — server token (`sk.`) + public token (`pk.`) for the 3D viewer and geocoding.
- **Static files** — Whitenoise serves `staticfiles/` (collectstatic output committed/served); `STATIC_URL=/static/`, `STATIC_ROOT=staticfiles/`.
- **Env-driven security** — `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS` (note: settings default `ALLOWED_HOSTS=["*"]`; tighten in production).

## Notes

- `.dockerignore` excludes `.git`, `.env`, pyc files, `staticfiles/`, `db.sqlite3`.
- The app runs as `airports_kenya.wsgi:application` (`DJANGO_SETTINGS_MODULE=airports_kenya.settings`).
- Caching falls back to LocMemCache unless Redis `CACHES` is configured.
- `DEM_URL` has no default — DEM-backed features fail loudly without it.
