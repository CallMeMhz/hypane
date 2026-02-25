// Styles
import './styles/main.css'

// HTMX
import htmx from 'htmx.org'
window.htmx = htmx

// Markdown
import { marked } from 'marked'

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,  // Convert \n to <br>
  gfm: true,     // GitHub Flavored Markdown
})

// Alpine.js
import Alpine from 'alpinejs'
window.Alpine = Alpine

// Render markdown to HTML, with special handling for <think> blocks
window.renderMarkdown = function(text) {
  if (!text) return ''
  
  // Handle <think>...</think> blocks - render them dimmed
  // Use placeholder to avoid double-parsing
  const thinkBlocks = []
  let processed = text
  
  // Complete think blocks: <think>content</think>
  processed = processed.replace(/<think>([\s\S]*?)<\/think>/g, (match, content) => {
    const idx = thinkBlocks.length
    thinkBlocks.push(content.trim())
    return `<!--THINK_${idx}-->`
  })
  
  // Incomplete/streaming think block: <think>content (no closing tag yet)
  processed = processed.replace(/<think>([\s\S]*)$/g, (match, content) => {
    const idx = thinkBlocks.length
    thinkBlocks.push(content.trim())
    return `<!--THINK_${idx}-->`
  })
  
  // Render markdown once
  let html = marked.parse(processed)
  
  // Replace placeholders with styled think blocks
  thinkBlocks.forEach((content, idx) => {
    const rendered = content ? marked.parse(content) : ''
    html = html.replace(`<!--THINK_${idx}-->`, `<div class="chat-thinking">${rendered}</div>`)
  })
  
  return html
}

// ============================================
// Responsive Tile Grid System
// ============================================

const CELL_SIZE = 70    // Fixed cell size
const GRID_GAP = 8      // Gap between cells
const MIN_COLS = 12     // Minimum columns
const MOBILE_BREAKPOINT = 768

// Grid state
let gridState = {
  cols: MIN_COLS,       // Current column count (dynamic)
  panels: [],           // [{id, order, w, h, el, x, y}, ...]
}

// Settings
let autoCompact = false  // Whether to auto-compact other panels when dragging

// Check if mobile mode
function isMobile() {
  return window.innerWidth < MOBILE_BREAKPOINT
}

// Calculate available columns based on container width
function calculateCols() {
  return 12  // Fixed 12 columns
}

// Build grid state from DOM
function buildGridState() {
  const grid = document.getElementById('dashboard-panels')
  if (!grid) return
  
  gridState.cols = calculateCols()
  gridState.panels = []
  
  const panels = grid.querySelectorAll('.card')
  panels.forEach((panel, index) => {
    const size = panel.dataset.gridSize || '2x2'
    const [w, h] = size.split('x').map(Number)
    const x = parseInt(panel.dataset.gridX) || 0
    const y = parseInt(panel.dataset.gridY) || 0
    
    gridState.panels.push({
      id: panel.id,
      w: w,
      h: h,
      x: x,
      y: y,
      origX: x,  // Remember original position
      origY: y,
      el: panel
    })
  })
}

// Check if two rectangles overlap
function rectsOverlap(a, b) {
  return a.x < b.x + b.w &&
         a.x + a.w > b.x &&
         a.y < b.y + b.h &&
         a.y + a.h > b.y
}

// Push away overlapping cards, restore non-overlapping to original position
function pushAwayCards(excludeId) {
  const cols = gridState.cols
  const draggedCard = gridState.panels.find(c => c.id === excludeId)
  if (!draggedCard) return
  
  for (const card of gridState.panels) {
    if (card.id === excludeId) continue
    
    // Check if card at original position would overlap with dragged card
    const cardAtOrig = { x: card.origX, y: card.origY, w: card.w, h: card.h }
    
    if (rectsOverlap(cardAtOrig, draggedCard)) {
      // Need to push away - find a safe spot below dragged card
      card.x = card.origX
      card.y = draggedCard.y + draggedCard.h
      
      // Make sure we don't overlap with other cards at their current positions
      let safe = false
      while (!safe && card.y < 100) {
        safe = true
        for (const other of gridState.panels) {
          if (other.id === card.id || other.id === excludeId) continue
          if (rectsOverlap(card, other)) {
            card.y = other.y + other.h
            safe = false
            break
          }
        }
      }
    } else {
      // No overlap - restore to original position
      card.x = card.origX
      card.y = card.origY
    }
  }
}

