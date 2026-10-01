<template>
  <footer class="border-t border-slate-200 mt-12 bg-white">
    <div class="max-w-6xl mx-auto px-4 py-12">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
        <!-- 产品 -->
        <div>
          <h4 class="text-slate-800 font-semibold mb-4">{{ t('产品') }}</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('功能特性') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('支持平台') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('更新日志') }}</a></li>
          </ul>
        </div>

        <!-- 资源 -->
        <div>
          <h4 class="text-slate-800 font-semibold mb-4">{{ t('资源') }}</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('帮助中心') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('使用教程') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('常见问题') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('API 文档') }}</a></li>
          </ul>
        </div>

        <!-- 公司 -->
        <div>
          <h4 class="text-slate-800 font-semibold mb-4">{{ t('公司') }}</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('关于我们') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('加入我们') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('合作伙伴') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('联系我们') }}</a></li>
          </ul>
        </div>

        <!-- 法律 -->
        <div>
          <h4 class="text-slate-800 font-semibold mb-4">{{ t('法律') }}</h4>
          <ul class="space-y-2">
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('服务条款') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('隐私政策') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('版权声明') }}</a></li>
            <li><a href="#" class="text-slate-500 hover:text-blue-600 transition-colors">{{ t('免责声明') }}</a></li>
          </ul>
        </div>
      </div>

      <!-- 底部 -->
      <div class="border-t border-slate-200 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 11a1 1 0 11-2 0 1 1 0 012 0z" />
            </svg>
          </div>
          <span class="font-bold text-slate-800">SaveAny</span>
        </div>
        <p class="text-slate-500 text-sm text-center">
          {{ t('© 2024 SaveAny. 保留所有权利。') }}
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { t } from '../i18n.js'
</script>
