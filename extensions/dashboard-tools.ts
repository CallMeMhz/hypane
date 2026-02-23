/**
 * Dashboard Tools Extension
 * 
 * 只提供 Dashboard 卡片管理的核心工具。
 * 数据采集、信源管理等通过 Skill + 文件操作完成。
 * 
 * Grid System:
 * - 80px grid units
 * - Size format: "WxH" (e.g., "3x2" = 3 cols × 2 rows = 240px × 160px)
 * - Position format: {x, y} grid coordinates (0-indexed)
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";

const DASHBOARD_API = process.env.DASHBOARD_API || "http://localhost:8000";

export default function (pi: ExtensionAPI) {
  // Tool: List cards
  pi.registerTool({
    name: "dashboard_list_cards",
    label: "List Dashboard Cards",
    description: "List all cards on the dashboard with their IDs, types, sizes and positions.",
    parameters: Type.Object({}),

    async execute() {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards`);
        const cards = await response.json();

        if (cards.length === 0) {
          return { content: [{ type: "text", text: "No cards on dashboard." }] };
        }

        const summary = cards
          .map((c: any) => {
            const pos = c.position || {};
            const posStr = pos.x !== undefined ? `@(${pos.x},${pos.y})` : '';
            return `- [${c.id}] ${c.type} ${c.size || '3x2'} ${posStr}: ${c.title || "(no title)"}`;
          })
          .join("\n");

        return {
          content: [{ type: "text", text: `Dashboard cards:\n${summary}` }],
          details: { cards },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Get card
  pi.registerTool({
    name: "dashboard_get_card",
    label: "Get Card Details",
    description: "Get full details of a specific card.",
    parameters: Type.Object({
      cardId: Type.String({ description: "Card ID" }),
    }),

    async execute(_toolCallId: string, params: { cardId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/${params.cardId}`);
        if (!response.ok) {
          return { content: [{ type: "text", text: `Card not found: ${params.cardId}` }] };
        }
        const card = await response.json();
        return {
          content: [{ type: "text", text: `Card ${params.cardId}:\n${JSON.stringify(card, null, 2)}` }],
          details: { card },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Create card
  pi.registerTool({
    name: "dashboard_create_card",
    label: "Create Dashboard Card",
    description: `Create a new card on the dashboard.

All cards are custom - use content.html to render HTML content (Tailwind CSS + Alpine.js supported).
See skills/card_examples.md for common card patterns (weather, todo, countdown, games, etc).

Size format: "WxH" where W=columns(1-12), H=rows(1-8). Each unit is 70px.
Examples: "3x2", "4x3", "6x2" (wide), "3x4" (tall)

Use content.minSize to set minimum resize limit, e.g. "3x2". Default is "2x2".

Position format: {x, y} grid coordinates. {x:0, y:0} is top-left.`,
    parameters: Type.Object({
      type: Type.String({ description: "Card type identifier (e.g. weather, todo, game)" }),
      title: Type.String({ description: "Card title" }),
      content: Type.Object({
        html: Type.String({ description: "HTML content (Tailwind CSS + Alpine.js)" }),
        minSize: Type.Optional(Type.String({ description: 'Minimum size "WxH", e.g. "3x2"' })),
      }),
      size: Type.Optional(Type.String({ description: 'Grid size "WxH", e.g. "3x2", "4x3"' })),
      position: Type.Optional(Type.Object({
        x: Type.Number({ description: "Column position (0-indexed)" }),
        y: Type.Number({ description: "Row position (0-indexed)" }),
      })),
    }),

    async execute(_toolCallId: string, params: any) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
        });
        const card = await response.json();
        return {
          content: [{ type: "text", text: `Created card: ${card.id} (${card.type}) size=${card.size}` }],
          details: { card },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Update card
  pi.registerTool({
    name: "dashboard_update_card",
    label: "Update Dashboard Card",
    description: `Update a card's properties.

Size: "WxH" format (e.g., "3x2", "6x3")
Position: {x, y} grid coordinates to move the card`,
    parameters: Type.Object({
      cardId: Type.String({ description: "Card ID to update" }),
      updates: Type.Object({
        title: Type.Optional(Type.String({ description: "New title" })),
        content: Type.Optional(Type.Any({ description: "New content" })),
        size: Type.Optional(Type.String({ description: 'Grid size "WxH"' })),
        position: Type.Optional(Type.Object({
          x: Type.Number({ description: "Column position" }),
          y: Type.Number({ description: "Row position" }),
        })),
        type: Type.Optional(Type.String({ description: "Card type" })),
      }),
    }),

    async execute(_toolCallId: string, params: { cardId: string; updates: any }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/${params.cardId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params.updates),
        });

        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error: ${error}` }] };
        }

        const card = await response.json();
        return {
          content: [{ type: "text", text: `Updated card: ${card.id}` }],
          details: { card },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Delete card
  pi.registerTool({
    name: "dashboard_delete_card",
    label: "Delete Dashboard Card",
    description: "Delete a card from the dashboard.",
    parameters: Type.Object({
      cardId: Type.String({ description: "Card ID to delete" }),
    }),

    async execute(_toolCallId: string, params: { cardId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/${params.cardId}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error: ${error}` }] };
        }

        return { content: [{ type: "text", text: `Deleted card: ${params.cardId}` }] };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Merge cards
  pi.registerTool({
    name: "dashboard_merge_cards",
    label: "Merge Cards into Bundle",
    description: "Merge multiple similar cards into a bundle card.",
    parameters: Type.Object({
      cardIds: Type.Array(Type.String(), { description: "Card IDs to merge" }),
      bundleType: Type.String({ description: "Bundle type (news-bundle, crypto-bundle, etc)" }),
      title: Type.String({ description: "Bundle title" }),
    }),

    async execute(_toolCallId: string, params: { cardIds: string[]; bundleType: string; title: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/merge`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
        });

        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error: ${error}` }] };
        }

        const card = await response.json();
        return {
          content: [{ type: "text", text: `Merged ${params.cardIds.length} cards into: ${card.id}` }],
          details: { card },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: View changelog
  pi.registerTool({
    name: "dashboard_changelog",
    label: "View Dashboard Changelog",
    description: "View recent changes to the dashboard.",
    parameters: Type.Object({
      limit: Type.Optional(Type.Number({ description: "Max entries (default 20)" })),
    }),

    async execute(_toolCallId: string, params: { limit?: number }) {
      try {
        const limit = params.limit || 20;
        const response = await fetch(`${DASHBOARD_API}/api/cards/changelog?limit=${limit}`);
        const changelog = await response.json();

        if (changelog.length === 0) {
          return { content: [{ type: "text", text: "No changes recorded." }] };
        }

        const summary = changelog
          .map((e: any) => `${e.timestamp.slice(11, 19)} ${e.action}: ${e.cardId} (${e.cardType})`)
          .join("\n");

        return {
          content: [{ type: "text", text: `Recent changes:\n${summary}` }],
          details: { changelog },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: View snapshot
  pi.registerTool({
    name: "dashboard_snapshot",
    label: "View Dashboard Snapshot",
    description: "View a past snapshot of the dashboard.",
    parameters: Type.Object({
      snapshotId: Type.String({ description: "Snapshot ID (from changelog)" }),
    }),

    async execute(_toolCallId: string, params: { snapshotId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/snapshot/${params.snapshotId}`);

        if (!response.ok) {
          return { content: [{ type: "text", text: `Snapshot not found: ${params.snapshotId}` }] };
        }

        const snapshot = await response.json();
        const cards = snapshot.cards || [];
        const summary = cards
          .map((c: any) => `- [${c.id}] ${c.type}: ${c.title || "(no title)"}`)
          .join("\n");

        return {
          content: [{ type: "text", text: `Snapshot ${params.snapshotId} (${cards.length} cards):\n${summary}` }],
          details: { snapshot },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  console.error("[Dashboard Extension] Registered 8 tools");
}
