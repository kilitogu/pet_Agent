<template>
  <div class="ai-page">
    <!-- 左侧：会话列表 -->
    <aside class="panel conv">
      <div class="conv__new">
        <el-button type="primary" style="width: 100%" @click="handleNew">
          <AppIcon name="plus" :size="15" />
          <span>新建对话</span>
        </el-button>
      </div>

      <div class="conv__list">
        <button
          v-for="c in conversations"
          :key="c.id"
          type="button"
          class="conv__item"
          :class="{ active: c.id === conversationId }"
          @click="handleOpen(c.id)"
        >
          <span class="conv__title">{{ c.title }}</span>
          <AppIcon
            name="trash"
            :size="15"
            class="conv__del"
            @click.stop="handleDelete(c)"
          />
        </button>
        <p v-if="!conversations.length" class="conv__empty">还没有对话记录</p>
      </div>
    </aside>

    <!-- 右侧：对话区 -->
    <section class="chat">
      <header class="chat__head">
        <div class="chat__avatar">咪</div>
        <div class="chat__who">
          <div class="chat__name">咪咪</div>
          <div class="chat__status">
            {{ loading ? '正在查询…' : '可查宠物库、知识库与系统统计' }}
          </div>
        </div>
        <el-button v-if="loading" text type="danger" @click="handleStop">
          停止生成
        </el-button>
      </header>

      <div ref="scrollRef" class="chat__scroll">
        <div class="msg-row">
          <div class="msg-avatar msg-avatar--ai">咪</div>
          <div class="msg-body">
            <div class="bubble bubble--ai">
              你好，我是咪咪。可以直接问我：现在有哪些待领养的宠物、领养流程是什么、
              系统里一共有多少只。涉及具体数据的问题，我会去数据库里查。
            </div>
          </div>
        </div>

        <div
          v-for="(msg, mi) in messages"
          :key="mi"
          class="msg-row"
          :class="msg.role === 'user' ? 'msg-row--user' : ''"
        >
          <div
            class="msg-avatar"
            :class="msg.role === 'user' ? 'msg-avatar--user' : 'msg-avatar--ai'"
          >
            <img
              v-if="msg.role === 'user' && userInfo?.avatar"
              :src="resolveAvatar(userInfo.avatar)"
              alt=""
              @error="(e) => (e.target.style.display = 'none')"
            />
            <template v-else>
              {{ msg.role === 'user' ? (userInfo?.name?.charAt(0)?.toUpperCase() || '我') : '咪' }}
            </template>
          </div>

          <div class="msg-body">
            <!-- 工具调用轨迹 -->
            <div v-if="msg.toolCalls && msg.toolCalls.length" class="tools">
              <button
                v-for="(t, ti) in msg.toolCalls"
                :key="ti"
                type="button"
                class="tool"
                :class="t.status === 'running' ? 'is-running' : 'is-done'"
                @click="t.open = !t.open"
              >
                <span class="tool__dot"></span>
                <span class="tool__name">{{ toolLabel(t.name) }}</span>
                <span class="tool__state">
                  {{ t.status === 'running' ? '执行中' : '已完成' }}
                </span>
                <span class="tool__caret" :class="{ open: t.open }">›</span>
              </button>

              <div
                v-for="(t, ti) in msg.toolCalls"
                v-show="t.open"
                :key="'d' + ti"
                class="tool-detail"
              >
                <div class="tool-detail__label">调用参数</div>
                <pre>{{ pretty(t.arguments) }}</pre>
                <div class="tool-detail__label">返回结果</div>
                <pre>{{ t.result || '（执行中…）' }}</pre>
              </div>
            </div>

            <div v-if="msg.content" class="bubble" :class="msg.role === 'user' ? 'bubble--user' : 'bubble--ai'" v-html="renderContent(msg.content)"></div>

            <div
              v-if="msg.role === 'assistant' && loading && !msg.content && !(msg.toolCalls || []).length"
              class="bubble bubble--ai bubble--typing"
            >
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="messages.length === 0" class="quick">
        <button
          v-for="(q, idx) in quickQuestions"
          :key="idx"
          type="button"
          class="quick__item"
          @click="sendMessage(q)"
        >
          {{ q }}
        </button>
      </div>

      <div class="composer">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          resize="none"
          placeholder="问点具体的，比如：现在有哪些待领养的猫？领养流程是什么？"
          @keydown.enter.exact.prevent="handleSend"
        />
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!inputText.trim()"
          @click="handleSend"
        >
          <AppIcon name="send" :size="16" />
          <span>发送</span>
        </el-button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppIcon from '@/components/AppIcon.vue'
