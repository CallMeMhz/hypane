/**
 * Dashboard Tools Extension
 * 
 * Panel 管理工具。每个 Panel 是独立目录：
 * - facade.html (外观)
 * - data.json (数据)  
 * - handler.py (后端逻辑，可选)
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";

const DASHBOARD_API = process.env.DASHBOARD_API || "http://localhost:8000";

export default function (pi: ExtensionAPI) {
  // Tool: List panels
  pi.registerTool({
    name: "panel_list",
    label: "List Panels",
    description: "List all panels on the dashboard.",
    parameters: Type.Object({}),

    async execute() {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/panels`);
        const panels = await response.json();

        if (panels.length === 0) {
          return { content: [{ type: "text", text: "No panels on dashboard." }] };
        }

        const summary = panels
          .map((p: any) => {
            const pos = p.position || {};
            const posStr = pos.x !== undefined ? `@(${pos.x},${pos.y})` : '';
            const desc = p.desc ? ` - ${p.desc}` : '';
            return `- [${p.id}] ${p.size || '3x2'} ${posStr}: ${p.title || "(no title)"}${desc}`;
          })
          .join("\n");

        return {
          content: [{ type: "text", text: `Panels:\n${summary}` }],
          details: { panels },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Get panel
  pi.registerTool({
    name: "panel_get",
    label: "Get Panel",
    description: "Get full details of a panel (data + facade).",
    parameters: Type.Object({
      panelId: Type.String({ description: "Panel ID" }),
    }),

    async execute(_toolCallId: string, params: { panelId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/panels/${params.panelId}`);
        if (!response.ok) {
          return { content: [{ type: "text", text: `Panel not found: ${params.panelId}` }] };
        }
        const panel = await response.json();
        return {
          content: [{ type: "text", text: `Panel ${params.panelId}:\n${JSON.stringify(panel, null, 2)}` }],
          details: { panel },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Create panel
  pi.registerTool({
    name: "panel_create",
    label: "Create Panel",
    description: `Create a new panel.

Each panel has:
- facade: HTML content (Tailwind CSS + Alpine.js)
- data: JSON data (includes icon, headerColor, desc, etc.)
- handler: Python code (optional, for action and/or scheduled tasks)

Handler example with scheduled task:
\`\`\`python
from scheduler.decorators import scheduled

@scheduled("*/30 * * * *")  # every 30 min
async def collect(data: dict) -> dict:
    # fetch data, update panel
    return data

async def handle_action(action: str, payload: dict, data: dict) -> dict:
    # handle user interaction
    return data
\`\`\`

Size format: "WxH" (e.g., "3x2", "4x3"). Each unit is 70px.
Use __PANEL_ID__ placeholder in facade - it will be replaced with actual ID.

Colors: gray, red, orange, amber, green, teal, cyan, blue, indigo, purple, pink, rose
Icons: check-square, hourglass, bell, calendar, cloud-sun, coins, newspaper, cookie, star, heart, code, box, etc.

See skills/panel_examples.md for full list and examples.`,
    parameters: Type.Object({
      title: Type.String({ description: "Panel title (no emoji)" }),
      desc: Type.Optional(Type.String({ description: "Natural language description of what this panel does (helps agent understand)" })),
      icon: Type.String({ description: "Icon name (e.g. check-square, bell, newspaper)" }),
      headerColor: Type.String({ description: "Color name (e.g. teal, amber, indigo)" }),
      facade: Type.String({ description: "HTML content (Tailwind CSS + Alpine.js)" }),
      data: Type.Optional(Type.Object({}, { additionalProperties: true })),
      handler: Type.Optional(Type.String({ description: "Python handler code with @scheduled decorator and/or handle_action()" })),
      size: Type.Optional(Type.String({ description: 'Grid size "WxH", default "3x2"' })),
      minSize: Type.Optional(Type.String({ description: 'Minimum size "WxH"' })),
      position: Type.Optional(Type.Object({
        x: Type.Number({ description: "Column (0-indexed)" }),
        y: Type.Number({ description: "Row (0-indexed)" }),
      })),
    }),

    async execute(_toolCallId: string, params: any) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/panels`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
        });
        const panel = await response.json();
        return {
          content: [{ type: "text", text: `Created panel: ${panel.id} (${panel.type}) size=${panel.size}` }],
          details: { panel },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Update panel
  pi.registerTool({
    name: "panel_update",
    label: "Update Panel",
    description: `Update a panel's facade, data, handler, or layout.`,
    parameters: Type.Object({
      panelId: Type.String({ description: "Panel ID" }),
      title: Type.Optional(Type.String({ description: "New title" })),
      facade: Type.Optional(Type.String({ description: "New facade HTML" })),
      data: Type.Optional(Type.Object({}, { additionalProperties: true })),
      handler: Type.Optional(Type.String({ description: "New handler code" })),
      size: Type.Optional(Type.String({ description: 'Grid size "WxH"' })),
      position: Type.Optional(Type.Object({
        x: Type.Number({ description: "Column" }),
        y: Type.Number({ description: "Row" }),
      })),
    }),

    async execute(_toolCallId: string, params: { panelId: string; [key: string]: any }) {
      const { panelId, ...updates } = params;
      try {
        const response = await fetch(`${DASHBOARD_API}/api/panels/${panelId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updates),
        });

        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error: ${error}` }] };
        }

        const panel = await response.json();
        return {
          content: [{ type: "text", text: `Updated panel: ${panel.id}` }],
          details: { panel },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Delete panel
  pi.registerTool({
    name: "panel_delete",
    label: "Delete Panel",
    description: "Delete a panel and all its files.",
    parameters: Type.Object({
      panelId: Type.String({ description: "Panel ID" }),
    }),

    async execute(_toolCallId: string, params: { panelId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/panels/${params.panelId}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error: ${error}` }] };
        }

        return { content: [{ type: "text", text: `Deleted panel: ${params.panelId}` }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Panel action
  pi.registerTool({
    name: "panel_action",
    label: "Panel Action",
    description: "Call a panel's handler with an action.",
    parameters: Type.Object({
      panelId: Type.String({ description: "Panel ID" }),
      action: Type.String({ description: "Action name" }),
      payload: Type.Optional(Type.Object({}, { additionalProperties: true })),
    }),

    async execute(_toolCallId: string, params: { panelId: string; action: string; payload?: any }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/panels/${params.panelId}/action`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: params.action, payload: params.payload }),
        });

        const result = await response.json();
        return {
          content: [{ type: "text", text: `Action ${params.action}: ${JSON.stringify(result)}` }],
          details: { result },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  console.error("[Dashboard Extension] Registered 6 panel tools");
}
