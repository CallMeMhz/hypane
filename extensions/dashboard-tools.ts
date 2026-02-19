/**
 * Dashboard Tools Extension for pi
 * 
 * Provides tools for the AI agent to manage dashboard cards
 * through a structured API instead of direct file manipulation.
 */

import { Type } from "@sinclair/typebox";
import { StringEnum } from "@mariozechner/pi-ai";

const DASHBOARD_API = process.env.DASHBOARD_API || "http://localhost:8000";

export default function (pi: any) {
  
  // Tool: List all cards
  pi.registerTool({
    name: "dashboard_list_cards",
    label: "List Dashboard Cards",
    description: "List all cards currently on the dashboard. Returns card IDs, types, titles, and summaries.",
    parameters: Type.Object({}),

    async execute() {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards`);
        if (!response.ok) {
          return { content: [{ type: "text", text: `Error: ${response.status} ${response.statusText}` }] };
        }
        const cards = await response.json();
        
        const summary = cards.map((card: any) => 
          `- [${card.id}] ${card.type}: ${card.title}`
        ).join("\n");
        
        return {
          content: [{ type: "text", text: summary || "No cards on dashboard" }],
          details: { cards },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Get card details
  pi.registerTool({
    name: "dashboard_get_card",
    label: "Get Card Details",
    description: "Get full details of a specific card by ID.",
    parameters: Type.Object({
      cardId: Type.String({ description: "The card ID to retrieve" }),
    }),

    async execute(_toolCallId: string, params: { cardId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/${params.cardId}`);
        if (!response.ok) {
          return { content: [{ type: "text", text: `Error: Card not found (${response.status})` }] };
        }
        const card = await response.json();
        
        return {
          content: [{ type: "text", text: JSON.stringify(card, null, 2) }],
          details: { card },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Create a new card
  pi.registerTool({
    name: "dashboard_create_card",
    label: "Create Dashboard Card",
    description: `Create a new card on the dashboard.
You can use any type name. Common types include: weather, todo, news-bundle, crypto, crypto-bundle, reminder.
You can also create new types - the frontend will render unknown types as JSON.
Content structure is flexible and depends on the type.`,
    parameters: Type.Object({
      type: Type.String({ description: "Card type (e.g. weather, todo, crypto, or any custom type)" }),
      title: Type.String({ description: "Card title" }),
      content: Type.Any({ description: "Card content (structure is flexible)" }),
      size: Type.Optional(Type.String({ description: "Card size: small, medium, or large" })),
    }),

    async execute(_toolCallId: string, params: { type: string; title: string; content: any; size?: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            type: params.type,
            title: params.title,
            content: params.content,
            size: params.size || "medium",
          }),
        });
        
        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error creating card: ${error}` }] };
        }
        
        const card = await response.json();
        return {
          content: [{ type: "text", text: `Created card: ${card.id} (${card.type}: ${card.title})` }],
          details: { card },
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Update a card
  pi.registerTool({
    name: "dashboard_update_card",
    label: "Update Dashboard Card",
    description: "Update an existing card's title, content, size, or type. Only provide fields you want to change.",
    parameters: Type.Object({
      cardId: Type.String({ description: "The card ID to update" }),
      title: Type.Optional(Type.String({ description: "New title" })),
      content: Type.Optional(Type.Any({ description: "New content (partial update supported)" })),
      size: Type.Optional(Type.String({ description: "Card size: small, medium, or large" })),
      type: Type.Optional(Type.String({ description: "Change card type" })),
    }),

    async execute(_toolCallId: string, params: { cardId: string; title?: string; content?: any; size?: string; type?: string }) {
      try {
        const updateData: any = {};
        if (params.title) updateData.title = params.title;
        if (params.content) updateData.content = params.content;
        if (params.size) updateData.size = params.size;
        if (params.type) updateData.type = params.type;

        const response = await fetch(`${DASHBOARD_API}/api/cards/${params.cardId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updateData),
        });
        
        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error updating card: ${error}` }] };
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

  // Tool: Delete a card
  pi.registerTool({
    name: "dashboard_delete_card",
    label: "Delete Dashboard Card",
    description: "Remove a card from the dashboard.",
    parameters: Type.Object({
      cardId: Type.String({ description: "The card ID to delete" }),
    }),

    async execute(_toolCallId: string, params: { cardId: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/${params.cardId}`, {
          method: "DELETE",
        });
        
        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error deleting card: ${error}` }] };
        }
        
        return {
          content: [{ type: "text", text: `Deleted card: ${params.cardId}` }],
        };
      } catch (error) {
        return { content: [{ type: "text", text: `Error: ${error}` }] };
      }
    },
  });

  // Tool: Merge cards
  pi.registerTool({
    name: "dashboard_merge_cards",
    label: "Merge Dashboard Cards",
    description: "Merge multiple cards of the same type into a single bundled card. Works for: crypto → crypto-bundle, news-single → news-bundle.",
    parameters: Type.Object({
      cardIds: Type.Array(Type.String(), { description: "Array of card IDs to merge" }),
      newTitle: Type.String({ description: "Title for the merged card" }),
    }),

    async execute(_toolCallId: string, params: { cardIds: string[]; newTitle: string }) {
      try {
        const response = await fetch(`${DASHBOARD_API}/api/cards/merge`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            cardIds: params.cardIds,
            title: params.newTitle,
          }),
        });
        
        if (!response.ok) {
          const error = await response.text();
          return { content: [{ type: "text", text: `Error merging cards: ${error}` }] };
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

  console.error("[Dashboard Extension] Registered 6 tools: dashboard_list_cards, dashboard_get_card, dashboard_create_card, dashboard_update_card, dashboard_delete_card, dashboard_merge_cards");
}
