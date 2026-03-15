<template>
  <section id="download" class="py-8 md:py-12">
    <div class="glass-card p-6 md:p-8 animate-slide-up">
      <!-- URL 输入区域 -->
      <div class="mb-6">
        <label class="block text-text-primary font-medium mb-3">
          粘贴视频链接
        </label>
        <div class="flex flex-col sm:flex-row gap-3">
          <div class="flex-1 relative">
            <input
              v-model="url"
              type="url"
              placeholder="粘贴视频链接，例如：https://www.youtube.com/watch?v=..."
              class="input-field pr-12"
              @keyup.enter="fetchVideoInfo"
            />
            <button
              v-if="url"
              @click="clearUrl"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <button
            @click="fetchVideoInfo"
            :disabled="!url || loading"
            class="btn-primary min-w-[120px]"
          >
            <template v-if="loading">
              <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              解析中...
            </template>
            <template v-else>
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              解析视频
            </template>
          </button>
        </div>
        <p class="text-text-muted text-sm mt-2">
          支持 YouTube、Bilibili、抖音、快手、TikTok、Instagram 等 1000+ 平台
        </p>
      </div>

      <!-- 视频信息卡片 -->
      <div v-if="videoInfo" class="animate-scale-in">
        <div class="border-t border-border-light pt-6">
          <div class="flex flex-col lg:flex-row gap-6">
            <!-- 缩略图 -->
            <div class="lg:w-80 flex-shrink-0">
              <div class="relative rounded-xl overflow-hidden aspect-video bg-slate-100">
                <img
                  :src="videoInfo.thumbnail"
                  :alt="videoInfo.title"
                  class="w-full h-full object-cover"
                />
                <div class="absolute bottom-2 right-2 px-2 py-1 rounded bg-black/80 text-white text-sm">
                  {{ videoInfo.duration }}
                </div>
              </div>
            </div>

            <!-- 视频详情 -->
            <div class="flex-1">
              <h3 class="text-xl font-bold text-text-primary mb-2 line-clamp-2">
                {{ videoInfo.title }}
              </h3>
              <div class="flex items-center gap-4 text-text-muted text-sm mb-4">
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {{ videoInfo.author }}
                </span>
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  {{ videoInfo.views }}
                </span>
              </div>

              <!-- 格式选择 -->
              <div class="mb-4">
                <label class="block text-text-primary font-medium mb-3">选择画质</label>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    v-for="format in videoInfo.formats"
                    :key="format.quality"
                    @click="selectedFormat = format"
                    :class="[
                      'px-4 py-2 rounded-lg border text-sm font-medium transition-all',
                      selectedFormat.quality === format.quality
                        ? 'bg-primary-100 border-primary-500 text-primary-700'
                        : 'bg-white border-border-light text-text-secondary hover:border-primary-300'
                    ]"
                  >
                    <div class="font-semibold">{{ format.quality }}</div>
                    <div class="text-xs opacity-70">{{ format.size }}</div>
                  </button>
                </div>
              </div>

              <!-- 附加选项 -->
              <div class="flex flex-wrap gap-4 mb-6">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" v-model="options.onlyAudio" class="w-4 h-4 rounded border-border-light bg-white text-primary-600 focus:ring-primary-500" />
                  <span class="text-text-secondary text-sm">仅下载音频 (MP3)</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" v-model="options.subtitle" class="w-4 h-4 rounded border-border-light bg-white text-primary-600 focus:ring-primary-500" />
                  <span class="text-text-secondary text-sm">下载字幕</span>
                </label>
              </div>

              <!-- 下载按钮 -->
              <div class="flex flex-col sm:flex-row gap-3">
                <button
                  @click="startDownload"
                  :disabled="downloading"
                  class="btn-primary flex-1"
                >
                  <template v-if="downloading">
                    <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    下载中 {{ downloadProgress }}%
                  </template>
                  <template v-else>
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    开始下载
                  </template>
                </button>
                <button class="btn-secondary" @click="generateSummary">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  AI 总结
                  <span class="badge badge-primary ml-1">Pro</span>
                </button>
              </div>

              <!-- 下载进度条 -->
              <div v-if="downloading" class="mt-4">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: downloadProgress + '%' }"></div>
                </div>
                <p class="text-text-muted text-sm mt-2 text-center">{{ downloadStatus }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="mt-4 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ error }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive } from 'vue'

const url = ref('')
const loading = ref(false)
const downloading = ref(false)
const downloadProgress = ref(0)
const downloadStatus = ref('')
const videoInfo = ref(null)
const error = ref('')
const selectedFormat = ref({ quality: '1080p', size: '~500MB' })
const options = reactive({
  onlyAudio: false,
  subtitle: false
})

function clearUrl() {
  url.value = ''
  videoInfo.value = null
  error.value = ''
}

async function fetchVideoInfo() {
  if (!url.value) return

  loading.value = true
  error.value = ''

  // 模拟 API 调用
  setTimeout(() => {
    videoInfo.value = {
      title: '【4K】这是一个示例视频标题，展示视频下载器的功能和界面设计',
      author: '鱼皮编程',
      views: '128.5万次观看',
      duration: '12:34',
      thumbnail: 'https://picsum.photos/800/450?random=1',
      formats: [
        { quality: '4K', size: '~2.5GB' },
        { quality: '1080p', size: '~500MB' },
        { quality: '720p', size: '~250MB' },
        { quality: '480p', size: '~100MB' }
      ]
    }
    selectedFormat.value = videoInfo.value.formats[1]
    loading.value = false
  }, 1500)
}

async function startDownload() {
  downloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = '正在准备下载...'

  // 模拟下载进度
  const interval = setInterval(() => {
    downloadProgress.value += Math.random() * 15
    if (downloadProgress.value >= 100) {
      downloadProgress.value = 100
      downloadStatus.value = '下载完成！'
      clearInterval(interval)
      setTimeout(() => {
        downloading.value = false
      }, 2000)
    } else if (downloadProgress.value < 30) {
      downloadStatus.value = '正在连接服务器...'
    } else if (downloadProgress.value < 60) {
      downloadStatus.value = '正在下载视频文件...'
    } else {
      downloadStatus.value = '正在合并视频和音频...'
    }
  }, 500)
}

function generateSummary() {
  alert('这是 Pro 会员功能，升级会员即可使用 AI 视频总结！')
}
</script>
