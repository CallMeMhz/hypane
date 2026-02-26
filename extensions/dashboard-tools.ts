/**
 * Dashboard Tools Extension
 * 
 * Panel 管理工具 (v2 架构):
 * - template.html (Jinja2 模板)
 * - handler.py (Python handler with on_action)
 * - storage_ids (绑定的 storage 列表)
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
            const storages = p.storage_ids?.length ? ` [storages: ${p.storage_ids.join(', ')}]` : '';
            return `- [${p.id}] ${p.size || '3x2'} ${posStr}: ${p.title || "(no title)"}${desc}${storages}`;
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
    description: "Get full details of a panel (metadata + template + handler + storage data).",
    parameters: Type.Object({
      panelId: Type.String({ description: "Panel ID" }),
    }),

    async execute(_toolCallId: string, params: { panelId: string }) {
      try {
        const [metaRes, templateRes, handlerRes] = await Promise.all([
          fetch(`${DASHBOARD_API}/api/panels/${params.panelId}`),
          fetch(`${DASHBOARD_API}/api/panels/${params.panelId}/template`),
          fetch(`${DASHBOARD_API}/api/panels/${params.panelId}/handler`),
        ]);
        
        if (!metaRes.ok) {
          return { content: [{ type: "text", text: `Panel not found: ${params.panelId}` }] };
        }
        
        const meta = await metaRes.json();
        const { template } = await templateRes.json();
        const { handler } = await handlerRes.json();
        
        // Also fetch storage data for each storage_id
        const storageData: Record<string, any> = {};
        for (const sid of meta.storage_ids || []) {
          try {
            const storageRes = await fetch(`${DASHBOARD_API}/api/storages/${sid}`);
            if (storageRes.ok) {
              const s = await storageRes.json();
              storageData[sid] = s.data;  // Just the data, not the full storage object
            }
          } catch {}
        }
        
        const panel = { ...meta, template, handler, storageData };
        
        // Format output to highlight storage IDs
        const storageInfo = meta.storage_ids?.length 
          ? `\n\nSTORAGE (use these IDs with storage_update):\n${meta.storage_ids.map((sid: string) => 
              `  - ${sid}: ${JSON.stringify(storageData[sid] || {})}`
            ).join('\n')}`
          : '';
        
        return {
          content: [{ type: "text", text: `Panel ${params.panelId}:${storageInfo}\n\nMETADATA: ${JSON.stringify(meta, null, 2)}\n\nTEMPLATE:\n${template}\n\nHANDLER:\n${handler}` }],
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
    description: `Create a new panel with Jinja2 template and Python handler.

**Architecture:**
- template: Jinja2 HTML, renders with \`panel\` (metadata) and \`storage\` (dict of bound storages)
- handler: Python with \`on_action(action: str, payload: dict, storage: dict)\`
- storage_ids: List of storage IDs this panel can access

**Template example (interactive):**
\`\`\`html
<div class="h-full flex flex-col items-center justify-center">
  <span class="text-6xl cursor-pointer" onclick="panelAction('{{ panel.id }}', 'click', {})">🍪</span>
  <div class="text-2xl font-bold">{{ storage['cookies']['count'] }}</div>
</div>
\`\`\`

**Handler example:**
\`\`\`python
def on_action(action: str, payload: dict, storage: dict) -> None:
    if action == "click":
        cookies = storage.get("cookies", {})
        cookies["count"] = cookies.get("count", 0) + 1
\`\`\`

**panelAction(panelId, action, payload)** - Call this to trigger handler and refresh panel.

Icons: check-square, cookie, cloud, globe, calendar, clock, bell, coins, newspaper, star, heart, code, box
Colors: gray, red, orange, amber, green, teal, cyan, blue, indigo, purple, pink, rose`,
    parameters: Type.Object({
      title: Type.String({ description: "Panel title" }),
      desc: Type.Optional(Type.String({ description: "Description for AI reference" })),
      icon: Type.String({ description: "Lucide icon name" }),
      headerColor: Type.Optional(Type.String({ description: "Header color name" })),
      size: Type.Optional(Type.String({ description: 'Grid size "WxH", default "3x2"' })),
      storage_ids: Type.Optional(Type.Array(Type.String(), { description: "Storage IDs to bind" })),
      template: Type.String({ description: "Jinja2 HTML template" }),
      handler: Type.Optional(Type.String({ description: "Python handler with on_action()" })),
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
          body: JSON.stringify({
            title: params.title,
            desc: params.desc,
            icon: params.icon,
            size: params.size || "3x2",
            storage_ids: params.storage_ids || [],
            template: params.template,
            handler: params.handler || "",
            position: params.position,
          }),
        });
        const panel = await response.json();
        return {
          content: [{ type: "text", text: `Created panel: ${panel.id} (${panel.size})` }],
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
    description: `Update a panel's metadata, template, or handler.`,
    parameters: Type.Object({
      panelId: Type.String({ description: "Panel ID" }),
      title: Type.Optional(Type.String({ description: "New title" })),
      desc: Type.Optional(Type.String({ description: "New description" })),
      icon: Type.Optional(Type.String({ description: "New icon" })),
      size: Type.Optional(Type.String({ description: 'Grid size "WxH"' })),
      storage_ids: Type.Optional(Type.Array(Type.String(), { description: "New storage IDs" })),
      template: Type.Optional(Type.String({ description: "New Jinja2 template" })),
      handler: Type.Optional(Type.String({ description: "New Python handler" })),
      position: Type.Optional(Type.Object({
        x: Type.Number({ description: "Column" }),
        y: Type.Number({ description: "Row" }),
      })),
    }),

    async execute(_toolCallId: string, params: { panelId: string; [key: string]: any }) {
      const { panelId, template, handler, ...updates } = params;
      try {
        // Update metadata
        if (Object.keys(updates).length > 0) {
          await fetch(`${DASHBOARD_API}/api/panels/${panelId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updates),
          });
        }
        
        // Update template
        if (template !== undefined) {
          await fetch(`${DASHBOARD_API}/api/panels/${panelId}/template`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ template }),
          });
        }
        
        // Update handler
        if (handler !== undefined) {
          await fetch(`${DASHBOARD_API}/api/panels/${panelId}/handler`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ handler }),
          });
        }

        return {
          content: [{ type: "text", text: `Updated panel: ${panelId}` }],
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
    description: "Delete a panel (soft delete — moved to trash, recoverable). Cascade: related storages and tasks that are exclusively used by this panel are also soft-deleted.",
    parameters: Type.Object({
      panelId: Type.String({ description: "Panel ID" }),
    }),

    async execute(_toolCallId: string, params: { panelId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/panels/${params.panelId}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          return { content: [{ type: "text", text: `Panel not found: ${params.panelId}` }] };
        }

        return {
          content: [{ type: "text", text: `Deleted panel: ${params.panelId}` }],
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Storage CRUD
  pi.registerTool({
    name: "storage_list",
    label: "List Storages",
    description: "List all storages.",
    parameters: Type.Object({}),

    async execute() {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/storages`);
        const storages = await response.json();

        if (storages.length === 0) {
          return { content: [{ type: "text", text: "No storages." }] };
        }

        const summary = storages
          .map((s: any) => `- [${s.id}]: ${JSON.stringify(s.data).slice(0, 100)}...`)
          .join("\n");

        return {
          content: [{ type: "text", text: `Storages:\n${summary}` }],
          details: { storages },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  pi.registerTool({
    name: "storage_get",
    label: "Get Storage",
    description: "Get storage data by ID.",
    parameters: Type.Object({
      storageId: Type.String({ description: "Storage ID" }),
    }),

    async execute(_toolCallId: string, params: { storageId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/storages/${params.storageId}`);
        if (!response.ok) {
          return { content: [{ type: "text", text: `Storage not found: ${params.storageId}` }] };
        }
        const storage = await response.json();
        return {
          content: [{ type: "text", text: `Storage ${params.storageId}:\n${JSON.stringify(storage, null, 2)}` }],
          details: { storage },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  pi.registerTool({
    name: "storage_create",
    label: "Create Storage",
    description: "Create a new storage with initial data.",
    parameters: Type.Object({
      storageId: Type.String({ description: "Storage ID (use lowercase-hyphen format)" }),
      data: Type.Optional(Type.Object({}, { additionalProperties: true, description: "Initial data" })),
    }),

    async execute(_toolCallId: string, params: { storageId: string; data?: object }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/storages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: params.storageId, data: params.data || {} }),
        });
        const storage = await response.json();
        return {
          content: [{ type: "text", text: `Created storage: ${storage.id}` }],
          details: { storage },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  pi.registerTool({
    name: "storage_update",
    label: "Update Storage",
    description: "Update storage data (shallow merge). Use panel_get to find the exact storage_ids for a panel.",
    parameters: Type.Object({
      storageId: Type.String({ description: "Storage ID (get from panel's storage_ids array)" }),
      data: Type.Object({}, { additionalProperties: true, description: "Data to merge" }),
    }),

    async execute(_toolCallId: string, params: { storageId: string; data: object }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/storages/${params.storageId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ data: params.data }),
        });
        if (!response.ok) {
          return { content: [{ type: "text", text: `Storage not found: ${params.storageId}` }] };
        }
        const storage = await response.json();
        return {
          content: [{ type: "text", text: `Updated storage: ${storage.id}` }],
          details: { storage },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });
}