// Compact cards: reposition all cards to fill gaps, keeping excluded card fixed
function compactCards(excludeId = null) {
  const cols = gridState.cols
  
  // Sort cards by position (top-left to bottom-right)
  const cardsToPlace = gridState.panels
    .filter(c => c.id !== excludeId)
    .sort((a, b) => a.y === b.y ? a.x - b.x : a.y - b.y)
  
  // Place the excluded card first (if any) - it stays fixed
  const placedCards = []
  const excludedCard = gridState.panels.find(c => c.id === excludeId)
  if (excludedCard) {
    placedCards.push(excludedCard)
  }
  
  // Place each card in the first available position
  for (const card of cardsToPlace) {
    let placed = false
    
    // Clamp width to available columns
    const cardW = Math.min(card.w, cols)
    
    // Try to find a spot from top-left
    for (let y = 0; y < 100 && !placed; y++) {
      for (let x = 0; x <= cols - cardW && !placed; x++) {
        // Check overlap with already placed cards
        let overlaps = false
        for (const p of placedCards) {
          if (x < p.x + p.w &&
              x + cardW > p.x &&
              y < p.y + p.h &&
              y + card.h > p.y) {
            overlaps = true
            break
          }
        }
        
        if (!overlaps) {
          card.x = x
          card.y = y
          placedCards.push(card)
          placed = true
        }
      }
    }
  }
}

// Apply positions to DOM
function applyPositions() {
  const grid = document.getElementById('dashboard-panels')
  if (!grid) return
  
  // Find actual used width (rightmost panel edge)
  let maxRight = 0
  let maxBottom = 400
  
  for (const panel of gridState.panels) {
    panel.el.style.left = `calc(${panel.x} * (var(--cell-size) + var(--grid-gap)))`
    panel.el.style.top = `calc(${panel.y} * (var(--cell-size) + var(--grid-gap)))`
    panel.el.dataset.gridX = panel.x
    panel.el.dataset.gridY = panel.y
    
    const right = panel.x + panel.w
    if (right > maxRight) maxRight = right
    
    const bottom = (panel.y + panel.h) * (CELL_SIZE + GRID_GAP)
    if (bottom > maxBottom) maxBottom = bottom
  }
  
  // Use actual content width for centering (not available cols)
  // Width = usedCols * cell + (usedCols-1) * gap
  const usedCols = Math.max(maxRight, MIN_COLS)
  const gridWidth = usedCols * CELL_SIZE + (usedCols - 1) * GRID_GAP
  
  grid.style.setProperty('--grid-cols', gridState.cols)
  grid.style.width = gridWidth + 'px'
  grid.style.minHeight = (maxBottom + 50) + 'px'
}

// Full reflow (compact all cards)
function reflow() {
  if (isMobile()) return
  buildGridState()
  compactCards()
  applyPositions()
}

// Just apply current positions from data attributes (no compacting)
function initPositions() {
  if (isMobile()) return
  buildGridState()
  applyPositions()
}

