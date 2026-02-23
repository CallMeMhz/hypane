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

// Render markdown to HTML
window.renderMarkdown = function(text) {
  if (!text) return ''
  return marked.parse(text)
}

// ============================================
// Microsoft-style Tile Grid System
// ============================================

const CELL_SIZE = 70  // Fixed cell size (no scaling)
const GRID_GAP = 8    // Microsoft uses 8px gap
const MOBILE_BREAKPOINT = 768

// Get current grid columns based on viewport
function getGridCols() {
  const width = window.innerWidth
  if (width < MOBILE_BREAKPOINT) return 0  // Mobile: flow layout
  if (width < 1024) return 8   // Tablet: 8 columns
  return 12  // Desktop: 12 columns
}

// Grid state
let gridState = {
  cellSize: CELL_SIZE,
  cols: 12,
  cards: [],  // [{id, x, y, w, h, el}, ...]
}

// Check if mobile mode
function isMobile() {
  return window.innerWidth < MOBILE_BREAKPOINT
}

// Build grid state from DOM
function buildGridState() {
  const grid = document.getElementById('dashboard-cards')
  if (!grid) return
  
  gridState.cols = getGridCols()
  gridState.cards = []
  const cards = grid.querySelectorAll('.card')
  
  cards.forEach(card => {
    const x = parseInt(card.dataset.gridX) || 0
    const y = parseInt(card.dataset.gridY) || 0
    const size = card.dataset.gridSize || '2x2'
    const [w, h] = size.split('x').map(Number)
    
    gridState.cards.push({
      id: card.id,
      x, y, w, h,
      el: card
    })
  })
}

// Check if a position overlaps with any card (except excludeId)
function checkOverlap(x, y, w, h, excludeId) {
  for (const card of gridState.cards) {
    if (card.id === excludeId) continue
    
    // Check rectangle overlap
    if (x < card.x + card.w &&
        x + w > card.x &&
        y < card.y + card.h &&
        y + h > card.y) {
      return card
    }
  }
  return null
}

// Find first available position for a card (flow layout)
function findAvailablePosition(w, h, excludeId) {
  const cols = gridState.cols || 12
  for (let y = 0; y < 100; y++) {
    for (let x = 0; x <= cols - w; x++) {
      if (!checkOverlap(x, y, w, h, excludeId)) {
        return { x, y }
      }
    }
  }
  return { x: 0, y: 0 }
}