import { useUser } from '@/utils/user'
import {
  listConversationsApi,
  getMessagesApi,
  deleteConversationApi,
  streamChatApi
} from '@/api/ai'

const { userInfo } = useUser()

const messages = reactive([])
const conversations = ref([])
const conversationId = ref(null)
const inputText = ref('')
const loading = ref(false)
const scrollRef = ref(null)
let controller = null

const quickQuestions = [
  '现在有哪些待领养的猫？',
  '领养流程是什么？审核要多久？',
  '系统一共有多少只宠物？',
  '把已领养的宠物也列出来看看'
]

const TOOL_LABELS = {
  search_pets: '检索宠物库',
  get_pet_detail: '查询宠物档案',
  get_system_stats: '获取系统统计',
  search_knowledge_base: '检索知识库',
  get_my_profile: '查询我的资料'
}
const toolLabel = (name) => TOOL_LABELS[name] || name

/* ============ 头像地址解析 ============ */
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const resolveAvatar = (avatar) => {
  if (!avatar) return ''
  if (/^https?:\/\//.test(avatar) || avatar.startsWith('data:') || avatar.startsWith('blob:')) {
    return avatar
  }
  return `${API_BASE}${avatar.startsWith('/') ? '' : '/'}${avatar}`
}

/* ============ 发送（流式） ============ */
const handleSend = () => sendMessage(inputText.value.trim())

const sendMessage = async (text) => {
  if (!text || loading.value) return

  messages.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  const assistant = reactive({ role: 'assistant', content: '', toolCalls: [] })
  messages.push(assistant)

  loading.value = true
  controller = new AbortController()

  try {
    await streamChatApi({
      content: text,
      conversationId: conversationId.value,
      signal: controller.signal,
      onEvent: (ev) => {
        if (ev.type === 'meta') {
          conversationId.value = ev.conversation_id
        } else if (ev.type === 'delta') {
          assistant.content += ev.content
        } else if (ev.type === 'tool_call') {
          assistant.toolCalls.push({
            name: ev.name,
            arguments: ev.arguments,
            result: '',
            status: 'running',
            open: false
          })
        } else if (ev.type === 'tool_result') {
          const t = [...assistant.toolCalls]
            .reverse()
            .find((x) => x.name === ev.name && x.status === 'running')
          if (t) {
            t.result = ev.result
            t.status = 'done'
          }
        } else if (ev.type === 'error') {
          assistant.content += (assistant.content ? '\n\n' : '') + `（出错：${ev.message}）`
        }
        scrollToBottom()
      }
    })
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.error('[AI Assistant] 流式请求失败', e)
      assistant.content +=
        (assistant.content ? '\n\n' : '') + '网络异常，请稍后重试。'
    }
  } finally {
    loading.value = false
    controller = null
    await loadConversations()
    scrollToBottom()
  }
}

const handleStop = () => {
  if (controller) controller.abort()
}

/* ============ 会话管理 ============ */
const loadConversations = async () => {
  try {
    const res = await listConversationsApi()
    conversations.value = res?.data || []
  } catch (e) {
    console.error('[AI] 加载会话列表失败', e)
  }
}

const handleNew = () => {
  if (loading.value) return
  conversationId.value = null
  messages.splice(0, messages.length)
}

const handleOpen = async (id) => {
  if (loading.value || id === conversationId.value) return
  try {
    const res = await getMessagesApi(id)
    const rows = res?.data || []
    conversationId.value = id
    messages.splice(0, messages.length)
    rows.forEach((m) => {
      messages.push({
        role: m.role,
        content: m.content || '',
        toolCalls: (m.tool_calls || []).map((t) => ({
          name: t.name,
          arguments: t.arguments,
          result: t.result,
          status: 'done',
          open: false
        }))
      })
    })
    scrollToBottom()
  } catch (e) {
    console.error('[AI] 加载历史消息失败', e)
  }
}

