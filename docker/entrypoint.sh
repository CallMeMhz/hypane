#!/bin/bash
set -e

# =============================================================================
# Pi Agent Configuration
# =============================================================================

PI_HOME="${PI_HOME:-/root/.pi/agent}"
PI_SETTINGS="${PI_HOME}/settings.json"

mkdir -p "$PI_HOME"

# Generate pi settings.json if provided
echo "🔧 Configuring Pi Agent..."

SETTINGS="{}"

if [ -n "$PI_PROVIDER" ]; then
    SETTINGS=$(echo "$SETTINGS" | jq --arg p "$PI_PROVIDER" '. + {defaultProvider: $p}')
    echo "   Provider: $PI_PROVIDER"
fi

if [ -n "$PI_MODEL" ]; then
    SETTINGS=$(echo "$SETTINGS" | jq --arg m "$PI_MODEL" '. + {defaultModel: $m}')
    echo "   Model: $PI_MODEL"
fi

# Save settings if any were configured
if [ "$SETTINGS" != "{}" ]; then
    echo "$SETTINGS" > "$PI_SETTINGS"
    echo "✅ Pi settings saved"
fi

# API Keys are passed as environment variables directly
# Pi reads these automatically:
#   ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, etc.
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "   Anthropic API Key: ****${ANTHROPIC_API_KEY: -4}"
fi
if [ -n "$OPENAI_API_KEY" ]; then
    echo "   OpenAI API Key: ****${OPENAI_API_KEY: -4}"
fi
if [ -n "$GEMINI_API_KEY" ]; then
    echo "   Gemini API Key: ****${GEMINI_API_KEY: -4}"
fi
if [ -n "$OPENROUTER_API_KEY" ]; then
    echo "   OpenRouter API Key: ****${OPENROUTER_API_KEY: -4}"
fi

# =============================================================================
# Custom Provider Extension (for proxy/custom endpoints)
# =============================================================================

# If custom base URL is provided, create a provider extension
if [ -n "$PI_CUSTOM_BASE_URL" ]; then
    echo "🔌 Creating custom provider extension..."
    
    PROVIDER_NAME="${PI_CUSTOM_PROVIDER:-custom}"
    EXT_DIR="/app/.pi/extensions"
    mkdir -p "$EXT_DIR"
    
    cat > "$EXT_DIR/custom-provider.ts" << EOF
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function(pi: ExtensionAPI) {
  pi.registerProvider("${PROVIDER_NAME}", {
    baseUrl: "${PI_CUSTOM_BASE_URL}",
    apiKey: "${PI_CUSTOM_API_KEY_ENV:-CUSTOM_API_KEY}",
    api: "${PI_CUSTOM_API:-openai-completions}",
    models: [
      {
        id: "${PI_MODEL:-gpt-4o}",
        name: "${PI_MODEL:-gpt-4o}",
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 128000,
        maxTokens: 4096
      }
    ]
  });
}
EOF
    
    echo "   Custom provider: $PROVIDER_NAME"
    echo "   Base URL: $PI_CUSTOM_BASE_URL"
fi

# Alternative: Copy mounted extension files
if [ -d "/config/extensions" ]; then
    echo "📄 Copying mounted extensions..."
    cp -r /config/extensions/* /app/.pi/extensions/ 2>/dev/null || true
fi

# =============================================================================
# Data Directory Setup
# =============================================================================

DATA_DIR="${DATA_DIR:-/app/data}"

echo "📁 Ensuring data directories exist..."
mkdir -p "$DATA_DIR/panels"
mkdir -p "$DATA_DIR/sessions"
mkdir -p "$DATA_DIR/snapshots"
mkdir -p "$DATA_DIR/history"
mkdir -p "$DATA_DIR/task_logs"
mkdir -p "$DATA_DIR/sources"

# Initialize default files if they don't exist
if [ ! -f "$DATA_DIR/dashboard.json" ]; then
    echo '{"panels": []}' > "$DATA_DIR/dashboard.json"
    echo "   Created default dashboard.json"
fi

if [ ! -f "$DATA_DIR/tasks.json" ]; then
    echo '{"tasks": []}' > "$DATA_DIR/tasks.json"
    echo "   Created default tasks.json"
fi

# =============================================================================
# Environment Info
# =============================================================================

echo ""
echo "🚀 AI Dashboard Starting..."
echo "   Host: ${HOST:-0.0.0.0}"
echo "   Port: ${PORT:-8000}"
echo "   Data: $DATA_DIR"
echo ""

# =============================================================================
# Start Application
# =============================================================================

exec "$@"
