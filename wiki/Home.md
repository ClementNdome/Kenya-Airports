# KCAA Obstacle Compliance & Airport GIS System — Wiki

Welcome to the project wiki for the **Kenya Civil Aviation Authority (KCAA) Obstacle Compliance & Airport GIS System**.

A Web GIS application built with **Django + GeoDjango** to regulate **Obstacle Limitation Surfaces (OLS)** around Kenyan aerodromes. Property developers, real estate agents, KCAA regulators, and the public can check whether a building or structure complies with KCAA regulations — and obtain official compliance certificates through an approval workflow.

## Quick Facts

| | |
|---|---|
| **Purpose** | Regulate Obstacle Limitation Surfaces (OLS) around Kenyan aerodromes; issue compliance certificates |
| **Stack** | Python 3.12 · Django 5.1.6 · GeoDjango · PostgreSQL + PostGIS · DRF 3.15 |
| **GIS** | GDAL · Rasterio · pyproj · Leaflet.js · Mapbox GL JS (3D) · django-leaflet |
| **Regulatory basis** | ICAO Annex 14 Vol I (8th ed.) · KCAA AC-AGA005C (June 2024) · KCAA AC-AGA032A (Feb 2026) |
| **Codebase** | 3 packages · 11 models · 45+ views · 36 templates · 12 management commands · 12 migrations |
| **Tests** | 32 tests (SimpleTestCase — no DB required), verified against a hand-computed matrix |
| **Demo** | [kenya-airports.onrender.com](https://kenya-airports.onrender.com/) |
| **Repo** | [github.com/ClementNdome/Kenya-Airports](https://github.com/ClementNdome/Kenya-Airports) |

## Status

The core compliance system is **functional end-to-end**: the full ICAO Annex 14 OLS engine, DEM-driven terrain analysis, 3D map visualisation, certificate workflow, bulk processing, REST API, and analytics are implemented. Several map/visualisation upgrades are recorded as deferred ADRs (see [ADRs](ADRs) and [Roadmap](Roadmap)).

## Wiki Pages

| Page | What you'll find |
|---|---|
| [Home](Home) | This page — overview and index |
| [Getting Started](Getting-Started) | Prerequisites, environment setup, data loading |
| [Architecture](Architecture) | Packages, models, engines, module map |
| [Features](Features) | All feature groups in detail |
| [Timeline](Timeline) | Project history phase-by-phase (from git history + ADRs) |
| [OLS Engine](OLS-Engine) | Annex 14 surface geometry, ceilings, buffers, UTM projection |
| [API Reference](API-Reference) | DRF v1 + GeoJSON + utility endpoints |
| [Data Model](Data-Model) | Models, unmanaged tables, migration history |
| [Management Commands](Management-Commands) | All 12 CLI commands |
| [Testing](Testing) | Test suite, coverage, how to run |
| [ADRs](ADRs) | Architecture Decision Records index + status |
| [Roadmap](Roadmap) | Deferred work and future product directions |
| [Deployment](Deployment) | Docker, Render, CI/CD, production notes |
