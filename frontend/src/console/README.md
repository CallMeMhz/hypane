# Drawflow Console (archived)

## What this was

A visual graph editor for panel/storage/task relationships using [Drawflow](https://github.com/jerosoler/Drawflow). Nodes represented panels (blue), storages (yellow), and tasks (green) in a vertical-flow layout. Connections encoded `storage_ids` bindings.

## Why it was replaced

- Difficult to edit on the canvas — nodes hard to select, connections often misaligned
- Connection wiring was fragile (dragging to wrong port, accidental disconnects)
- Didn't scale well beyond ~10 nodes
- Replaced with a simpler list-based UI at `/console` that shows the same data in a more practical way

## How to restore

1. Move `drawflow.js` back to `frontend/src/console.js`
2. Add entry to `frontend/vite.config.js`:
   ```js
   input: {
     main: resolve(__dirname, 'src/main.js'),
     console: resolve(__dirname, 'src/console.js'),
   }
   ```
3. Re-add drawflow dependency: `pnpm add drawflow`
4. Restore drawflow CSS block in `frontend/src/styles/main.css` (see git history)
5. Update `app/templates/console.html` to load `/static/js/console.js` and `/static/css/console.css`
