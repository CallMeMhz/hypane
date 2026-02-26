<div align="center">

# Hypane

**AI-powered personal dashboard. Create and manage panels through natural language chat.**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)](https://mongodb.com)
[![HTMX](https://img.shields.io/badge/HTMX-36C?logo=htmx&logoColor=white)](https://htmx.org)
[![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0?logo=alpine.js&logoColor=white)](https://alpinejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS_4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](README.md) | [中文](README_zh.md)

<img src="screenshots/dashboard.jpg" alt="dashboard" width="800">

</div>

## Features

- **Chat-driven** — Describe what you want, the AI agent creates panels with templates, handlers, and data
- **Panel system** — Drag-and-drop tiles on a 12-column grid (GridStack), resizable, per-dashboard layout
- **Multi-dashboard** — Multiple dashboards with a sidebar drawer to organize and reuse panels
- **Scheduled tasks** — Cron-based background jobs that update panel data (APScheduler)
- **Panel market** — Install pre-built panel templates with one click
- **Dark theme** — Obsidian-inspired Kabadoni theme with CSS custom properties

## Panel Examples

| Weather | Poster | Cookie Clicker | VPS CPU Load |
|---------|--------|----------------|--------------|
| ![weather](screenshots/weather.jpg) | ![poster](screenshots/poster.jpg) | ![cookie clicker](screenshots/cookie_clicker.jpg) | ![vps cpu load](screenshots/vps_cpu_load.jpg) |

## Resource Console

Manage all panels, storages, and tasks in one place. Click to filter and inspect relationships.

<img src="screenshots/resource_console.jpg" alt="resource console" width="800">

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Dashboard                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │ Panel A │ │ Panel B │ │ Panel C │  ← position & size    │
│  └────┬────┘ └────┬────┘ └────┬────┘    per dashboard      │
│       │           │           │                             │
└───────┼───────────┼───────────┼─────────────────────────────┘
        │           │           │
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Storage │ │ Storage │ │ Storage │   ← shared JSON data
   │   "s1"  │ │   "s2"  │ │   "s3"  │     containers
   └─────────┘ └────┬────┘ └─────────┘
                     │
                     ▲
                ┌────┴────┐
                │  Task   │   ← cron job writes to
                │ (cron)  │     the same storage
                └─────────┘
```

- **Panel** — Self-contained tile with a Jinja2 template and optional Python handler. Panels reference storages by ID. The same panel can appear on multiple dashboards (shared data, independent layout).
- **Storage** — Shared JSON data container. Multiple panels and tasks can read/write the same storage, enabling real-time data flow.
- **Task** — Cron-scheduled background job (APScheduler). Tasks write to storages, and panels that reference those storages automatically reflect the latest data on render.

> Example: A "Weather" task runs every 30 minutes, fetches forecast data, and writes it to storage `weather-sg`. The "Singapore Weather" panel references the same storage and renders the data as a card. No direct coupling between task and panel — storage is the glue.

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12+ / FastAPI / Jinja2 |
| Database | MongoDB (Motor async driver) |
| Frontend | HTMX / Alpine.js / GridStack / Tailwind CSS 4 |
| Agent | [Pi](https://github.com/mariozechner/pi-coding-agent) coding agent (subprocess) |
| Build | Vite / uv / Docker |

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env
# Edit .env — set your API key (Anthropic, OpenAI, Gemini, or OpenRouter)

docker compose up -d
# Open http://localhost:8000
```

### Local Development

```bash
# Prerequisites: Python 3.12+, Node.js 20+, MongoDB running locally

# Backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend && npm install && npm run build
```

Tailwind CSS is compiled via Vite, not CDN. Rebuild frontend after adding new utility classes.

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Description |
|----------|-------------|
| `PI_PROVIDER` | LLM provider: `anthropic`, `openai`, `gemini`, `openrouter`, or `custom` |
| `PI_MODEL` | Model name (e.g., `claude-sonnet-4-20250514`) |
| `ANTHROPIC_API_KEY` | API key for your chosen provider |
| `MONGO_DSN` | MongoDB connection string (auto-configured in Docker) |

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=CallMeMhz/hypane&type=Date)](https://star-history.com/#CallMeMhz/hypane&Date)

## License

MIT
