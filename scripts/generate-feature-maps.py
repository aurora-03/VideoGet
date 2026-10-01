"""Regenerate bilingual README feature maps as SVG and PNG."""

from html import escape
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'images'
CONTENT = {
    'en': {
        'title': 'VideoGet · Feature mind map',
        'subtitle': 'Current capabilities and planned work · built from the implementation',
        'center': 'Video downloader',
        'current': 'Implemented capability', 'planned': 'Planned / not implemented',
        'cards': [
            ('Video information', ['Paste a URL or share text', 'Title, author, cover and duration', 'Real quality options / best quality']),
            ('Download media', ['Video with available audio', 'Extract MP3 using FFmpeg', 'Save available subtitles on server']),
            ('Task tracking', ['Background download jobs', 'Progress polling and error messages', 'Fetch the completed media file']),
            ('Platform adapters', ['YouTube, Bilibili, TikTok and more', 'Douyin / Kuaishou public share pages', 'Vimeo player-URL fallback']),
            ('Access and delivery', ['Optional authorized cookie file', 'Known video password support', 'Encoded filenames and final paths']),
            ('Planned features', ['AI summaries and subtitle translation', 'Batch workflow and download history', 'Accounts, payments and task storage']),
        ],
        'note': 'Limits: no DRM downloads · galleries unsupported · subtitle delivery is server-side · task state is in memory',
    },
    'zh-CN': {
        'title': 'VideoGet · 功能思维导图',
        'subtitle': '根据当前实现整理：现有能力与待开发功能',
        'center': '网页视频下载器',
        'current': '已实现能力', 'planned': '规划中 / 尚未实现',
        'cards': [
            ('视频信息解析', ['粘贴视频链接或分享文本', '标题、作者、封面和视频时长', '真实画质选项 / 最佳画质']),
            ('媒体下载', ['下载视频及可用音轨', '通过 FFmpeg 提取 MP3', '将可用字幕保存到服务器']),
            ('任务跟踪', ['创建后台下载任务', '轮询进度并显示错误提示', '获取下载完成的媒体文件']),
            ('平台适配', ['YouTube、B站、TikTok 等平台', '抖音 / 快手公开分享页解析', 'Vimeo 播放器地址回退']),
            ('访问与文件交付', ['可配置已有授权的 Cookie 文件', '支持提供已知视频密码', '文件名编码与转换后路径校验']),
            ('待开发功能', ['AI 总结与字幕翻译', '完整批量流程与下载历史', '账户、支付与任务持久化']),
        ],
        'note': '限制：不支持 DRM 下载及图文作品 · 字幕仅保存在服务端 · 任务状态暂存内存',
    },
}


