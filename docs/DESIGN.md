# Design System

## Philosophy

**Monochrome, minimal, restrained.**

No gradients, no colorful accents, no "AI purple". Just shades of gray with careful attention to hierarchy and spacing.

## Color Palette

We use a single gray scale. Default is dark mode.

| Token | Hex | Usage |
|-------|-----|-------|
| `gray-900` | `#111827` | Background |
| `gray-800` | `#1f2937` | Cards, elevated surfaces, borders |
| `gray-700` | `#374151` | Hover states, active borders |
| `gray-600` | `#4b5563` | Secondary text, muted elements |
| `gray-500` | `#6b7280` | Tertiary text, timestamps |
| `gray-400` | `#9ca3af` | Subtle accents |
| `gray-300` | `#d1d5db` | Primary text (assistant messages) |
| `gray-200` | `#e5e7eb` | Primary text (headings, user input) |
| `gray-100` | `#f3f4f6` | Emphasized text |

## Typography

- **Headings**: `text-gray-100` or `text-gray-200`, `font-medium`
- **Body**: `text-gray-300` or `text-gray-400`, `text-sm`
- **Muted**: `text-gray-500` or `text-gray-600`, `text-xs`
- **Font weight**: Prefer `font-medium` over `font-bold`
- **Tracking**: Use `tracking-tight` for headings

## Components

### Cards

```html
<div class="bg-gray-800/50 border border-gray-800 rounded-lg p-4 hover:border-gray-700">
  <h3 class="text-sm font-medium text-gray-200">Title</h3>
  <p class="text-sm text-gray-400">Content</p>
</div>
```

### Buttons

```html
<!-- Primary -->
<button class="px-3 py-2 rounded-lg text-sm bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 hover:text-white">
  Action
</button>

<!-- Ghost -->
<button class="p-2 rounded-lg border border-gray-800 hover:border-gray-700 hover:bg-gray-800/50 text-gray-400">
  <svg>...</svg>
</button>
```

### Input

```html
<div contenteditable class="px-3 py-2 border border-gray-800 rounded-lg bg-gray-900 text-gray-200 text-sm focus:outline-none focus:border-gray-700">
</div>
```

### Badges / Tags

```html
<span class="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded border border-gray-700">
  Tag
</span>
```

### Status Indicators

```html
<!-- Running -->
<span class="w-1 h-1 bg-gray-500 rounded-full animate-pulse"></span>

<!-- Done -->
<span class="text-gray-600">·</span>

<!-- Error (exception - subtle red) -->
<span class="text-red-400/70">✗</span>
```

## Spacing

- Container padding: `px-6 py-8`
- Section gaps: `mb-10`
- Card padding: `p-4`
- Element gaps: `gap-2` or `gap-3`

## Borders

- Default: `border-gray-800`
- Hover: `border-gray-700`
- Dividers: `border-gray-800`
- Border radius: `rounded-lg` (8px)

## Shadows

Minimal. Use only for floating elements:
- Chat panel: `shadow-2xl`
- Floating button: `shadow-lg`

## Animation

- Transitions: `transition-colors` or `transition-all`
- Duration: default (150ms)
- Hover delay for tools: `delay-500` (magic wand)
- Loading: `animate-pulse` or `animate-bounce`

## Icons

- Stroke width: `1.5` (not 2)
- Size: `w-5 h-5` for buttons, `w-3.5 h-3.5` for inline
- Color: `text-gray-400` default, `text-gray-300` on hover

## Don'ts

- ❌ Colorful gradients (`from-violet-500 to-fuchsia-500`)
- ❌ Bright accent colors (sky-500, emerald-500, etc.)
- ❌ Heavy shadows with color (`shadow-violet-500/25`)
- ❌ Bold fonts everywhere
- ❌ Emojis in UI chrome (OK in user content)
- ❌ Rounded-full on large elements

## Light Mode

Light mode inverts the scale but maintains the monochrome feel:
- Background: `gray-100`
- Cards: `white` with `border-gray-200`
- Text: `gray-800`, `gray-600`, `gray-400`
