// Styles
import './styles/main.css'

// HTMX
import htmx from 'htmx.org'
window.htmx = htmx

// Alpine.js
import Alpine from 'alpinejs'
window.Alpine = Alpine

// Alpine components
Alpine.data('chatBox', () => ({
  open: false,
  message: '',
  messages: [],
  loading: false,
  currentMessageIndex: -1,

  toggle() {
    this.open = !this.open
  },

  async send() {
    if (!this.message.trim() || this.loading) return

    const userMessage = this.message
    this.messages.push({ role: 'user', content: userMessage })
    this.message = ''
    this.loading = true
    this.currentMessageIndex = -1

    try {
      const response = await fetch('/chat/stream?' + new URLSearchParams({ message: userMessage }))
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
      console.error('Chat error:', error)
      this.messages.push({ role: 'assistant', content: '抱歉，连接出错了。' })
    } finally {
      this.loading = false
      this.scrollToBottom()
    }
  },

  handleEvent(event) {
    switch (event.type) {
      case 'message_start':
        // 新消息开始（只有有内容时才会收到这个事件）
        this.messages.push({ role: 'assistant', content: '' })
        this.currentMessageIndex = this.messages.length - 1
        break
        
      case 'delta':
        // 文本增量
        if (this.currentMessageIndex >= 0 && this.messages[this.currentMessageIndex]) {
          this.messages[this.currentMessageIndex].content += event.content
        }
        this.scrollToBottom()
        break
        
      case 'message_end':
        // 消息结束，重置当前消息索引
        this.currentMessageIndex = -1
        break
        
      case 'tool_start':
        // 工具调用，显示为小标签
        let toolDisplay = event.tool
        if (event.args) {
          if (event.args.command) {
            toolDisplay += `: ${event.args.command}`
          } else if (event.args.path) {
            toolDisplay += `: ${event.args.path}`
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
        // 工具完成，更新最近的同名工具消息状态
        for (let i = this.messages.length - 1; i >= 0; i--) {
          if (this.messages[i].role === 'tool' && this.messages[i].status === 'running') {
            this.messages[i].status = event.isError ? 'error' : 'done'
            break
          }
        }
        break
        
      case 'done':
        // Agent 完成
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
