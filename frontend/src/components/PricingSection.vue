<template>
  <section id="pricing" class="py-16 md:py-24 bg-slate-50">
    <div class="max-w-6xl mx-auto px-4">
      <div class="text-center mb-12">
        <h2 class="text-3xl md:text-4xl font-bold text-slate-800 mb-4">套餐价格</h2>
        <p class="text-slate-500 text-lg max-w-2xl mx-auto">
          选择适合您的方案，免费版也能正常使用
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        <!-- 免费版 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 class="text-xl font-bold text-slate-800 mb-2">免费版</h3>
          <div class="mb-6">
            <span class="text-4xl font-bold text-slate-800">¥0</span>
            <span class="text-slate-500">/月</span>
          </div>
          <ul class="space-y-3 mb-8">
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              每天 5 次下载
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              最高 720p 画质
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              单视频下载
            </li>
          </ul>
          <button class="w-full py-3 rounded-xl border border-slate-200 text-slate-700 font-medium hover:bg-slate-50 transition-colors">
            免费使用
          </button>
        </div>

        <!-- 专业版 - 推荐 -->
        <div class="bg-white rounded-2xl border-2 border-blue-500 p-6 relative shadow-lg shadow-blue-100/50">
          <div class="absolute -top-3 left-1/2 -translate-x-1/2">
            <span class="px-4 py-1 rounded-full bg-blue-500 text-white text-sm font-medium">
              最受欢迎
            </span>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-2">专业版</h3>
          <div class="mb-6">
            <span class="text-4xl font-bold text-blue-600">¥19</span>
            <span class="text-slate-500">/月</span>
            <span class="block text-sm text-green-600 mt-1">原价 ¥39，立省 ¥20</span>
          </div>
          <ul class="space-y-3 mb-8">
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span class="font-medium">无限下载次数</span>
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span class="font-medium">最高 4K 画质</span>
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span class="font-medium">批量/播放列表下载</span>
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              AI 视频总结 (100 次/月)
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              字幕翻译 (50 次/月)
            </li>
          </ul>
          <button class="w-full py-3 rounded-xl bg-blue-500 hover:bg-blue-600 text-white font-medium transition-colors">
            立即开通
          </button>
        </div>

        <!-- 企业版 -->
        <div class="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 class="text-xl font-bold text-slate-800 mb-2">企业版</h3>
          <div class="mb-6">
            <span class="text-4xl font-bold text-slate-800">¥99</span>
            <span class="text-slate-500">/月</span>
          </div>
          <ul class="space-y-3 mb-8">
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              专业版所有功能
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              最高 8K 画质
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              无限 AI 总结
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              无限字幕翻译
            </li>
            <li class="flex items-center gap-3 text-slate-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              API 接入支持
            </li>
          </ul>
          <button class="w-full py-3 rounded-xl border border-slate-200 text-slate-700 font-medium hover:bg-slate-50 transition-colors">
            联系销售
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
</script>
