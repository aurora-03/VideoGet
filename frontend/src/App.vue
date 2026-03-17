<template>
  <div class="min-h-screen relative bg-white">
    <!-- 主容器 -->
    <div class="relative z-10">
      <!-- 导航栏 -->
      <NavBar />

      <!-- 主要内容 -->
      <main>
        <!-- Hero + 下载区域 -->
        <HeroSection @video-info="onVideoInfo" />

        <!-- 视频信息展示区域 -->
        <div v-if="videoInfo" ref="videoInfoSectionRef">
          <VideoInfoSection
            :video-info="videoInfo"
            :downloading="downloading"
            :download-progress="downloadProgress"
            :download-status="downloadStatus"
            @select-format="onSelectFormat"
            @update-options="onUpdateOptions"
            @start-download="onStartDownload"
          />
        </div>

        <!-- 功能特性 -->
        <FeaturesSection />
      </main>

      <!-- 页脚 -->
      <Footer />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import axios from 'axios'
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import VideoInfoSection from './components/VideoInfoSection.vue'
import FeaturesSection from './components/FeaturesSection.vue'
import Footer from './components/Footer.vue'

const videoInfo = ref(null)
const downloading = ref(false)
const downloadProgress = ref(0)
const downloadStatus = ref('')
const selectedFormat = ref({ quality: '1080p', size: '~500MB' })
const videoInfoSectionRef = ref(null)
const options = reactive({
  onlyAudio: false,
  subtitle: false,
  currentUrl: ''
})

function scrollToVideoInfoSection() {
  const sectionEl = videoInfoSectionRef.value
  if (!sectionEl) return
  const sectionTop = sectionEl.getBoundingClientRect().top + window.scrollY
  const offset = Math.min(220, Math.round(window.innerHeight * 0.25))
  const targetTop = Math.max(0, sectionTop - offset)
  window.scrollTo({ top: targetTop, behavior: 'smooth' })
}

function onVideoInfo(info) {
  videoInfo.value = info
  selectedFormat.value = info.formats.find(f => f.quality === '1080p') || info.formats[0]
  options.currentUrl = info.url || ''
  nextTick(() => {
    scrollToVideoInfoSection()
  })
}

function onSelectFormat(format) {
  selectedFormat.value = format
}

function onUpdateOptions(opts) {
  Object.assign(options, opts)
}

async function onStartDownload() {
  if (!videoInfo.value) return

  downloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = '正在准备下载...'

  try {
    const response = await axios.post('http://localhost:8000/api/download', {
      url: options.currentUrl,
      quality: selectedFormat.value.quality,
      only_audio: options.onlyAudio,
      download_subtitle: options.subtitle
    })

    const taskId = response.data.task_id

    // 轮询任务状态
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await axios.get(`http://localhost:8000/api/task/${taskId}`)
        const task = statusResponse.data

        downloadProgress.value = task.progress
        downloadStatus.value = task.status === 'downloading' ? '正在下载...' :
                              task.status === 'completed' ? '下载完成！' :
                              task.status === 'error' ? '下载失败' : task.status

        if (task.status === 'completed') {
          clearInterval(pollInterval)
          downloadStatus.value = '下载完成！'
          setTimeout(() => {
            downloading.value = false
            // 触发下载
            if (task.download_url) {
              window.open(`http://localhost:8000${task.download_url}`, '_blank')
            }
          }, 1500)
        } else if (task.status === 'error') {
          clearInterval(pollInterval)
          downloadStatus.value = task.error || '下载失败'
          setTimeout(() => {
            downloading.value = false
          }, 2000)
        }
      } catch (err) {
        console.error('Poll error:', err)
      }
    }, 1000)

  } catch (err) {
    console.error('Download error:', err)
    downloadStatus.value = err.response?.data?.detail || '下载失败'
    setTimeout(() => {
      downloading.value = false
    }, 2000)
  }
}
</script>
