// Styles
import './styles/main.css'

// HTMX
import htmx from 'htmx.org'
window.htmx = htmx

// Sortable for drag-and-drop
import Sortable from 'sortablejs'

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

// Grid layout - sortable drag-and-drop
let sortableInstance = null

function initGrid() {
  const grid = document.getElementById('dashboard-cards')
  if (!grid) return
  
  initSortable(grid)
}

function initSortable(grid) {
  if (sortableInstance) {
    sortableInstance.destroy()
  }
  
  sortableInstance = new Sortable(grid, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    dragClass: 'sortable-drag',
    handle: '.card-drag-handle',
    draggable: '.card',
    
    onEnd: async function(evt) {
      // Get new order of card IDs
      const cards = grid.querySelectorAll('.card')
      const cardIds = Array.from(cards).map(el => {
        const id = el.id.replace('card-', '')
        return id
      }).filter(id => id) // Filter out empty
      
      // Save new order to backend
      try {
        await fetch('/api/cards/reorder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cardIds })
        })
      } catch (e) {
        console.error('Failed to save card order:', e)
      }
    }
  })
}

// Refresh grid (re-init sortable after HTMX swap)
function refreshGrid() {
  const grid = document.getElementById('dashboard-cards')
  if (grid) {
    initSortable(grid)
  }
}

// Card resize functionality
const SIZE_ORDER = ['small', 'medium', 'large', 'full']

function initCardResize() {
  document.addEventListener('mousedown', (e) => {
    const handle = e.target.closest('.card-resize-handle')
    if (!handle) return
    
    e.preventDefault()
    const cardId = handle.dataset.cardId
    const card = document.getElementById('card-' + cardId)
    if (!card) return
    
    const startX = e.clientX
    const startY = e.clientY
    const startWidth = card.offsetWidth
    const startHeight = card.offsetHeight
    const gridWidth = card.parentElement.offsetWidth
    
    // Get current size
    let currentSize = 'medium'
    for (const size of SIZE_ORDER) {
      if (card.classList.contains('card-' + size)) {
        currentSize = size
        break
      }
    }
    
    // Store original min-height and set temporary styles
    const originalMinHeight = card.style.minHeight
    card.style.transition = 'none'
    
    const onMouseMove = (e) => {
      const deltaX = e.clientX - startX
      const deltaY = e.clientY - startY
      const newWidth = startWidth + deltaX
      const newHeight = startHeight + deltaY
      const widthPercent = newWidth / gridWidth
      
      // Determine new size based on width percentage
      let newSize = 'small'
      if (widthPercent > 0.8) {
        newSize = 'full'
      } else if (widthPercent > 0.55) {
        newSize = 'large'
      } else if (widthPercent > 0.35) {
        newSize = 'medium'
      }
      
      // Update width class if changed
      if (newSize !== currentSize) {
        card.classList.remove('card-small', 'card-medium', 'card-large', 'card-full')
        card.classList.add('card-' + newSize)
        currentSize = newSize
      }
      
      // Update height directly (with minimum)
      const minHeight = 80
      card.style.minHeight = Math.max(minHeight, newHeight) + 'px'
    }
    
    const onMouseUp = async () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      
      // Get final height
      const finalHeight = card.style.minHeight
      card.style.transition = ''
      
      // Save new size and height to backend
      try {
        const updates = { size: currentSize }
        if (finalHeight) {
          updates.height = finalHeight
        }
        await fetch(`/api/cards/${cardId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates)
        })
      } catch (e) {
        console.error('Failed to save card size:', e)
      }
    }
    
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  })
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(initGrid, 100)
  initCardResize()
})

// Refresh after HTMX swaps
document.body.addEventListener('htmx:afterSwap', (e) => {
  if (e.target.id === 'dashboard-cards') {
    setTimeout(refreshGrid, 50)
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
