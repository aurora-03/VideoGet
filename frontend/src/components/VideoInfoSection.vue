<template>
  <section class="py-12 bg-slate-50">
    <div class="max-w-5xl mx-auto px-4">
      <div v-if="showVideoInfo" class="bg-white rounded-2xl border border-slate-200 shadow-lg p-6 animate-slide-up">
        <div class="flex flex-col lg:flex-row gap-6">
          <!-- 缩略图 -->
          <div class="lg:w-96 flex-shrink-0">
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
            <h3 class="text-xl font-bold text-slate-800 mb-2 line-clamp-2">
              {{ videoInfo.title }}
            </h3>
            <div class="flex items-center gap-4 text-slate-500 text-sm mb-4">
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
              <label class="block text-slate-700 font-medium mb-3">选择画质</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="format in videoInfo.formats"
                  :key="format.quality"
                  @click="selectedFormat = format"
                  :class="[
                    'px-4 py-2 rounded-lg border text-sm font-medium transition-all',
                    selectedFormat.quality === format.quality
                      ? 'bg-blue-500 text-white border-blue-500'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600'
                  ]"
                >
                  <div class="font-semibold">{{ format.quality }}</div>
                  <div class="text-xs opacity-70">{{ format.size }}</div>
                </button>
              </div>
            </div>

            <!-- 下载按钮 -->
            <div class="flex gap-3">
              <button
                @click="startDownload"
                :disabled="downloading"
                class="flex items-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {{ downloading ? `下载中 ${downloadProgress}%` : '开始下载' }}
              </button>
            </div>

            <!-- 下载进度条 -->
            <div v-if="downloading" class="mt-4">
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 rounded-full transition-all duration-300" :style="{ width: downloadProgress + '%' }"></div>
              </div>
              <p class="text-slate-500 text-sm mt-2 text-center">{{ downloadStatus }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'

const showVideoInfo = ref(true)
const downloading = ref(false)
const downloadProgress = ref(0)
const downloadStatus = ref('')
const selectedFormat = ref({ quality: '1080p', size: '~500MB' })

const videoInfo = ref({
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
})

function startDownload() {
  downloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = '正在准备下载...'

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
</script>
