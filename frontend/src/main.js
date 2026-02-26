// Styles
import './styles/main.css'

// HTMX
import htmx from 'htmx.org'
window.htmx = htmx

// Alpine.js
import Alpine from 'alpinejs'
import collapse from '@alpinejs/collapse'
Alpine.plugin(collapse)
window.Alpine = Alpine

// GridStack
import { GridStack } from 'gridstack'
import 'gridstack/dist/gridstack.min.css'

// Chat module
import { registerChat } from './chat/index.js'

// Read dashboard_id from DOM
function getDashboardId() {
  return document.querySelector('[data-dashboard-id]')?.dataset.dashboardId || 'default'
}

// Debounced dashboard refresh — avoids rapid destroy/init when agent fires many panel_updates
let _refreshTimer = null
function debouncedDashboardRefresh() {
  clearTimeout(_refreshTimer)
  const did = getDashboardId()
  _refreshTimer = setTimeout(() => {
    htmx.ajax('GET', `/d/${did}/panels`, { target: '#dashboard-panels', swap: 'innerHTML' })
  }, 300)
}
// Expose for sidebar Alpine component
window.debouncedDashboardRefresh = debouncedDashboardRefresh

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
    acceptWidgets: '.drawer-panel-item',  // Accept external items from drawer
    columnOpts: { breakpoints: [{ w: 768, c: 1 }] }
  }, '#dashboard-panels')

  // Save positions after drag/resize
  grid.on('change', (event, items) => {
    savePositions(items)
  })

  // Handle external panel dropped from drawer
  grid.on('dropped', (event, previousNode, newNode) => {
    try {
      const el = newNode?.el
      if (!el) { console.warn('dropped: no newNode.el'); return }
      const panelId = el.getAttribute('data-panel-id')
      if (!panelId) { console.warn('dropped: no data-panel-id on', el); return }
      const x = newNode.x ?? 0, y = newNode.y ?? 0
      // Remove the temporary clone widget GridStack inserted
      grid.removeWidget(el, true, false)
      // Call API to add the real panel at the dropped position, then refresh
      const did = getDashboardId()
      fetch(`/api/panels/${panelId}/add-to-dashboard?dashboard_id=${did}&x=${x}&y=${y}`, { method: 'POST' })
        .then(() => debouncedDashboardRefresh())
        .catch(e => console.error('dropped: API error', e))
    } catch (e) {
      console.error('dropped handler error:', e)
    }
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

  // Set up drawer drag if drawer is already open
  setupDrawerDrag()
}

// Save grid positions to backend
async function savePositions(items) {
  const did = getDashboardId()
  // Use provided items or gather from grid
  const nodes = items || (grid ? grid.getGridItems().map(el => el.gridstackNode).filter(Boolean) : [])
  const updates = nodes.map(n => ({
    id: n.el?.getAttribute('data-panel-id') || n.id || '',
    x: n.x,
    y: n.y,
    w: n.w,
    h: n.h
  })).filter(u => u.id)

  if (updates.length === 0) return

  try {
    await fetch(`/api/panels/positions?dashboard_id=${did}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ panels: updates })
    })
  } catch (e) {
    console.error('Failed to save positions:', e)
  }
}

// Setup external drag from drawer into grid
function setupDrawerDrag() {
  document.querySelectorAll('.drawer-panel-item').forEach(el => {
    const w = parseInt(el.getAttribute('gs-w')) || 3
    const h = parseInt(el.getAttribute('gs-h')) || 2
    // Set gridstackNode so GridStack reads correct size in dropover handler
    el.gridstackNode = { w, h }
  })
  GridStack.setupDragIn('.drawer-panel-item', {
    appendTo: 'body',
    // Custom helper — 'clone' breaks because Alpine's MutationObserver tries to
    // evaluate x-bind/x-text directives on the clone (appended to body, outside
    // x-for scope), causing "p is not defined" and losing data-panel-id.
    helper: (originalEl) => {
      const el = document.createElement('div')
      el.className = 'drawer-panel-item'
      el.setAttribute('data-panel-id', originalEl.getAttribute('data-panel-id') || '')
      el.setAttribute('gs-w', originalEl.getAttribute('gs-w') || '3')
      el.setAttribute('gs-h', originalEl.getAttribute('gs-h') || '2')
      const label = originalEl.querySelector('.truncate')?.textContent || 'Panel'
      el.style.cssText = 'padding:6px 12px; font-size:12px; background:var(--kb-bg-secondary); border:1px solid var(--kb-accent); border-radius:6px; color:var(--kb-text-primary); white-space:nowrap; pointer-events:none;'
      el.textContent = label
      return el
    },
    start() {
      // Drawer/backdrop overlay blocks mouseenter on the grid — disable pointer events during drag
      document.querySelectorAll('[data-drawer-overlay]').forEach(el => {
        el.style.pointerEvents = 'none'
      })
    },
    stop() {
      document.querySelectorAll('[data-drawer-overlay]').forEach(el => {
        el.style.pointerEvents = ''
      })
    }
  })
}
window.setupDrawerDrag = setupDrawerDrag

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
  const tid = e.detail.target.id
  if ((tid === 'dashboard-panels' || tid === 'dashboard-content') && grid) {
    grid.destroy(false)
    grid = null
  }
})

document.body.addEventListener('htmx:afterSwap', (e) => {
  const tid = e.detail.target.id
  if (tid === 'dashboard-panels' || tid === 'dashboard-content') {
    setTimeout(initGrid, 50)
  } else if (e.detail.target.classList?.contains('grid-stack-item') && grid) {
    grid.makeWidget(e.detail.target)
  }
})

// Browser back/forward for dashboard switching
window.addEventListener('popstate', (e) => {
  if (e.state?.dashboardId) {
    const did = e.state.dashboardId
    htmx.ajax('GET', '/d/' + did + '/content', { target: '#dashboard-content', swap: 'innerHTML' })
    // Update Alpine sidebar state if available
    const sidebar = document.querySelector('[x-data="dashboardSidebar"]')
    if (sidebar && sidebar._x_dataStack) {
      sidebar._x_dataStack[0].currentDashboardId = did
    }
  }
})

// Listen for dashboard updates
document.body.addEventListener('dashboardUpdated', () => {
  debouncedDashboardRefresh()
})
