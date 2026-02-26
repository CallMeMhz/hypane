import { marked } from 'marked'

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,  // Convert \n to <br>
  gfm: true,     // GitHub Flavored Markdown
})

// Render markdown to HTML, with special handling for <think> blocks
export function renderMarkdown(text) {
  if (!text) return ''

  // Handle <think>...</think> blocks - render them dimmed
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

// Generate a simple session ID
function generateSessionId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
}

// Insert card reference to chat input (with rendered HTML for debug)
export async function insertCardToChat(cardId) {
  const chatBoxEl = document.querySelector('[x-data="chatBox"]')
  if (!chatBoxEl) return

  const Alpine = window.Alpine
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

/**
 * Create the Alpine chatBox component.
 * @param {Object} options
 * @param {Function} options.onToolEnd - callback(tool, args) when a tool completes successfully
 */
export function createChatBoxComponent(options = {}) {
  const { onToolEnd } = options

  return () => ({
    expanded: false,
    showSidebar: false,
    sessions: [],
    messages: [],
    loading: false,
    currentMessageIndex: -1,
    cardRefs: [], // [{id, title, html, data}, ...]
    sessionId: generateSessionId(),
    abortController: null,

    async init() {
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
      if (!this.cardRefs.find(c => c.id === cardId)) {
        this.cardRefs.push({ id: cardId, title: cardTitle, html: renderedHtml, data: cardData })
      }
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
      return renderMarkdown(text)
    },

    stop() {
      if (this.abortController) {
        this.abortController.abort()
        this.abortController = null
      }
      this.loading = false
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

      // Build message with card references
      let userMessage = ''
      if (this.cardRefs.length > 0) {
        const refs = this.cardRefs.map(c => {
          let ref = `[${c.title}](${c.id})`
          if (c.data) {
            const dataJson = JSON.stringify(c.data, null, 2)
            const truncatedData = dataJson.length > 3000 ? dataJson.slice(0, 3000) + '\n...' : dataJson
            ref += `\n<card-data id="${c.id}">\n${truncatedData}\n</card-data>`
          }
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

      const displayMessage = this.cardRefs.length > 0
        ? this.cardRefs.map(c => `📌${c.title}`).join(' ') + (text ? ' ' + text : '')
        : text

      this.messages.push({ role: 'user', content: displayMessage })
      this.clearInput()
      this.cardRefs = []
      this.loading = true
      this.currentMessageIndex = -1

      this.abortController = new AbortController()

      try {
        const dashboardId = document.querySelector('[data-dashboard-id]')?.dataset.dashboardId || 'default'
        const response = await fetch('/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            session_id: this.sessionId,
            dashboard_id: dashboardId
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

              // Notify via callback instead of directly refreshing
              if (!event.isError && onToolEnd) {
                const tool = this.messages[i].toolName
                const args = this.messages[i].args
                onToolEnd(tool, args)
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

    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    }
  })
}
