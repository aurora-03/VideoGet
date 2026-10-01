<template>
  <section class="py-8 bg-slate-50">
    <div class="max-w-5xl mx-auto px-4">
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 class="text-xl font-bold text-slate-800">{{ t('字幕与 AI 助手') }}</h2>
        <p class="text-sm text-slate-500 mt-2">{{ t('提取已有字幕，或将语音转为文字，再翻译或生成总结。') }}</p>

        <div class="flex flex-wrap gap-4 mt-5">
          <label class="text-sm text-slate-600">
            {{ t('原文语言') }}
            <select v-model="sourceLanguage" :disabled="busy" class="block mt-1 border border-slate-200 rounded-lg px-3 py-2 bg-white">
              <option value="auto">{{ t('自动检测') }}</option>
              <option v-for="language in languages" :key="language.code" :value="language.code">{{ t(language.label) }}</option>
            </select>
          </label>
          <label class="text-sm text-slate-600">
            {{ t('翻译 / 总结语言') }}
            <select v-model="targetLanguage" :disabled="busy" class="block mt-1 border border-slate-200 rounded-lg px-3 py-2 bg-white">
              <option v-for="language in languages" :key="language.code" :value="language.code">{{ t(language.label) }}</option>
            </select>
          </label>
          <label class="flex items-center gap-2 text-sm text-slate-600">
            <input v-model="allowTranscription" type="checkbox" :disabled="busy || !capabilities.speech_ready" class="rounded text-blue-600" />
            {{ t('无字幕时使用语音转文字') }}
          </label>
        </div>

        <div class="flex flex-wrap gap-3 mt-5">
          <button :disabled="busy" @click="start('subtitles')" class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">{{ t('提取字幕') }}</button>
          <button :disabled="busy || !capabilities.speech_ready" @click="start('transcribe')" class="px-4 py-2 rounded-lg border border-blue-200 text-blue-700 hover:bg-blue-50 disabled:opacity-50">{{ t('语音转文字') }}</button>
          <button :disabled="busy || !capabilities.translation_ready" @click="start('translate')" class="px-4 py-2 rounded-lg border border-blue-200 text-blue-700 hover:bg-blue-50 disabled:opacity-50">{{ t('翻译字幕') }}</button>
          <button :disabled="busy || !capabilities.summary_ready" @click="start('summarize')" class="px-4 py-2 rounded-lg border border-blue-200 text-blue-700 hover:bg-blue-50 disabled:opacity-50">{{ t('生成 AI 总结') }}</button>
        </div>

        <p v-if="!capabilities.translation_ready" class="mt-3 text-sm text-amber-700">{{ t('字幕翻译模型未配置，翻译暂不可用。') }}</p>
        <p v-if="!capabilities.summary_ready" class="mt-2 text-sm text-amber-700">{{ t('总结模型未配置，总结暂不可用。') }}</p>
        <p v-if="!capabilities.speech_ready" class="mt-2 text-sm text-amber-700">{{ t('语音转文字服务未配置，可先提取视频已有字幕。') }}</p>
        <p class="mt-2 text-xs text-slate-500">{{ t('使用云端模型时，文本或音频会发送至服务端配置的模型服务。') }}</p>

        <div v-if="busy" class="mt-5" role="status" aria-live="polite">
          <div class="h-2 bg-slate-100 rounded-full overflow-hidden"><div class="h-full bg-blue-500 transition-all" :style="{ width: progress + '%' }"></div></div>
          <p class="mt-2 text-sm text-slate-600">{{ stageLabel }} · {{ progress }}%</p>
        </div>
        <p v-if="error" role="alert" class="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">{{ t(error) }}</p>

        <div v-if="result" class="mt-6 space-y-5">
          <div class="flex flex-wrap items-center gap-3">
            <span class="text-xs bg-blue-50 text-blue-700 rounded-full px-3 py-1">{{ t(sourceLabels[result.source] || result.source) }} · {{ result.language }}</span>
            <a v-for="file in result.files || []" :key="file.filename" :href="fileUrl(file.download_url)" :download="file.filename" class="text-sm text-blue-600 hover:underline">{{ t(fileLabels[file.kind] || file.kind) }}{{ file.language ? ` (${file.language})` : '' }}</a>
          </div>
          <div v-if="result.summary" class="rounded-xl bg-blue-50 p-4">
            <h3 class="font-semibold text-slate-800 mb-2">{{ t('AI 视频总结') }}</h3>
            <p class="whitespace-pre-wrap text-slate-700 leading-relaxed text-sm">{{ result.summary }}</p>
            <p class="text-xs text-slate-500 mt-3">{{ t('总结基于字幕或语音转写，不包含未描述的画面信息。') }}</p>
          </div>
          <div v-if="result.translated_segments?.length">
            <h3 class="font-semibold text-slate-800 mb-2">{{ t('翻译字幕') }} · {{ result.translation_language }}</h3>
            <div class="max-h-72 overflow-y-auto border border-slate-200 rounded-xl p-4 space-y-3">
              <p v-for="(segment, index) in result.translated_segments" :key="index" class="text-sm text-slate-700"><span class="text-slate-400 font-mono mr-2">{{ time(segment.start) }}</span>{{ segment.text }}</p>
            </div>
          </div>
          <div>
            <h3 class="font-semibold text-slate-800 mb-2">{{ t('原文字幕 / 转写') }}</h3>
            <div class="max-h-72 overflow-y-auto border border-slate-200 rounded-xl p-4 space-y-3">
              <p v-for="(segment, index) in result.segments" :key="index" class="text-sm text-slate-700"><span class="text-slate-400 font-mono mr-2">{{ time(segment.start) }}</span>{{ segment.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { api, fileUrl } from '../api.js'
import { locale, t } from '../i18n.js'

const props = defineProps({ url: { type: String, required: true } })
const languages = [{ code: 'zh', label: '简体中文' }, { code: 'en', label: '英语' },
  { code: 'ja', label: '日语' }, { code: 'ko', label: '韩语' }, { code: 'es', label: '西班牙语' },
  { code: 'fr', label: '法语' }, { code: 'de', label: '德语' }]
const sourceLabels = { subtitles: '平台字幕', automatic_subtitles: '平台自动字幕', transcription: '语音转写' }
const fileLabels = { subtitles: '下载原文 SRT', transcript: '下载原文 TXT', translated_subtitles: '下载翻译 SRT', summary: '下载总结 TXT' }
const stages = { extracting_subtitles: '正在提取字幕...', audio_download: '正在获取音频...',
  transcribing: '正在语音转文字...', translating: '正在翻译字幕...', summarizing: '正在生成总结...' }
const capabilities = ref({ text_ready: false, translation_ready: false, summary_ready: false, speech_ready: false })
const sourceLanguage = ref('auto')
const targetLanguage = ref(locale === 'en' ? 'en' : 'zh')
const allowTranscription = ref(false)
const busy = ref(false)
const progress = ref(0)
const stage = ref('extracting_subtitles')
const error = ref('')
const result = ref(null)
const sourceTaskId = ref(null)
const stageLabel = computed(() => t(stages[stage.value] || '正在处理...'))
let generation = 0
let timer
let controller

function stop() {
  generation++
  clearTimeout(timer)
  controller?.abort()
  busy.value = false
}

watch(() => props.url, () => {
  stop()
  result.value = null
  sourceTaskId.value = null
  error.value = ''
})
watch(sourceLanguage, () => { sourceTaskId.value = null })
onUnmounted(stop)
onMounted(async () => {
  try { capabilities.value = (await api.get('/ai/capabilities')).data }
  catch { error.value = '无法连接后端，请确认服务已启动' }
})

function time(seconds) {
  return new Date(Math.floor(seconds) * 1000).toISOString().slice(11, 19)
}

async function start(mode) {
  stop()
  const version = generation
  controller = new AbortController()
  busy.value = true
  progress.value = 0
  stage.value = 'extracting_subtitles'
  error.value = ''
  try {
    const response = await api.post('/video/analyze', {
      url: props.url, mode, source_language: sourceLanguage.value, target_language: targetLanguage.value,
      source_task_id: ['translate', 'summarize'].includes(mode) ? sourceTaskId.value : null,
      allow_transcription: allowTranscription.value
    }, { signal: controller.signal })
    const taskId = response.data.task_id
    let failures = 0
    async function poll() {
      try {
        const task = (await api.get(`/task/${taskId}`, { signal: controller.signal })).data
        if (version !== generation) return
        failures = 0
        progress.value = task.progress
        stage.value = task.stage
        if (task.status === 'completed' || task.status === 'error') {
          busy.value = false
          if (task.result?.segments?.length) { result.value = task.result; sourceTaskId.value = taskId }
          if (task.status === 'error') error.value = task.error || '分析失败，请重试'
          return
        }
      } catch (failure) {
        if (version !== generation) return
        if (++failures >= 3) { busy.value = false; error.value = '任务状态获取失败，请重试'; return }
      }
      if (version === generation) timer = setTimeout(poll, 1000)
    }
    await poll()
  } catch (failure) {
    if (version !== generation) return
    busy.value = false
    error.value = failure.response?.data?.detail || '分析失败，请重试'
  }
}
</script>