const handleDelete = async (c) => {
  try {
    await ElMessageBox.confirm(`确定删除对话「${c.title}」吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await deleteConversationApi(c.id)
    if (conversationId.value === c.id) handleNew()
    await loadConversations()
    ElMessage.success('对话已删除')
  } catch (e) {
    console.error('[AI] 删除对话失败', e)
  }
}

/* ============ 滚动 ============ */
const scrollToBottom = () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}
watch(messages, scrollToBottom, { deep: true })

/* ============ 渲染工具 ============ */
const pretty = (v) => {
  if (v === null || v === undefined || v === '') return '（无参数）'
  if (typeof v === 'string') {
    try {
      return JSON.stringify(JSON.parse(v), null, 2)
    } catch {
      return v
    }
  }
  return JSON.stringify(v, null, 2)
}

const escapeHtml = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

/**
 * 极简 Markdown 渲染：模型习惯用 **加粗**、- 列表、# 标题，
 * 只做换行转义的话用户会看到一堆星号。这里先转义 HTML 再渲染受控子集。
 * 只输出自己生成的标签，不存在注入风险。
 */
const renderContent = (text) => {
  if (!text) return ''

  const inline = (s) =>
    s
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+?)`/g, '<code>$1</code>')

  const out = []
  let inList = false
  const closeList = () => {
    if (inList) {
      out.push('</ul>')
      inList = false
    }
  }

  for (const raw of escapeHtml(text).split('\n')) {
    const line = raw.replace(/\s+$/, '')
    const bullet = line.match(/^\s*[-*]\s+(.*)$/)
    const heading = line.match(/^#{1,4}\s+(.*)$/)

    if (bullet) {
      if (!inList) {
        out.push('<ul>')
        inList = true
      }
      out.push(`<li>${inline(bullet[1])}</li>`)
      continue
    }

    closeList()
    if (heading) {
      out.push(`<p class="md-h">${inline(heading[1])}</p>`)
    } else if (!line.trim()) {
      out.push('<div class="md-gap"></div>')
    } else {
      out.push(`<p>${inline(line)}</p>`)
    }
  }
  closeList()
  return out.join('')
}

onMounted(loadConversations)
</script>

<style scoped>
.ai-page {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 14px;
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
}

/* ============ 左侧会话列表 ============ */
.conv {
  width: 228px;
  flex-shrink: 0;
}

.conv__new {
  padding: 12px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}

.conv__list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px;
}

.conv__item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-left: 2px solid transparent;
  border-radius: 0 var(--r) var(--r) 0;
  background: transparent;
  font-family: inherit;
  font-size: 13px;
  color: var(--ink-2);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s, border-color 0.15s;
}

.conv__item:hover {
  background: var(--surface-2);
}

.conv__item.active {
  background: var(--brand-soft);
  border-left-color: var(--brand);
  color: var(--brand);
  font-weight: 500;
}

