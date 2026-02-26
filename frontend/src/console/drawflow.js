import 'drawflow/dist/drawflow.min.css'
import Drawflow from 'drawflow'

const { panels, storages, tasks } = window.__CONSOLE_DATA__

// ── Drawflow init ──────────────────────────────────────────
const container = document.getElementById('drawflow')
const editor = new Drawflow(container)
editor.reroute = false
editor.zoom_min = 0.15
editor.zoom_max = 2.5
editor.curvature = 0.5
editor.start()

// Scroll-wheel zoom (no Ctrl required)
container.addEventListener('wheel', (e) => {
  e.preventDefault()
  if (e.deltaY < 0) editor.zoom_in()
  else editor.zoom_out()
}, { passive: false })

// Override path generation for vertical (top→bottom) flow
editor.createCurvature = (sx, sy, ex, ey, curvature) => {
  const dy = Math.abs(ey - sy)
  const hy1 = sy + dy * curvature
  const hy2 = ey - dy * curvature
  return ` M ${sx} ${sy} C ${sx} ${hy1} ${ex} ${hy2} ${ex} ${ey}`
}

// ── Node ID maps ───────────────────────────────────────────
const nodeIdToResource = {}
const resourceToNodeId = {}

// ── Layout: group related resources into vertical columns ──
// Row Y positions (horizontal layers)
const ROW_Y = { panel: 40, storage: 200, task: 360 }
const COL_GAP = 60
const SUB_GAP = 240
const COL_START = 40

// Build columns: each storage anchors a column; panels above, tasks below
const placedPanels = new Set()
const placedTasks = new Set()
const columns = []

storages.forEach(s => {
  const connPanels = panels.filter(p =>
    !placedPanels.has(p.id) && (p.storage_ids || []).includes(s.id)
  )
  const connTasks = tasks.filter(t =>
    !placedTasks.has(t.id) && (t.storage_ids || []).includes(s.id)
  )
  connPanels.forEach(p => placedPanels.add(p.id))
  connTasks.forEach(t => placedTasks.add(t.id))
  columns.push({ storage: s, panels: connPanels, tasks: connTasks })
})

// Orphan panels / tasks (not connected to any storage)
const orphanPanels = panels.filter(p => !placedPanels.has(p.id))
const orphanTasks = tasks.filter(t => !placedTasks.has(t.id))
if (orphanPanels.length || orphanTasks.length) {
  columns.push({ storage: null, panels: orphanPanels, tasks: orphanTasks })
}

