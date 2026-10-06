import request from '@/utils/request'
import { getToken } from '@/utils/auth'

// 非流式（保留兼容：脚本化调用 / 快速调试）
export function chatApi(data) {
  return request({
    url: '/api/ai/chat',
    method: 'post',
    data,
    timeout: 60000
  })
}

// 会话列表
export function listConversationsApi() {
  return request({ url: '/api/ai/conversations', method: 'get' })
}

// 某个会话的历史消息
export function getMessagesApi(conversationId) {
  return request({
    url: `/api/ai/conversations/${conversationId}/messages`,
    method: 'get'
  })
}

// 删除会话
export function deleteConversationApi(conversationId) {
  return request({
    url: `/api/ai/conversations/${conversationId}`,
    method: 'delete'
  })
}

/**
 * 流式对话（SSE over fetch）。
 * EventSource 无法携带 Authorization 头，所以用 fetch + ReadableStream 手动解析 SSE。
 * @param {Object}   opts
 * @param {string}   opts.content         本轮提问
 * @param {number?}  opts.conversationId  会话 id，为空表示新建会话
 * @param {Function} opts.onEvent         每收到一个事件回调一次
 * @param {AbortSignal?} opts.signal      用于"停止生成"
 */
export async function streamChatApi({ content, conversationId, onEvent, signal }) {
  const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
  const res = await fetch(`${base}/api/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken() || ''}`
    },
    body: JSON.stringify({ content, conversation_id: conversationId ?? null }),
    signal
  })

  if (!res.ok || !res.body) {
    throw new Error(`流式请求失败：HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // SSE 以空行分隔事件
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''

    for (const block of blocks) {
      const dataLine = block
        .split('\n')
        .filter((l) => l.startsWith('data:'))
        .map((l) => l.slice(5).trim())
        .join('')
      if (!dataLine) continue
      try {
        onEvent(JSON.parse(dataLine))
      } catch (e) {
        console.warn('[AI] 无法解析的 SSE 事件', dataLine)
      }
    }
  }
}