// Save panel positions to backend
async function savePositions() {
  const updates = gridState.panels.map(p => ({
    id: p.id.replace(/^panel-/, ''),
    x: p.x,
    y: p.y
  }))
  
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

// Drag functionality
function initCardDrag() {
  let dragPanel = null
  let dragPlaceholder = null
  let dragOverlay = null
  let startGridX = 0
  let startGridY = 0
  
  document.addEventListener('mousedown', (e) => {
    if (isMobile()) return
    
    const handle = e.target.closest('.card-drag-handle')
    if (!handle) return
    
    const card = handle.closest('.card')
    if (!card) return
    
    e.preventDefault()
    buildGridState()
    
    const panelState = gridState.panels.find(p => p.id === card.id)
    if (!panelState) return
    
    dragPanel = panelState
    startGridX = panelState.x
    startGridY = panelState.y
    
    const startX = e.clientX
    const startY = e.clientY
    const startLeft = panelState.x * (CELL_SIZE + GRID_GAP)
    const startTop = panelState.y * (CELL_SIZE + GRID_GAP)
    
    // Create overlay to capture all mouse events (prevents resize handle interference)
    dragOverlay = document.createElement('div')
    dragOverlay.style.cssText = `
      position: fixed;
      inset: 0;
      z-index: 99;
      cursor: grabbing;
    `
    document.body.appendChild(dragOverlay)
    
    // Create placeholder
    dragPlaceholder = document.createElement('div')
    dragPlaceholder.className = 'card-placeholder'
    dragPlaceholder.style.cssText = `
      position: absolute;
      left: ${startLeft}px;
      top: ${startTop}px;
      width: calc(${panelState.w} * var(--cell-size) + ${panelState.w - 1} * var(--grid-gap));
      height: calc(${panelState.h} * var(--cell-size) + ${panelState.h - 1} * var(--grid-gap));
      border: 2px dashed var(--kb-border);
      border-radius: 0.5rem;
      background: var(--kb-bg-hover);
      opacity: 0.3;
      pointer-events: none;
      transition: left 0.15s, top 0.15s;
    `
    card.parentElement.appendChild(dragPlaceholder)
    
    card.style.zIndex = '100'
    card.style.transition = 'box-shadow 0.2s'
    card.style.opacity = '0.95'
    card.style.boxShadow = '0 10px 40px rgba(0,0,0,0.3)'
    
    const onMouseMove = (e) => {
      const deltaX = e.clientX - startX
      const deltaY = e.clientY - startY
      
      // Move card freely
      card.style.left = (startLeft + deltaX) + 'px'
      card.style.top = (startTop + deltaY) + 'px'
      
      // Calculate target grid position
      const cols = gridState.cols
      const panelW = Math.min(panelState.w, cols)
      let newX = Math.round((startLeft + deltaX) / (CELL_SIZE + GRID_GAP))
      let newY = Math.round((startTop + deltaY) / (CELL_SIZE + GRID_GAP))
      newX = Math.max(0, Math.min(cols - panelW, newX))
      newY = Math.max(0, newY)
      
      // Update placeholder position
      dragPlaceholder.style.left = `calc(${newX} * (var(--cell-size) + var(--grid-gap)))`
      dragPlaceholder.style.top = `calc(${newY} * (var(--cell-size) + var(--grid-gap)))`
      
      // If position changed, update
      if (newX !== panelState.x || newY !== panelState.y) {
        panelState.x = newX
        panelState.y = newY
        
        // Push away overlapping cards (always), or full compact if autoCompact
        if (autoCompact) {
          compactCards(panelState.id)
        } else {
          pushAwayCards(panelState.id)
        }
        
        // Apply positions to other panels (with transition)
        for (const p of gridState.panels) {
          if (p.id === dragPanel.id) continue
          p.el.style.transition = 'left 0.15s, top 0.15s'
          p.el.style.left = `calc(${p.x} * (var(--cell-size) + var(--grid-gap)))`
          p.el.style.top = `calc(${p.y} * (var(--cell-size) + var(--grid-gap)))`
        }
      }
    }
    
    const onMouseUp = async () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      
      // Remove overlay
      if (dragOverlay) {
        dragOverlay.remove()
        dragOverlay = null
      }
      
      if (dragPlaceholder) {
        dragPlaceholder.remove()
        dragPlaceholder = null
      }
      
      card.style.zIndex = ''
      card.style.transition = ''
      card.style.opacity = ''
      card.style.boxShadow = ''
      
      // Clear transitions on other panels
      for (const p of gridState.panels) {
        p.el.style.transition = ''
      }
      
      // Snap to final position
      applyPositions()
      
      // Save positions if changed
      if (dragPanel.x !== startGridX || dragPanel.y !== startGridY) {
        await savePositions()
      }
      
      dragPanel = null
    }
    
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  })
}

