import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { locale, t } from './i18n.js'

document.documentElement.lang = locale
document.title = `VideoGet - ${t('万能视频下载器')}`

createApp(App).mount('#app')
