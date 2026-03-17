<template>
  <section v-if="videoInfo" class="py-8 bg-slate-50">
    <div class="max-w-5xl mx-auto px-4">
      <div class="bg-white rounded-2xl border border-slate-200 shadow-lg p-6 animate-slide-up">
        <div class="flex flex-col lg:flex-row gap-6">
          <!-- 缩略图 -->
          <div class="lg:w-96 flex-shrink-0">
            <div class="relative rounded-xl overflow-hidden aspect-video bg-slate-100">
              <img
                :src="videoInfo.thumbnail"
                :alt="videoInfo.title"
                referrerpolicy="no-referrer"
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
                  @click="selectedFormat = format; $emit('select-format', format)"
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

            <!-- 附加选项 -->
            <div class="flex flex-wrap gap-4 mb-6">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="options.onlyAudio" @change="$emit('update-options', options)" class="w-4 h-4 rounded border-slate-300 bg-white text-blue-600 focus:ring-blue-500" />
                <span class="text-slate-600 text-sm">仅下载音频 (MP3)</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="options.subtitle" @change="$emit('update-options', options)" class="w-4 h-4 rounded border-slate-300 bg-white text-blue-600 focus:ring-blue-500" />
                <span class="text-slate-600 text-sm">下载字幕</span>
              </label>
            </div>

            <!-- 下载按钮 -->
            <div class="flex gap-3">
              <button
                @click="$emit('start-download')"
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
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  videoInfo: Object,
  downloading: Boolean,
  downloadProgress: Number,
  downloadStatus: String
})

const emit = defineEmits(['select-format', 'update-options', 'start-download'])

const selectedFormat = ref({ quality: '1080p', size: '~500MB' })
const options = reactive({
  onlyAudio: false,
  subtitle: false
})

watch(
  () => props.videoInfo,
  (info) => {
    const formats = info?.formats || []
    if (!formats.length) return
    selectedFormat.value = formats.find(f => f.quality === '1080p') || formats[0]
    emit('select-format', selectedFormat.value)
  },
  { immediate: true }
)
</script>
