# Hypane

AI-powered personal dashboard. Create and manage panels through chat.

## Features

- 🎛️ **Panel System** - Drag & drop, resizable tiles with flow layout
- 🤖 **AI Integration** - Create panels via natural language chat
- ⏰ **Scheduled Tasks** - Cron-based tasks with APScheduler
- 📱 **Responsive** - Dynamic columns, mobile-friendly
- 🎨 **Dark Theme** - Obsidian-inspired Kabadoni theme

## Tech Stack

- **Backend**: Python 3.12+ / FastAPI / Jinja2
- **Frontend**: HTMX 2.x / Alpine.js / Tailwind CSS 4.x
- **Agent**: [Pi](https://github.com/mariozechner/pi-coding-agent) (CLI)
- **Scheduler**: APScheduler

## Quick Start

### Docker (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env, set your API key

# 2. Run
docker compose up -d

# 3. Open http://localhost:8000
```

### Local Development

```bash
# Install dependencies
uv sync

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Run (scheduler starts automatically with the app)
uv run uvicorn app.main:app --reload
```

## Panel Architecture

```
data/panels/{panel-id}/
├── metadata.json  # Title, icon, size, storage_ids
├── facade.html    # Jinja2 template (rendered with storage context)
└── handler.py     # Optional: on_action, on_init

data/tasks/{task-id}/
├── metadata.json  # Schedule (cron), storage_ids, enabled
└── handler.py     # on_schedule(storage)
```

**Facade Example:**
```html
<div x-data="myPanel()" x-init="init()">
  <span x-text="data.value"></span>
</div>
<script>
window.myPanel = () => ({
  data: {},
  async init() {
    const res = await fetch('/api/panels/__PANEL_ID__/data');
    this.data = await res.json();
  }
});
</script>
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `PI_PROVIDER` | Default provider (anthropic/openai/custom) |
| `PI_MODEL` | Default model |

See `.env.example` for custom provider setup.

## License

MIT
