// URL-selected UI language; video titles and authors retain their source language.
export const locale = new URLSearchParams(window.location.search).get('lang') === 'en' ? 'en' : 'zh-CN'

const english = {
  '万能视频下载': 'Video downloader',
  '功能特性': 'Features',
  '支持平台': 'Supported platforms',
  '支持 1800+ 平台，永久免费使用': '1800+ platforms · Free to use',
  '万能视频下载器': 'Download any video',
  '，': ', ',
  '一键保存': 'in one click',
  '粘贴视频链接，智能解析，支持多种清晰度下载。YouTube、Bilibili、抖音、TikTok…': 'Paste a video link and choose your quality. YouTube, Bilibili, Douyin, TikTok…',
  '随时随地，想下就下': 'Save your videos, wherever you are.',
  '粘贴视频链接': 'Paste a video link',
  '解析中...': 'Parsing…',
  '解析视频': 'Parse video',
  '试试：': 'Try:',
  '解析失败': 'Unable to parse video',
  '我知道了': 'Got it',
  '解析视频失败，请检查链接是否正确': 'Could not parse this video. Please check the link.',
  '链接不存在或已失效，请检查视频地址后重试': 'This link is unavailable or has expired. Please check the video URL.',
  '地址无效，请输入正确的视频链接': 'Please enter a valid video URL.',
  '选择画质': 'Choose quality',
  '仅下载音频 (MP3)': 'Audio only (MP3)',
  '下载字幕': 'Download subtitles',
  '开始下载': 'Start download',
  '下载中 {progress}%': 'Downloading {progress}%',
  '正在准备下载...': 'Preparing your download…',
  '正在下载...': 'Downloading…',
  '下载完成！': 'Download complete!',
  '下载失败': 'Download failed',
  '最佳画质': 'Best quality',
  '未知': 'Unknown',
  '强大的功能，简单的操作': 'Powerful features. Simple to use.',
  '支持 1800+ 平台': '1800+ platforms',
  'YouTube、Bilibili、抖音、快手、TikTok、Instagram 等主流平台全覆盖': 'YouTube, Bilibili, Douyin, Kuaishou, TikTok, Instagram and more.',
  '4K 高清画质': '4K video quality',
  '支持最高 8K 画质下载，保留原始视频的每一帧细节': 'Download up to 8K and preserve the detail of the original video.',
  '极速下载': 'Fast downloads',
  '多线程加速下载，充分利用您的带宽，告别漫长等待': 'Multi-threaded downloads to make the most of your bandwidth.',
  '批量下载': 'Batch downloads',
  '一键下载整个播放列表、频道或合集，省时省力': 'Save entire playlists, channels or collections in one go.',
  'AI 视频总结': 'AI video summaries',
  '智能 AI 自动生成视频摘要，快速了解视频核心内容': 'Get an AI-generated summary of a video’s key ideas.',
  '字幕翻译': 'Subtitle translation',
  '自动下载并翻译字幕，支持多国语言互译': 'Download and translate subtitles across languages.',
  '产品': 'Product',
  '套餐价格': 'Pricing',
  '更新日志': 'Changelog',
  '资源': 'Resources',
  '帮助中心': 'Help center',
  '使用教程': 'Tutorials',
  '常见问题': 'FAQ',
  'API 文档': 'API documentation',
  '公司': 'Company',
  '关于我们': 'About us',
  '加入我们': 'Careers',
  '合作伙伴': 'Partners',
  '联系我们': 'Contact',
  '法律': 'Legal',
  '服务条款': 'Terms of service',
  '隐私政策': 'Privacy policy',
  '版权声明': 'Copyright',
  '免责声明': 'Disclaimer',
  '© 2024 SaveAny. 保留所有权利。': '© 2024 SaveAny. All rights reserved.',
  '该视频受密码保护，请在服务端配置 YTDLP_VIDEO_PASSWORD 后重试': 'This video requires a password. Configure YTDLP_VIDEO_PASSWORD on the server.',
  '该视频需要登录，请在服务端配置 YTDLP_COOKIE_FILE 后重试': 'This video requires login. Configure YTDLP_COOKIE_FILE on the server.',
  '所选画质当前不可用，请重新解析并选择其他画质': 'This quality is unavailable. Parse the video again and choose another quality.',
  '该视频没有可下载的非 DRM 格式': 'This video has no downloadable non-DRM format.',
  '暂不支持该链接格式，请确认是可访问的视频地址': 'This link format is unsupported. Please use an accessible video URL.',
  '解析失败，请检查链接是否正确': 'Could not parse this video. Please check the link.',
  '该抖音链接当前受风控，请使用抖音App分享链接后重试': 'Douyin is restricting this link. Please try a fresh app share link.',
  '该抖音视频当前受限，无法下载，请在抖音App打开并重新分享后重试': 'This Douyin video is restricted. Open it in the app and share it again.',
  'pending': 'Queued',
  'downloading': 'Downloading…',
}

export function t(text, values = {}) {
  const translated = locale === 'en' ? (english[text] ?? text) : text
  return translated.replace(/\{(\w+)\}/g, (match, key) => values[key] ?? match)
}

export function formatViews(value) {
  if (locale !== 'en') return value
  const match = String(value).match(/^([\d.]+)(万|亿)?次观看$/)
  if (!match) return value
  const count = Number(match[1]) * (match[2] === '亿' ? 100000000 : match[2] === '万' ? 10000 : 1)
  return `${new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(count)} views`
}
