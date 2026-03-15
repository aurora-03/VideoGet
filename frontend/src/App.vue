<template>
  <div class="min-h-screen relative bg-white">
    <!-- 主容器 -->
    <div class="relative z-10">
      <!-- 导航栏 -->
      <NavBar />

      <!-- 主要内容 -->
      <main>
        <!-- Hero + 下载区域 -->
        <HeroSection />

        <!-- 视频信息展示区域 -->
        <VideoInfoSection />

        <!-- 功能特性 -->
        <FeaturesSection />

        <!-- 定价/会员 -->
        <PricingSection />
      </main>

      <!-- 页脚 -->
      <Footer />
    </div>
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import VideoInfoSection from './components/VideoInfoSection.vue'
import FeaturesSection from './components/FeaturesSection.vue'
import PricingSection from './components/PricingSection.vue'
import Footer from './components/Footer.vue'
</script>
