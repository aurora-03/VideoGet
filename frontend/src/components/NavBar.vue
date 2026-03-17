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
          <span class="px-2 py-1 bg-slate-100 text-slate-500 text-xs rounded-md">万能视频下载</span>
        </div>

        <!-- 导航链接 -->
        <div class="hidden md:flex items-center gap-8">
          <a href="#features" class="text-slate-500 hover:text-blue-600 transition-colors font-medium">功能特性</a>
          <a href="#" class="text-slate-500 hover:text-blue-600 transition-colors font-medium">支持平台</a>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
</script>