// Compact all cards - reflow to fill gaps (like Windows Start)
function compactCards(excludeId = null) {
  const cols = gridState.cols || 12
  
  // Sort cards by original position (top-left to bottom-right)
  const cardsToPlace = gridState.cards
    .filter(c => c.id !== excludeId)
    .sort((a, b) => a.y === b.y ? a.x - b.x : a.y - b.y)
  
  // Place the excluded card first (if any)
  const placedCards = []
  const excludedCard = gridState.cards.find(c => c.id === excludeId)
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
        for (const placed of placedCards) {
          if (x < placed.x + placed.w &&
              x + cardW > placed.x &&
              y < placed.y + placed.h &&
              y + card.h > placed.y) {
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

// Update grid container height
function updateGridHeight() {
  const grid = document.getElementById('dashboard-cards')
  if (!grid) return
  
  let maxBottom = 400
  for (const card of gridState.cards) {
    const bottom = (card.y + card.h) * (gridState.cellSize + GRID_GAP)
    if (bottom > maxBottom) maxBottom = bottom
  }
  
  grid.style.minHeight = (maxBottom + 50) + 'px'
}

// Apply positions to DOM
function applyPositions() {
  for (const card of gridState.cards) {
    card.el.style.left = `calc(${card.x} * (var(--cell-size) + var(--grid-gap)))`
    card.el.style.top = `calc(${card.y} * (var(--cell-size) + var(--grid-gap)))`
    card.el.dataset.gridX = card.x
    card.el.dataset.gridY = card.y
  }
  updateGridHeight()
}

// Save all card positions to backend
async function saveAllPositions() {
  const updates = gridState.cards.map(c => ({
    id: c.id.replace('card-', ''),
    position: { x: c.x, y: c.y }
  }))
  
  try {
    await fetch('/api/cards/positions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cards: updates })
    })
  } catch (e) {
    console.error('Failed to save positions:', e)
  }
}

// Card drag functionality
function initCardDrag() {
  let dragCard = null
  let dragPlaceholder = null
  
  document.addEventListener('mousedown', (e) => {
    // Skip on mobile
    if (isMobile()) return
    
    const handle = e.target.closest('.card-drag-handle')
    if (!handle) return
    
    const card = handle.closest('.card')
    if (!card) return
    
    e.preventDefault()
    buildGridState()
    
    const cardState = gridState.cards.find(c => c.id === card.id)
    if (!cardState) return
    
    dragCard = cardState
    const cellSize = CELL_SIZE
    const cols = gridState.cols
    const startX = e.clientX
    const startY = e.clientY
    const startGridX = cardState.x
    const startGridY = cardState.y
    
    // Create placeholder
    dragPlaceholder = document.createElement('div')
    dragPlaceholder.className = 'card-placeholder'
    dragPlaceholder.style.cssText = `
      position: absolute;
      left: calc(${startGridX} * (var(--cell-size) + var(--grid-gap)));
      top: calc(${startGridY} * (var(--cell-size) + var(--grid-gap)));
      width: calc(${cardState.w} * var(--cell-size) + ${cardState.w - 1} * var(--grid-gap));
      height: calc(${cardState.h} * var(--cell-size) + ${cardState.h - 1} * var(--grid-gap));
      border: 2px dashed var(--kb-border);
      border-radius: 0.5rem;
      opacity: 0.5;
      pointer-events: none;
    `
    card.parentElement.appendChild(dragPlaceholder)
    
    card.style.zIndex = '100'
    card.style.transition = 'none'
    card.style.opacity = '0.9'
    card.style.boxShadow = '0 10px 40px rgba(0,0,0,0.3)'
    
    const onMouseMove = (e) => {
      const deltaX = e.clientX - startX
      const deltaY = e.clientY - startY
      
      // Free movement for the dragged card
      card.style.left = `calc(${startGridX} * (var(--cell-size) + var(--grid-gap)) + ${deltaX}px)`
      card.style.top = `calc(${startGridY} * (var(--cell-size) + var(--grid-gap)) + ${deltaY}px)`
      
      // Calculate snapped grid position
      const cardW = Math.min(cardState.w, cols)
      let newX = startGridX + Math.round(deltaX / (cellSize + GRID_GAP))
      let newY = startGridY + Math.round(deltaY / (cellSize + GRID_GAP))
      newX = Math.max(0, Math.min(cols - cardW, newX))
      newY = Math.max(0, newY)
      
      // Update placeholder position
      dragPlaceholder.style.left = `calc(${newX} * (var(--cell-size) + var(--grid-gap)))`
      dragPlaceholder.style.top = `calc(${newY} * (var(--cell-size) + var(--grid-gap)))`
      
      // Update dragged card position and recompact
      if (newX !== cardState.x || newY !== cardState.y) {
        cardState.x = newX
        cardState.y = newY
        // Recompact all other cards around the dragged card
        compactCards(cardState.id)
        applyPositions()
      }
    }
    
    const onMouseUp = async () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      
      if (dragPlaceholder) {
        dragPlaceholder.remove()
        dragPlaceholder = null
      }
      
      card.style.zIndex = ''
      card.style.transition = ''
      card.style.opacity = ''
      card.style.boxShadow = ''
      
      // Snap to final position
      applyPositions()
      
      // Save all positions
      await saveAllPositions()
      
      dragCard = null
    }
    
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  })
}

// Card resize functionality
function initCardResize() {
  document.addEventListener('mousedown', (e) => {
    // Skip on mobile
    if (isMobile()) return
    
    const handle = e.target.closest('.card-resize-handle')
    if (!handle) return
    
    e.preventDefault()
    buildGridState()
    
    const cardId = handle.dataset.cardId
    const card = document.getElementById('card-' + cardId)
    if (!card) return
    
    const cardState = gridState.cards.find(c => c.id === card.id)
    if (!cardState) return
    
    const cellSize = CELL_SIZE
    const cols = gridState.cols
    const startX = e.clientX
    const startY = e.clientY
    const startW = cardState.w
    const startH = cardState.h
    
    // Get minimum size
    let minW = 2, minH = 2
    const minSizeAttr = card.dataset.minSize
    if (minSizeAttr && minSizeAttr.includes('x')) {
      const [w, h] = minSizeAttr.split('x').map(Number)
      minW = w || 2
      minH = h || 2
    }
    
    card.style.transition = 'none'
    
    const updateCardSize = (w, h) => {
      card.className = card.className.replace(/\bw\d+\b/g, '').replace(/\bh\d+\b/g, '').trim()
      card.classList.add('card', `w${w}`, `h${h}`)
      card.dataset.gridSize = `${w}x${h}`
      cardState.w = w
      cardState.h = h
    }
    
    const onMouseMove = (e) => {
      const deltaX = e.clientX - startX
      const deltaY = e.clientY - startY
      
      let newW = startW + Math.round(deltaX / (cellSize + GRID_GAP))
      let newH = startH + Math.round(deltaY / (cellSize + GRID_GAP))
      
      newW = Math.max(minW, Math.min(cols - cardState.x, newW))
      newH = Math.max(minH, Math.min(8, newH))
      
      if (newW !== cardState.w || newH !== cardState.h) {
        updateCardSize(newW, newH)
        compactCards(cardState.id)
        applyPositions()
      }
    }
    
    const onMouseUp = async () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      
      card.style.transition = ''
      
      // Save size and positions
      const newSize = `${cardState.w}x${cardState.h}`
      try {
        await fetch(`/api/cards/${cardId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ size: newSize })
        })
        await saveAllPositions()
      } catch (e) {
        console.error('Failed to save:', e)
      }
    }
    
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  })
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  buildGridState()
  if (!isMobile()) {
    applyPositions()
  }
  initCardDrag()
  initCardResize()
})

// Update on resize
window.addEventListener('resize', () => {
  const wasMobile = gridState.cols === 0
  buildGridState()
  const nowMobile = gridState.cols === 0
  
  // Only reposition if not mobile
  if (!nowMobile) {
    // If switching from mobile to desktop, recompact
    if (wasMobile) {
      compactCards()
    }
    applyPositions()
  }
})

// Generate a simple session ID
function generateSessionId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
}

// Insert card reference to chat input (with rendered HTML for debug)
window.insertCardToChat = function(cardId) {
  const chatBoxEl = document.querySelector('[x-data="chatBox"]')
  if (!chatBoxEl) return
  
  const chatBox = Alpine.$data(chatBoxEl)
  
  // Get card element and extract info
  const cardEl = document.getElementById('card-' + cardId)
  if (!cardEl) return
  
  const titleEl = cardEl.querySelector('h3')
  const title = titleEl ? titleEl.textContent.trim() : cardId
  
  // Get rendered HTML from card content
  const contentEl = cardEl.querySelector('.card-content')
  const renderedHtml = contentEl ? contentEl.innerHTML.trim() : ''
  
  // Open chat if not open
  if (!chatBox.open) {
    chatBox.open = true
  }
  
  // Add card reference with HTML
  chatBox.addCardRef(cardId, title, renderedHtml)
}

// Alpine components
Alpine.data('chatBox', () => ({
  open: false,
  messages: [],
  loading: false,
  currentMessageIndex: -1,
  cardRefs: [], // [{id, title, html}, ...]
  sessionId: generateSessionId(), // Unique session for this browser tab
  abortController: null, // For stopping requests

  toggle() {
    this.open = !this.open
  },

  addCardRef(cardId, cardTitle, renderedHtml = '') {
    // Avoid duplicates
    if (!this.cardRefs.find(c => c.id === cardId)) {
      this.cardRefs.push({ id: cardId, title: cardTitle, html: renderedHtml })
    }
    // Focus input after a short delay
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

    // Build message with card references (include rendered HTML for agent debugging)
    let userMessage = ''
    if (this.cardRefs.length > 0) {
      const refs = this.cardRefs.map(c => {
        // Format: [title](id) with HTML context
        let ref = `[${c.title}](${c.id})`
        if (c.html) {
          // Add rendered HTML as context (truncate if too long)
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
          } else if (event.args.type) {
            toolDisplay += `: ${event.args.type}`
          }
        }
        this.messages.push({ 
          role: 'tool', 
          content: toolDisplay,
          status: 'running'
        })
        this.scrollToBottom()
        break
        
      case 'tool_end':
        for (let i = this.messages.length - 1; i >= 0; i--) {
          if (this.messages[i].role === 'tool' && this.messages[i].status === 'running') {
            this.messages[i].status = event.isError ? 'error' : 'done'
            break
          }
        }
        break
        
      case 'done':
        if (event.dashboardUpdated) {
          this.refreshDashboard()
        }
        break
        
      case 'error':
        this.messages.push({ role: 'assistant', content: '错误: ' + event.message })
        break
    }
  },

  refreshDashboard() {
    htmx.ajax('GET', '/dashboard-cards', { target: '#dashboard-cards', swap: 'innerHTML' })
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
  htmx.ajax('GET', '/dashboard-cards', { target: '#dashboard-cards', swap: 'innerHTML' })
})