.conv__title {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv__del {
  opacity: 0;
  color: var(--faint);
  transition: opacity 0.15s, color 0.15s;
}

.conv__item:hover .conv__del {
  opacity: 1;
}

.conv__del:hover {
  color: var(--danger);
}

.conv__empty {
  padding: 18px 10px;
  font-size: 12px;
  color: var(--faint);
  text-align: center;
}

/* ============ 右侧对话区 ============ */
.chat {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.chat__head {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 12px 16px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}

.chat__avatar {
  width: 34px;
  height: 34px;
  border-radius: var(--r);
  background: var(--brand);
  color: #fff;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat__who {
  flex: 1;
  min-width: 0;
}

.chat__name {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  letter-spacing: 0.4px;
}

.chat__status {
  margin-top: 1px;
  font-size: 12px;
  color: var(--muted);
}

/* 消息滚动区 */
.chat__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.msg-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.msg-row--user {
  flex-direction: row-reverse;
}

.msg-body {
  max-width: min(76%, 620px);
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.msg-row--user .msg-body {
  align-items: flex-end;
}

.msg-avatar {
  width: 30px;
  height: 30px;
  border-radius: var(--r);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 500;
  flex-shrink: 0;
  overflow: hidden;
}

.msg-avatar--ai {
  background: var(--brand-soft);
  color: var(--brand);
  font-size: 15px;
}

.msg-avatar--user {
  background: var(--surface-2);
  border: 1px solid var(--line);
  color: var(--ink-2);
}

.msg-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 气泡 */
.bubble {
  padding: 10px 14px;
  border-radius: var(--r-lg);
  font-size: 13.5px;
  line-height: 1.75;
  word-break: break-word;
  white-space: pre-wrap;
  min-width: 0;
}

.bubble--ai {
  background: var(--surface);
  border: 1px solid var(--line);
  border-top-left-radius: var(--r-sm);
  color: var(--ink-2);
}

.bubble--user {
  background: var(--brand);
  color: #fff;
  border-top-right-radius: var(--r-sm);
}

/* v-html 渲染的内容不带 scoped 属性，需要用 :deep 才能命中 */
.bubble :deep(p) {
  margin: 0;
}

.bubble :deep(ul) {
  margin: 4px 0;
  padding-left: 18px;
  list-style: disc;
}

.bubble :deep(li) {
  margin: 2px 0;
}

.bubble :deep(strong) {
  font-weight: 600;
  color: var(--ink);
}

.bubble :deep(code) {
  padding: 0 4px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 3px;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12.5px;
}

.bubble :deep(.md-h) {
  margin: 8px 0 3px;
  font-weight: 600;
  color: var(--ink);
}

.bubble :deep(.md-gap) {
  height: 6px;
}

.bubble--user :deep(strong) {
  color: #fff;
}

.bubble--user :deep(code) {
  background: rgba(255, 255, 255, 0.18);
  border-color: transparent;
  color: #fff;
}

/* 工具调用轨迹 */
.tools {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tool {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  background: var(--surface-2);
  font-family: inherit;
  font-size: 12px;
  color: var(--ink-2);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.tool:hover {
  border-color: var(--brand-line);
}

.tool.is-running {
  border-color: var(--brand-line);
  color: var(--brand);
}

.tool__dot {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  background: var(--faint);
  flex-shrink: 0;
}

.tool.is-running .tool__dot {
  background: var(--brand);
  animation: blink 1.2s ease-in-out infinite;
}

.tool.is-done .tool__dot {
  background: var(--brand);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}

.tool__state {
  font-size: 11px;
  color: var(--muted);
}

.tool__caret {
  display: inline-block;
  transition: transform 0.18s;
  color: var(--faint);
}

.tool__caret.open {
  transform: rotate(90deg);
}

.tool-detail {
  flex-basis: 100%;
}

.tool-detail__label {
  font-size: 11px;
  color: var(--muted);
  margin: 6px 0 3px;
}

.tool-detail pre {
  margin: 0;
  padding: 9px 11px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--r);
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 12px;
  line-height: 1.55;
  color: var(--ink-2);
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
}

/* 打字指示 */
.bubble--typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 14px 16px;
}

.bubble--typing span {
  width: 5px;
  height: 5px;
  border-radius: 1px;
  background: var(--brand-line);
  animation: typing 1.2s infinite ease-in-out;
}

.bubble--typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.bubble--typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

/* 快捷问题 */
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 16px 12px;
  flex-shrink: 0;
}

.quick__item {
  padding: 5px 12px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  font-family: inherit;
  font-size: 12.5px;
  color: var(--ink-2);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background-color 0.15s;
}

.quick__item:hover {
  border-color: var(--brand-line);
  background: var(--brand-soft);
  color: var(--brand);
}

/* 输入区 */
.composer {
  display: flex;
  gap: 10px;
  padding: 12px 16px 14px;
  border-top: 1px solid var(--line);
  background: var(--surface);
  flex-shrink: 0;
}

.composer .el-textarea {
  flex: 1;
}

.composer :deep(.el-textarea__inner) {
  border-radius: var(--r);
  font-size: 13.5px;
  padding: 8px 12px;
  resize: none;
}

.composer :deep(.el-button--primary) {
  height: auto;
  min-height: 44px;
  padding: 0 20px;
  align-self: stretch;
}

@media (max-width: 900px) {
  .ai-page {
    flex-direction: column;
  }

  .conv {
    width: 100%;
    max-height: 180px;
  }

  .conv__list {
    display: flex;
    gap: 6px;
    overflow-x: auto;
  }

  .conv__item {
    width: auto;
    white-space: nowrap;
    border-left: none;
    border-radius: var(--r);
  }

  .conv__item.active {
    border-left-color: transparent;
  }

  .msg-body {
    max-width: 86%;
  }
}
</style>