// Resize functionality
function initCardResize() {
  document.addEventListener('mousedown', (e) => {
    if (isMobile()) return
    
    const handle = e.target.closest('.card-resize-handle')
    if (!handle) return
    
    e.preventDefault()
    buildGridState()
    if (autoCompact) compactCards()
    
    const cardId = handle.dataset.cardId || handle.dataset.panelId
    const card = document.getElementById('card-' + cardId) || document.getElementById('panel-' + cardId)
    if (!card) return
    
    const panelState = gridState.panels.find(p => p.id === card.id)
    if (!panelState) return
    
    const cols = gridState.cols
    const startX = e.clientX
    const startY = e.clientY
    const startW = panelState.w
    const startH = panelState.h
    
    // Get minimum size
    let minW = 2, minH = 2
    const minSizeAttr = card.dataset.minSize
    if (minSizeAttr && minSizeAttr.includes('x')) {
      const [w, h] = minSizeAttr.split('x').map(Number)
      minW = w || 2
      minH = h || 2
    }
    
    // Create overlay to capture all mouse events
    const resizeOverlay = document.createElement('div')
    resizeOverlay.style.cssText = `
      position: fixed;
      inset: 0;
      z-index: 99;
      cursor: se-resize;
    `
    document.body.appendChild(resizeOverlay)
    
    card.style.transition = 'none'
    card.style.zIndex = '100'
    
    const updateCardSize = (w, h) => {
      card.className = card.className.replace(/\bw\d+\b/g, '').replace(/\bh\d+\b/g, '').trim()
      card.classList.add('card', `w${w}`, `h${h}`)
      card.dataset.gridSize = `${w}x${h}`
      panelState.w = w
      panelState.h = h
    }
    
    const onMouseMove = (e) => {
      const deltaX = e.clientX - startX
      const deltaY = e.clientY - startY
      
      let newW = startW + Math.round(deltaX / (CELL_SIZE + GRID_GAP))
      let newH = startH + Math.round(deltaY / (CELL_SIZE + GRID_GAP))
      
      // Clamp to valid range
      newW = Math.max(minW, Math.min(cols, newW))
      newH = Math.max(minH, Math.min(8, newH))
      
      if (newW !== panelState.w || newH !== panelState.h) {
        updateCardSize(newW, newH)
        // Push away overlapping panels
        pushAwayCards(card.id)
        applyPositions()
      }
    }
    
    const onMouseUp = async () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      
      resizeOverlay.remove()
      
      card.style.transition = ''
      card.style.zIndex = ''
      
      // Save size and positions (other panels may have been pushed)
      const newSize = `${panelState.w}x${panelState.h}`
      try {
        await fetch(`/api/panels/${cardId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ size: newSize })
        })
        await savePositions()
      } catch (e) {
        console.error('Failed to save size/positions:', e)
      }
    }
    
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  })
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  if (!isMobile()) {
    initPositions()  // Just apply saved positions, don't compact
  }
  initCardDrag()
  initCardResize()
  
  // Expose autoCompact toggle
  window.setAutoCompact = (value) => { autoCompact = !!value }
  window.getAutoCompact = () => autoCompact
  window.compactAll = () => { buildGridState(); compactCards(); applyPositions(); savePositions() }
})

// Reflow after HTMX swaps (new panels added)
document.body.addEventListener('htmx:afterSwap', (e) => {
  if (e.detail.target.id === 'dashboard-panels') {
    setTimeout(reflow, 50)
  }
})

// Generate a simple session ID
function generateSessionId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
}

// Insert card reference to chat input (with rendered HTML for debug)
window.insertCardToChat = async function(cardId) {
  const chatBoxEl = document.querySelector('[x-data="chatBox"]')
  if (!chatBoxEl) return
  
  const chatBox = Alpine.$data(chatBoxEl)
  
  // Get panel/card element and extract info (support both panel-* and card-* IDs)
  const cardEl = document.getElementById('panel-' + cardId) || document.getElementById('card-' + cardId)
  if (!cardEl) return
  
  const titleEl = cardEl.querySelector('h3')
  const title = titleEl ? titleEl.textContent.trim() : cardId
  
  // Get rendered HTML from card content
  const contentEl = cardEl.querySelector('.card-content')
  const renderedHtml = contentEl ? contentEl.innerHTML.trim() : ''
  
  // Fetch panel data from API
  let cardData = null
  try {
    const res = await fetch(`/api/panels/${cardId}`)
    if (res.ok) {
      cardData = await res.json()
    }
  } catch (e) {
    console.error('Failed to fetch panel data:', e)
  }
  
  // Expand chat panel
  chatBox.expanded = true
  
  // Add card reference with HTML and data
  chatBox.addCardRef(cardId, title, renderedHtml, cardData)
}

// Alpine components
Alpine.data('chatBox', () => ({
  expanded: false,
  showSidebar: false,
  sessions: [],
  messages: [],
  loading: false,
  currentMessageIndex: -1,
  cardRefs: [], // [{id, title, html, data}, ...]
  sessionId: generateSessionId(), // Unique session for this browser tab
  abortController: null, // For stopping requests

  async init() {
    // Load sessions list when sidebar is first shown
    this.$watch('showSidebar', async (value) => {
      if (value && this.sessions.length === 0) {
        await this.loadSessions()
      }
    })
  },

  async loadSessions() {
    try {
      const res = await fetch('/api/sessions')
      if (res.ok) {
        this.sessions = await res.json()
      }
    } catch (e) {
      console.error('Failed to load sessions:', e)
    }
  },

  async loadSession(sessionId) {
    try {
      const res = await fetch(`/api/sessions/${sessionId}`)
      if (res.ok) {
        const data = await res.json()
        this.messages = data.messages || []
        // Update sessionId to continue this session
        this.sessionId = sessionId.replace('web-', '')
        this.scrollToBottom()
      }
    } catch (e) {
      console.error('Failed to load session:', e)
    }
  },

  newSession() {
    this.sessionId = generateSessionId()
    this.messages = []
    this.cardRefs = []
  },

  formatDate(isoString) {
    const date = new Date(isoString)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'just now'
    if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago'
    if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago'
    if (diff < 604800000) return Math.floor(diff / 86400000) + 'd ago'
    return date.toLocaleDateString()
  },

  addCardRef(cardId, cardTitle, renderedHtml = '', cardData = null) {
    // Avoid duplicates
    if (!this.cardRefs.find(c => c.id === cardId)) {
      this.cardRefs.push({ id: cardId, title: cardTitle, html: renderedHtml, data: cardData })
    }
    // Focus input and expand
    this.expanded = true
    setTimeout(() => {
      const input = this.$refs.messageInput
      if (input) input.focus()
    }, 50)
  },

  removeCardRef(cardId) {
    this.cardRefs = this.cardRefs.filter(c => c.id !== cardId)
  },

  getInputText() {
    const input = this.$refs.messageInput
    return input ? input.innerText.trim() : ''
  },

  clearInput() {
    const input = this.$refs.messageInput
    if (input) input.innerText = ''
  },

  renderMd(text) {
    return window.renderMarkdown(text)
  },

  stop() {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    this.loading = false
    // Add a note that generation was stopped
    if (this.currentMessageIndex >= 0 && this.messages[this.currentMessageIndex]) {
      const msg = this.messages[this.currentMessageIndex]
      if (msg.content) {
        msg.content += '\n\n*(stopped)*'
      }
    }
    this.currentMessageIndex = -1
  },

  async send() {
    const text = this.getInputText()
    if ((!text && this.cardRefs.length === 0) || this.loading) return

    // Build message with card references (include both data and rendered HTML)
    let userMessage = ''
    if (this.cardRefs.length > 0) {
      const refs = this.cardRefs.map(c => {
        let ref = `[${c.title}](${c.id})`
        
        // Add original card data (JSON)
        if (c.data) {
          const dataJson = JSON.stringify(c.data, null, 2)
          const truncatedData = dataJson.length > 3000 ? dataJson.slice(0, 3000) + '\n...' : dataJson
          ref += `\n<card-data id="${c.id}">\n${truncatedData}\n</card-data>`
        }
        
        // Add rendered HTML for visual debugging
        if (c.html) {
          const truncatedHtml = c.html.length > 2000 ? c.html.slice(0, 2000) + '...' : c.html
          ref += `\n<card-html id="${c.id}">\n${truncatedHtml}\n</card-html>`
        }
        return ref
      }).join('\n\n')
      userMessage = refs + (text ? '\n\n' + text : '')
    } else {
      userMessage = text
    }

    // Display message in chat (simplified, without HTML dump)
    const displayMessage = this.cardRefs.length > 0 
      ? this.cardRefs.map(c => `📌${c.title}`).join(' ') + (text ? ' ' + text : '')
      : text

    this.messages.push({ role: 'user', content: displayMessage })
    this.clearInput()
    this.cardRefs = []
    this.loading = true
    this.currentMessageIndex = -1
    
    // Create abort controller for this request
    this.abortController = new AbortController()

    try {
      // POST request with JSON body
      const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: this.sessionId
        }),
        signal: this.abortController.signal
      })
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            
            try {
              const event = JSON.parse(data)
              this.handleEvent(event)
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        // User stopped the request - already handled in stop()
        console.log('Request aborted by user')
      } else {
        console.error('Chat error:', error)
        this.messages.push({ role: 'assistant', content: '抱歉，连接出错了。' })
      }
    } finally {
      this.loading = false
      this.abortController = null
      this.scrollToBottom()
    }
  },

  handleKeydown(e) {
    // 忽略输入法组合状态下的回车（中文、日文等）
    if (e.isComposing || e.keyCode === 229) {
      return
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      this.send()
    }
  },

  handleEvent(event) {
    switch (event.type) {
      case 'message_start':
        this.messages.push({ role: 'assistant', content: '' })
        this.currentMessageIndex = this.messages.length - 1
        break
        
      case 'delta':
        if (this.currentMessageIndex >= 0 && this.messages[this.currentMessageIndex]) {
          this.messages[this.currentMessageIndex].content += event.content
        }
        this.scrollToBottom()
        break
        
      case 'message_end':
        this.currentMessageIndex = -1
        break
        
      case 'tool_start':
        let toolDisplay = event.tool
        if (event.args) {
          if (event.args.command) {
            toolDisplay += `: ${event.args.command}`
          } else if (event.args.path) {
            toolDisplay += `: ${event.args.path}`
          } else if (event.args.cardId) {
            toolDisplay += `: ${event.args.cardId}`
          } else if (event.args.panelId) {
            toolDisplay += `: ${event.args.panelId}`
          } else if (event.args.storageId) {
            toolDisplay += `: ${event.args.storageId}`
          } else if (event.args.type) {
            toolDisplay += `: ${event.args.type}`
          }
        }
        this.messages.push({ 
          role: 'tool', 
          content: toolDisplay,
          status: 'running',
          toolName: event.tool,
          args: event.args || {}
        })
        this.scrollToBottom()
        break
        
      case 'tool_end':
        for (let i = this.messages.length - 1; i >= 0; i--) {
          if (this.messages[i].role === 'tool' && this.messages[i].status === 'running') {
            this.messages[i].status = event.isError ? 'error' : 'done'
            
            // Refresh panels based on tool type
            if (!event.isError) {
              const tool = this.messages[i].toolName
              const args = this.messages[i].args
              
              if (tool === 'panel_create' || tool === 'panel_delete' || tool === 'market_install') {
                // Full dashboard refresh for panel add/remove
                this.refreshDashboard()
              } else if (tool === 'panel_update' && args.panelId) {
                // Refresh specific panel
                this.refreshPanel(args.panelId)
              } else if (tool === 'storage_update' && args.storageId) {
                // Refresh panels that use this storage
                this.refreshPanelsByStorage(args.storageId)
              }
            }
            break
          }
        }
        break
        
      case 'done':
        break
        
      case 'error':
        this.messages.push({ role: 'assistant', content: '错误: ' + event.message })
        break
    }
  },

  refreshDashboard() {
    htmx.ajax('GET', '/dashboard-panels', { target: '#dashboard-panels', swap: 'innerHTML' })
  },

  refreshPanel(panelId) {
    const panel = document.querySelector(`[data-panel-id="${panelId}"] .card-content`)
    if (panel) {
      htmx.ajax('GET', `/panels/${panelId}/content`, { target: panel, swap: 'innerHTML' })
    }
  },

  async refreshPanelsByStorage(storageId) {
    // Find panels that use this storage by checking dashboard
    try {
      const res = await fetch('/api/panels')
      const panels = await res.json()
      for (const panel of panels) {
        if (panel.storage_ids && panel.storage_ids.includes(storageId)) {
          this.refreshPanel(panel.id)
        }
      }
    } catch (e) {
      // Fallback to full refresh
      this.refreshDashboard()
    }
  },

  scrollToBottom() {
    this.$nextTick(() => {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    })
  }
}))

Alpine.start()

// Listen for dashboard updates
document.body.addEventListener('dashboardUpdated', () => {
  htmx.ajax('GET', '/dashboard-panels', { target: '#dashboard-panels', swap: 'innerHTML' })
})
