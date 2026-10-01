<template>
  <nav class="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100">
    <div class="max-w-6xl mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center gap-2">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 11a1 1 0 11-2 0 1 1 0 012 0z" />
            </svg>
          </div>
          <span class="text-xl font-bold text-slate-800">SaveAny</span>
          <span class="hidden sm:inline px-2 py-1 bg-slate-100 text-slate-500 text-xs rounded-md">{{ t('万能视频下载') }}</span>
        </div>

        <!-- 导航链接 -->
        <div class="flex items-center gap-2 sm:gap-6">
          <a href="#features" class="hidden md:block text-slate-500 hover:text-blue-600 transition-colors font-medium">{{ t('功能特性') }}</a>
          <a href="#" class="hidden md:block text-slate-500 hover:text-blue-600 transition-colors font-medium">{{ t('支持平台') }}</a>
          <button type="button" @click="$emit('open-settings')" :aria-expanded="settingsOpen" aria-controls="model-settings-dialog" aria-haspopup="dialog" :class="settingsOpen ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-blue-600'" class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 7h16M4 17h16M8 4v6m8 4v6" /></svg>
            {{ t('模型设置') }}
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { t } from '../i18n.js'
defineProps({ settingsOpen: Boolean })
defineEmits(['open-settings'])
</script>