def generate(language, content):
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 960" width="1480" height="960" role="img">')
    lines.append(f'<title>{escape(content["title"])}</title>')
    lines.append('<style>text{font-family:"Helvetica Neue",Helvetica,Arial,"PingFang SC","Microsoft YaHei",sans-serif}</style>')
    lines.append('<defs>')
    for name, color in [('current', '#2563eb'), ('planned', '#ea580c')]:
        lines.append(f'<marker id="arrow-{name}" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto"><polygon points="0 0,8 3.5,0 7" fill="{color}"/></marker>')
    lines.append('</defs>')
    lines.append('<rect width="1480" height="960" fill="#ffffff"/>')
    lines.append(f'<text x="40" y="48" font-size="30" font-weight="700" fill="#111827">{escape(content["title"])}</text>')
    lines.append(f'<text x="40" y="80" font-size="18" fill="#6b7280">{escape(content["subtitle"])}</text>')
    positions = [(40, 120), (40, 390), (40, 660), (1020, 120), (1020, 390), (1020, 660)]
    # Curved branches connect the central concept to the edge of each category.
    for index, (x, y) in enumerate(positions):
        planned = index == 5
        color = '#ea580c' if planned else '#2563eb'
        style = 'planned' if planned else 'current'
        start_x = 630 if x < 740 else 850
        end_x = x + 420 if x < 740 else x
        dash = ' stroke-dasharray="7,5"' if planned else ''
        lines.append(f'<path d="M {start_x},495 C {(start_x+end_x)/2},495 {(start_x+end_x)/2},{y+36} {end_x},{y+36}" fill="none" stroke="{color}" stroke-width="2.5"{dash} marker-end="url(#arrow-{style})"/>')
    for index, ((x, y), (title, children)) in enumerate(zip(positions, content['cards'])):
        planned = index == 5
        color = '#ea580c' if planned else '#2563eb'
        tint = '#fff7ed' if planned else '#eff6ff'
        lines.append(f'<rect x="{x}" y="{y}" width="420" height="210" rx="14" fill="#ffffff" stroke="#d1d5db" stroke-width="1.5"/>')
        lines.append(f'<rect x="{x+12}" y="{y+12}" width="396" height="48" rx="8" fill="{tint}"/>')
        lines.append(f'<circle cx="{x+36}" cy="{y+36}" r="14" fill="{color}"/>')
        lines.append(f'<text x="{x+36}" y="{y+42}" text-anchor="middle" font-size="16" fill="#ffffff" font-weight="700">{index+1}</text>')
        lines.append(f'<text x="{x+62}" y="{y+43}" font-size="22" font-weight="600" fill="#111827">{escape(title)}</text>')
        # Second-level branches terminate before each leaf label.
        for child_index, child in enumerate(children):
            leaf_y = y + 92 + child_index * 44
            lines.append(f'<path d="M {x+36},{y+61} C {x+36},{leaf_y-8} {x+36},{leaf_y-8} {x+51},{leaf_y-8}" fill="none" stroke="{color}" opacity="0.45" stroke-width="1.4"/>')
            lines.append(f'<circle cx="{x+52}" cy="{leaf_y-8}" r="3" fill="{color}"/>')
            lines.append(f'<text x="{x+64}" y="{leaf_y-2}" font-size="18" fill="#374151">{escape(child)}</text>')
    lines.append('<rect x="630" y="443" width="220" height="104" rx="16" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5"/>')
    lines.append('<rect x="646" y="455" width="188" height="17" rx="5" fill="#dbeafe"/>')
    for index, color in enumerate(['#ef4444', '#f59e0b', '#10b981']):
        lines.append(f'<circle cx="{658+index*14}" cy="463" r="3.5" fill="{color}"/>')
    lines.append('<text x="740" y="505" text-anchor="middle" font-size="29" font-weight="700" fill="#1d4ed8">VideoGet</text>')
    lines.append(f'<text x="740" y="529" text-anchor="middle" font-size="16" fill="#6b7280">{escape(content["center"])}</text>')
    lines.append('<path d="M 40,906 H 78" stroke="#2563eb" stroke-width="2.5" fill="none"/>')
    lines.append(f'<text x="90" y="912" font-size="16" fill="#6b7280">{escape(content["current"])}</text>')
    lines.append('<path d="M 380,906 H 418" stroke="#ea580c" stroke-width="2.5" stroke-dasharray="7,5" fill="none"/>')
    lines.append(f'<text x="430" y="912" font-size="16" fill="#6b7280">{escape(content["planned"])}</text>')
    lines.append(f'<text x="40" y="944" font-size="16" fill="#6b7280">{escape(content["note"])}</text>')
    lines.append('</svg>')
    svg = OUTPUT / f'feature-mindmap.{language}.svg'
    svg.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    subprocess.run(['rsvg-convert', str(svg)], stdout=subprocess.DEVNULL, check=True)
    png = svg.with_suffix('.png')
    subprocess.run(['rsvg-convert', '-w', '1920', str(svg), '-o', str(png)], check=True)
    print(svg)
    print(png)


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for language, content in CONTENT.items():
        generate(language, content)
