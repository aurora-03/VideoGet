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

      <!-- URL 输入区域 -->
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
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {{ loading ? '解析中...' : '解析视频' }}
          </button>
        </div>
      </div>

      <!-- 快捷标签 -->
      <div class="flex items-center justify-center gap-3 text-sm">
        <span class="text-slate-400">试试：</span>
        <button v-for="platform in quickPlatforms" :key="platform" @click="setExampleUrl(platform)" class="px-3 py-1.5 rounded-full border border-slate-200 text-slate-500 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all">
          {{ platform }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const url = ref('https://www.bilibili.com/video/BV1mAAmqEfP')
const loading = ref(false)

const quickPlatforms = ['YouTube', 'Bilibili', 'Twitter/X']

function setExampleUrl(platform) {
  const examples = {
    'YouTube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'Bilibili': 'https://www.bilibili.com/video/BV1mAAmqEfP',
    'Twitter/X': 'https://twitter.com/user/status/123456789'
  }
  url.value = examples[platform] || ''
}

function fetchVideoInfo() {
  if (!url.value) return
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 1500)
}
</script>