// ── Helpers ────────────────────────────────────────────────
function truncate(str, len = 40) {
  if (typeof str !== 'string') str = JSON.stringify(str) ?? ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

function panelNodeHtml(p) {
  return `
    <div class="console-node console-node--panel">
      <div class="console-node__header" style="border-left: 3px solid var(--kb-blue);">
        <span class="console-node__title">${p.icon ? p.icon + ' ' : ''}${p.title}</span>
      </div>
      <div class="console-node__meta">${p.size} &middot; ${(p.storage_ids || []).length} storages</div>
    </div>`
}

function storageNodeHtml(s) {
  const preview = truncate(JSON.stringify(s.data))
  return `
    <div class="console-node console-node--storage">
      <div class="console-node__header" style="border-left: 3px solid var(--kb-yellow);">
        <span class="console-node__title">${s.id}</span>
      </div>
      <div class="console-node__meta">${preview}</div>
    </div>`
}

function taskNodeHtml(t) {
  const status = t.enabled ? 'enabled' : 'disabled'
  return `
    <div class="console-node console-node--task">
      <div class="console-node__header" style="border-left: 3px solid var(--kb-green);">
        <span class="console-node__title">${t.name}</span>
      </div>
      <div class="console-node__meta">${t.schedule || 'no schedule'} &middot; ${status}</div>
    </div>`
}

function addNodeTracked(name, inputs, outputs, x, y, cls, html, type, id) {
  const nid = editor.addNode(name, inputs, outputs, x, y, cls, {}, html)
  nodeIdToResource[nid] = { type, id }
  resourceToNodeId[`${type}:${id}`] = nid
}

// ── Place nodes per column ─────────────────────────────────
let curX = COL_START

columns.forEach(col => {
  const maxWidth = Math.max(col.panels.length, col.tasks.length, 1)
  const colCenterX = curX + ((maxWidth - 1) * SUB_GAP) / 2

  // Panels (top row)
  col.panels.forEach((p, i) => {
    const x = colCenterX + (i - (col.panels.length - 1) / 2) * SUB_GAP
    addNodeTracked(`panel_${p.id}`, 0, 1, x, ROW_Y.panel, 'console-panel', panelNodeHtml(p), 'panel', p.id)
  })

  // Storage (middle row, centered)
  if (col.storage) {
    addNodeTracked(`storage_${col.storage.id}`, 2, 0, colCenterX, ROW_Y.storage, 'console-storage', storageNodeHtml(col.storage), 'storage', col.storage.id)
  }

  // Tasks (bottom row)
  col.tasks.forEach((t, i) => {
    const x = colCenterX + (i - (col.tasks.length - 1) / 2) * SUB_GAP
    addNodeTracked(`task_${t.id}`, 0, 1, x, ROW_Y.task, 'console-task', taskNodeHtml(t), 'task', t.id)
  })

  curX += maxWidth * SUB_GAP + COL_GAP
})

// ── Draw existing connections ──────────────────────────────
let _suppressEvents = true

function drawConnections() {
  // Panels → storage input_1 (top port)
  panels.forEach(p => {
    const from = resourceToNodeId[`panel:${p.id}`]
    ;(p.storage_ids || []).forEach(sid => {
      const to = resourceToNodeId[`storage:${sid}`]
      if (from && to) editor.addConnection(from, to, 'output_1', 'input_1')
    })
  })
  // Tasks → storage input_2 (bottom port)
  tasks.forEach(t => {
    const from = resourceToNodeId[`task:${t.id}`]
    ;(t.storage_ids || []).forEach(sid => {
      const to = resourceToNodeId[`storage:${sid}`]
      if (from && to) editor.addConnection(from, to, 'output_1', 'input_2')
    })
  })
}

// ── Connection events → API persistence ────────────────────
editor.on('connectionCreated', async ({ output_id, input_id, output_class, input_class }) => {
  if (_suppressEvents) return
  const source = nodeIdToResource[output_id]
  const target = nodeIdToResource[input_id]
  if (!source || !target || target.type !== 'storage') return

  const storageId = target.id
  const endpoint = source.type === 'panel'
    ? `/api/panels/${source.id}`
    : `/api/tasks/${source.id}`

  try {
    const res = await fetch(endpoint)
    const data = await res.json()
    const ids = data.storage_ids || []
    if (!ids.includes(storageId)) {
      ids.push(storageId)
      await fetch(endpoint, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ storage_ids: ids })
      })
    }
  } catch (e) {
    console.error('Failed to add connection:', e)
  }
})

editor.on('connectionRemoved', async ({ output_id, input_id, output_class, input_class }) => {
  if (_suppressEvents) return
  const source = nodeIdToResource[output_id]
  const target = nodeIdToResource[input_id]
  if (!source || !target || target.type !== 'storage') return

  const storageId = target.id
  const endpoint = source.type === 'panel'
    ? `/api/panels/${source.id}`
    : `/api/tasks/${source.id}`

  try {
    const res = await fetch(endpoint)
    const data = await res.json()
    const ids = (data.storage_ids || []).filter(id => id !== storageId)
    await fetch(endpoint, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ storage_ids: ids })
    })
  } catch (e) {
    console.error('Failed to remove connection:', e)
  }
})

// Draw initial connections then enable events
drawConnections()
_suppressEvents = false
