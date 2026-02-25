// Styles
import './styles/main.css'

// HTMX
import htmx from 'htmx.org'
window.htmx = htmx

// Alpine.js
import Alpine from 'alpinejs'
window.Alpine = Alpine

// GridStack
import { GridStack } from 'gridstack'
import 'gridstack/dist/gridstack.min.css'

// Chat module
import { registerChat } from './chat/index.js'

// Debounced dashboard refresh — avoids rapid destroy/init when agent fires many panel_updates
let _refreshTimer = null
function debouncedDashboardRefresh() {
  clearTimeout(_refreshTimer)
  _refreshTimer = setTimeout(() => {
    htmx.ajax('GET', '/dashboard-panels', { target: '#dashboard-panels', swap: 'innerHTML' })
  }, 300)
}

registerChat(Alpine, {
  onToolEnd(tool, args) {
    if (['panel_create', 'panel_delete', 'panel_update', 'market_install'].includes(tool)) {
      debouncedDashboardRefresh()
    } else if (tool === 'storage_update' && args.storageId) {
      fetch('/api/panels').then(r => r.json()).then(panels => {
        panels.filter(p => p.storage_ids?.includes(args.storageId))
          .forEach(p => {
            const el = document.querySelector(`[data-panel-id="${p.id}"] .card-content`)
            if (el) htmx.ajax('GET', `/panels/${p.id}/content`, { target: el, swap: 'innerHTML' })
          })
      })
    }
  }
})

Alpine.start()

// ============================================
// GridStack Dashboard Grid
// ============================================

let grid = null

function initGrid() {
  if (grid || !document.getElementById('dashboard-panels')) return

  grid = GridStack.init({
    column: 12,
    cellHeight: 70,
    margin: 8,
    float: true,              // Free placement (matches current non-compact default)
    animate: true,
    handle: '.card-drag-handle',
    resizable: { handles: 'se' },
    columnOpts: { breakpoints: [{ w: 768, c: 1 }] }
  }, '#dashboard-panels')

  // Save positions after drag/resize
  grid.on('change', (event, items) => {
    savePositions(items)
  })

  // Lock widgets above the resizing one so SE resize won't push them
  grid.on('resizestart', (event, el) => {
    const node = el.gridstackNode
    if (!node) return
    grid.getGridItems().forEach(item => {
      const n = item.gridstackNode
      if (item !== el && n && n.y + n.h <= node.y) {
        grid.update(item, { locked: true })
      }
    })
  })

  // Unlock all widgets after resize ends
  grid.on('resizestop', (event, el) => {
    grid.getGridItems().forEach(item => {
      grid.update(item, { locked: false })
    })

    const node = el.gridstackNode
    if (!node) return
    const panelId = el.getAttribute('data-panel-id')
    if (!panelId) return
    const newSize = `${node.w}x${node.h}`
    fetch(`/api/panels/${panelId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ size: newSize })
    }).catch(e => console.error('Failed to save size:', e))
  })
}

// Save grid positions to backend
async function savePositions(items) {
  // Use provided items or gather from grid
  const nodes = items || (grid ? grid.getGridItems().map(el => el.gridstackNode).filter(Boolean) : [])
  const updates = nodes.map(n => ({
    id: n.el?.getAttribute('data-panel-id') || n.id || '',
    x: n.x,
    y: n.y
  })).filter(u => u.id)

  if (updates.length === 0) return

  try {
    await fetch('/api/panels/positions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ panels: updates })
    })
  } catch (e) {
    console.error('Failed to save positions:', e)
  }
}

// Expose compact / autoCompact globally
window.compactAll = () => {
  if (grid) {
    grid.compact()
    savePositions()
  }
}
window.setAutoCompact = (v) => {
  if (grid) grid.float(!v)
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  initGrid()
})

// HTMX integration: destroy/reinit grid on dashboard swap
document.body.addEventListener('htmx:beforeSwap', (e) => {
  if (e.detail.target.id === 'dashboard-panels' && grid) {
    grid.destroy(false)
    grid = null
  }
})

document.body.addEventListener('htmx:afterSwap', (e) => {
  if (e.detail.target.id === 'dashboard-panels') {
    setTimeout(initGrid, 50)
  } else if (e.detail.target.classList?.contains('grid-stack-item') && grid) {
    grid.makeWidget(e.detail.target)
  }
})

// Listen for dashboard updates
document.body.addEventListener('dashboardUpdated', () => {
  htmx.ajax('GET', '/dashboard-panels', { target: '#dashboard-panels', swap: 'innerHTML' })
})
