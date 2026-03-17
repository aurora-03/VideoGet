<template>
  <section class="text-center py-16 md:py-24 relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-white to-white pointer-events-none"></div>
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-100/30 blur-3xl rounded-full"></div>

    <div class="relative z-10 animate-fade-in">
      <!-- 标签 -->
      <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200 shadow-sm mb-8">
        <span class="w-2 h-2 rounded-full bg-green-400"></span>
        <span class="text-slate-600 text-sm font-medium">支持 1800+ 平台，永久免费使用</span>
      </div>

      <!-- 主标题 -->
      <h1 class="text-4xl md:text-6xl font-bold mb-6 leading-tight">
        <span class="text-slate-800">万能视频下载器</span>
        <span class="text-slate-800">，</span>
        <span class="text-blue-600">一键保存</span>
      </h1>

      <!-- 副标题 -->
      <p class="text-lg md:text-xl text-slate-500 max-w-3xl mx-auto mb-10 leading-relaxed">
        粘贴视频链接，智能解析，支持多种清晰度下载。YouTube、Bilibili、抖音、TikTok…<br>
        随时随地，想下就下
      </p>

      <div class="max-w-3xl mx-auto mb-6">
        <div class="flex items-center bg-white rounded-2xl border border-slate-200 shadow-lg shadow-slate-200/50 overflow-hidden">
          <div class="flex items-center gap-3 pl-5 py-1">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <input
            v-model="url"
            type="url"
            placeholder="粘贴视频链接"
            class="flex-1 py-4 px-2 text-slate-700 placeholder:text-slate-400 text-lg outline-none"
            @keyup.enter="fetchVideoInfo"
          />
          <button
            @click="fetchVideoInfo"
            :disabled="!url || loading"
            class="flex items-center gap-2 px-8 py-4 bg-blue-500 hover:bg-blue-600 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="!loading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <svg v-else class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? '解析中...' : '解析视频' }}
          </button>
        </div>
      </div>
      <div class="flex items-center justify-center gap-3 text-sm">
        <span class="text-slate-400">试试：</span>
        <button v-for="platform in quickPlatforms" :key="platform" @click="setExampleUrl(platform)" class="px-3 py-1.5 rounded-full border border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all">
          {{ platform }}
        </button>
      </div>
    </div>
    <div v-if="error" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4" @click.self="closeErrorModal">
      <div class="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-slate-200">
        <div class="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-800">解析失败</h3>
          <button
            @click="closeErrorModal"
            class="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="px-5 py-5">
          <p class="text-slate-600 leading-relaxed">{{ error }}</p>
        </div>
        <div class="px-5 pb-5 flex justify-end">
          <button
            @click="closeErrorModal"
            class="px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-medium transition-colors"
          >
            我知道了
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['video-info'])

const url = ref('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
const loading = ref(false)
const error = ref('')

const quickPlatforms = ['YouTube', 'Bilibili', 'Twitter/X']

function setExampleUrl(platform) {
  const examples = {
    'YouTube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'Bilibili': 'https://www.bilibili.com/video/BV1mAAmqEfP',
    'Twitter/X': 'https://twitter.com/user/status/123456789'
  }
  url.value = examples[platform] || ''
  error.value = ''
}

function closeErrorModal() {
  error.value = ''
}

function formatErrorMessage(rawError) {
  const message = String(rawError || '')
    .replace(/\x1B\[[0-?]*[ -/]*[@-~]/g, '')
    .replace(/^ERROR:\s*/i, '')
    .replace(/\s*\(caused by <[^>]+>\)\s*$/i, '')
    .trim()
  if (!message) return '解析视频失败，请检查链接是否正确'
  if (message.includes('Unable to download webpage') && message.includes('HTTP Error 404')) {
    return '链接不存在或已失效，请检查视频地址后重试'
  }
  if (/invalid url|not a valid url|\[generic\]/i.test(message)) {
    return '地址无效，请输入正确的视频链接'
  }
  return message
}

function normalizeInputUrl(rawValue) {
  const text = String(rawValue || '').trim()
  if (!text) return ''
  const matched = text.match(/https?:\/\/[^\s<>"'`]+/i)
  const candidate = matched ? matched[0] : text
  return candidate.replace(/[)\]}>，。！？、；：'"`]+$/g, '')
}

async function fetchVideoInfo() {
  const normalizedUrl = normalizeInputUrl(url.value)
  if (!normalizedUrl || !/^https?:\/\//i.test(normalizedUrl)) {
    error.value = '地址无效，请输入正确的视频链接'
    return
  }

  loading.value = true
  error.value = ''

  try {
    url.value = normalizedUrl
    const response = await axios.post('http://localhost:8000/api/video/info', {
      url: normalizedUrl
    })
    emit('video-info', response.data)
  } catch (err) {
    error.value = formatErrorMessage(err.response?.data?.detail)
  } finally {
    loading.value = false
  }
}
</script>
