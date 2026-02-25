import './chat.css'
import { createChatBoxComponent, insertCardToChat, renderMarkdown } from './chat.js'

export { createChatBoxComponent, insertCardToChat, renderMarkdown }

export function registerChat(Alpine, options = {}) {
  Alpine.data('chatBox', createChatBoxComponent(options))
  window.insertCardToChat = insertCardToChat
  window.renderMarkdown = renderMarkdown
}
