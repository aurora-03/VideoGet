<template>
  <dialog ref="dialog" id="model-settings-dialog" aria-labelledby="model-settings-title" class="settings-dialog" @cancel.prevent="close" @close="emit('update:open', false)" @click="onBackdropClick">
    <div class="flex items-start justify-between gap-4 px-6 py-5 border-b border-slate-100 bg-white">
      <div>
        <h2 id="model-settings-title" class="text-xl font-semibold text-slate-800">{{ t('模型设置') }}</h2>
        <p class="text-sm text-slate-500 mt-1">{{ t('配置当前浏览器使用的模型服务，保存后立即生效。') }}</p>
      </div>
      <button type="button" @click="close" :aria-label="t('关闭')" class="p-2 -mr-2 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-width="2" d="m6 6 12 12M18 6 6 18" /></svg>
      </button>
    </div>
      <form @submit.prevent="save" class="settings-form space-y-5 p-6" autocomplete="off">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label class="text-sm text-slate-600">{{ t('文本服务') }}
            <select v-model="form.provider" class="setting-input"><option value="custom">{{ t('自定义云端') }}</option><option value="openai">OpenAI</option><option value="ollama">{{ t('本地 Ollama') }}</option></select>
          </label>
          <label v-if="form.provider !== 'ollama'" class="text-sm text-slate-600">{{ t('接口协议') }}
            <select v-model="form.protocol" class="setting-input"><option value="openai">OpenAI Chat Completions</option><option value="anthropic">Anthropic Messages</option></select>
          </label>
          <label class="text-sm text-slate-600 md:col-span-2">{{ t('云端 / 本地服务地址') }}
            <input v-model="form.base_url" type="url" class="setting-input" placeholder="https://your-service/v1" />
          </label>
          <label v-if="form.provider !== 'ollama'" class="text-sm text-slate-600 md:col-span-2">API Key
            <input v-model="form.api_key" type="password" autocomplete="new-password" class="setting-input" :placeholder="savedKey ? t('已配置，留空保留') : t('输入 API Key')" />
            <span class="text-xs text-slate-500">{{ t('更换服务地址或协议后，需重新填写密钥。') }}</span>
            <span class="flex items-center gap-2 mt-2 text-xs"><input v-model="form.clear_api_key" type="checkbox" />{{ t('清除已保存密钥') }}</span>
          </label>
          <label class="text-sm text-slate-600">{{ t('字幕翻译模型') }}<input v-model="form.translation_model" class="setting-input" placeholder="model-name" /></label>
          <label class="text-sm text-slate-600">{{ t('AI 总结模型') }}<input v-model="form.summary_model" class="setting-input" placeholder="model-name" /></label>
          <label class="text-sm text-slate-600">{{ t('输出 Token 上限') }}<input v-model.number="form.max_output_tokens" type="number" min="256" max="32768" class="setting-input" /></label>
          <label class="text-sm text-slate-600">{{ t('语音转文字模式') }}<select v-model="form.asr_backend" class="setting-input"><option value="api">{{ t('云端语音服务') }}</option><option value="local">{{ t('本地 Whisper') }}</option></select></label>
          <label class="text-sm text-slate-600">{{ t('语音模型') }}<input v-model="form.asr_model" class="setting-input" :placeholder="form.asr_backend === 'local' ? 'base / small' : 'whisper-1'" /></label>
          <template v-if="form.asr_backend === 'api'">
            <label class="text-sm text-slate-600">{{ t('独立语音服务地址（可选）') }}<input v-model="form.asr_base_url" type="url" class="setting-input" placeholder="https://your-speech-service/v1" /></label>
            <label class="text-sm text-slate-600 md:col-span-2">{{ t('独立语音 API Key（可选）') }}
              <input v-model="form.asr_api_key" type="password" autocomplete="new-password" class="setting-input" :placeholder="savedSpeechKey ? t('已配置，留空保留') : t('与共享地址一致时可复用共享密钥')" />
              <span class="flex items-center gap-2 mt-2 text-xs"><input v-model="form.clear_asr_api_key" type="checkbox" />{{ t('清除语音密钥') }}</span>
            </label>
            <p v-if="form.protocol === 'anthropic'" class="text-sm text-amber-700 md:col-span-2">{{ t('Anthropic 文本入口需要另配语音服务，或选择本地 Whisper。') }}</p>
          </template>
        </div>
        <p class="text-xs text-slate-500">{{ t('密钥仅保存在服务端当前会话，不回显、不写入浏览器存储；会话两小时后或后端重启后失效。') }}</p>
        <div class="flex flex-wrap items-center gap-3 pt-4 border-t border-slate-200"><button :disabled="saving || loading" type="submit" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50">{{ t(saving ? '正在保存...' : '保存模型配置') }}</button><span v-if="success" role="status" class="text-sm text-green-700">{{ t('配置已生效') }}</span></div>
        <p v-if="error" role="alert" class="text-sm text-red-700">{{ t(error) }}</p>
      </form>
  </dialog>
</template>

<script setup>
import { onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { api } from '../api.js'
import { t } from '../i18n.js'
const props = defineProps({ open: Boolean })
const emit = defineEmits(['updated', 'update:open'])
const dialog = ref(null)
let previousOverflow = null
function restoreScroll() {
  if (previousOverflow !== null) document.body.style.overflow = previousOverflow
  previousOverflow = null
}
function close() { emit('update:open', false) }
function onBackdropClick(event) {
  if (event.target !== dialog.value) return
  const bounds = dialog.value.getBoundingClientRect()
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) close()
}
watch(() => props.open, (open) => {
  if (open) {
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialog.value.showModal()
  } else {
    dialog.value.close()
    restoreScroll()
  }
}, { flush: 'post' })
onBeforeUnmount(restoreScroll)
const form = reactive({ provider: 'custom', protocol: 'openai', base_url: '', api_key: '',
  translation_model: '', summary_model: '', max_output_tokens: 16384, asr_backend: 'api',
  asr_base_url: '', asr_model: '', asr_api_key: '', clear_api_key: false, clear_asr_api_key: false })
const savedKey = ref(false)
const savedSpeechKey = ref(false)
const saving = ref(false)
const loading = ref(true)
const success = ref(false)
const error = ref('')
function apply(settings) {
  for (const key of Object.keys(form)) if (key in settings) form[key] = settings[key]
  form.api_key = ''
  form.asr_api_key = ''
  form.clear_api_key = false
  form.clear_asr_api_key = false
  savedKey.value = settings.api_key_configured
  savedSpeechKey.value = settings.asr_api_key_configured
}
onMounted(async () => {
  try { apply((await api.get('/ai/settings')).data); emit('updated') }
  catch { error.value = '模型配置加载失败，请刷新页面' }
  finally { loading.value = false }
})
async function save() {
  saving.value = true
  success.value = false
  error.value = ''
  try {
    const response = await api.post('/ai/settings', { ...form })
    apply(response.data.settings)
    success.value = true
    emit('updated')
  } catch (failure) { error.value = typeof failure.response?.data?.detail === 'string' ? failure.response.data.detail : '模型配置保存失败，请重试' }
  finally { form.api_key = ''; form.asr_api_key = ''; saving.value = false }
}
</script>

<style scoped>
.settings-dialog { width: min(720px, calc(100vw - 32px)); max-height: calc(100dvh - 48px); padding: 0; border: 1px solid #e2e8f0; border-radius: 20px; background: #f8fafc; box-shadow: 0 24px 80px rgb(15 23 42 / .2); }
.settings-dialog[open] { display: flex; flex-direction: column; }
.settings-dialog::backdrop { background: rgb(15 23 42 / .35); backdrop-filter: blur(4px); }
.settings-form { overflow-y: auto; min-height: 0; }
.setting-input { display: block; width: 100%; margin-top: .5rem; border: 1px solid #e2e8f0; border-radius: .625rem; padding: .625rem .75rem; background: white; color: #334155; transition: border-color .15s, box-shadow .15s; }
.setting-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgb(59 130 246 / .12); }
</style>
