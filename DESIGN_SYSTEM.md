# VideoGet 设计系统

## 配色方案

### 主色调
```css
--primary-50: #eff6ff
--primary-100: #dbeafe
--primary-200: #bfdbfe
--primary-300: #93c5fd
--primary-400: #60a5fa
--primary-500: #3b82f6
--primary-600: #2563eb
--primary-700: #1d4ed8
--primary-800: #1e40af
--primary-900: #1e3a8a
--primary-950: #020817
```

### 背景色
```css
--bg-dark: #020817
--bg-card: rgba(15, 23, 42, 0.8)
--bg-glass: rgba(15, 23, 42, 0.6)
```

### 文字色
```css
--text-primary: rgba(255, 255, 255, 0.9)
--text-secondary: rgba(255, 255, 255, 0.65)
--text-muted: rgb(107, 114, 128)
```

### 边框色
```css
--border-glass: rgba(148, 163, 184, 0.2)
--border-glow: rgba(59, 130, 246, 0.3)
```

## 字体系统

### 字体栈
```css
--font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif
```

### 字体大小
```css
--text-xs: 0.75rem (12px)
--text-sm: 0.875rem (14px)
--text-base: 1rem (16px)
--text-lg: 1.125rem (18px)
--text-xl: 1.25rem (20px)
--text-2xl: 1.5rem (24px)
--text-3xl: 1.875rem (30px)
--text-4xl: 2.25rem (36px)
```

## 间距系统

使用 4px 基准：
```css
--spacing-1: 0.25rem (4px)
--spacing-2: 0.5rem (8px)
--spacing-3: 0.75rem (12px)
--spacing-4: 1rem (16px)
--spacing-5: 1.25rem (20px)
--spacing-6: 1.5rem (24px)
--spacing-8: 2rem (32px)
--spacing-10: 2.5rem (40px)
--spacing-12: 3rem (48px)
--spacing-16: 4rem (64px)
```

## 圆角系统

```css
--radius-sm: 0.375rem (6px)
--radius-md: 0.5rem (8px)
--radius-lg: 0.75rem (12px)
--radius-xl: 1rem (16px)
--radius-2xl: 1.5rem (24px)
```

## 阴影系统

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05)
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)
--shadow-glow: 0 0 20px rgba(59, 130, 246, 0.3)
```

## 动画系统

```css
--duration-fast: 150ms
--duration-normal: 200ms
--duration-slow: 300ms

--ease-out: cubic-bezier(0, 0, 0.2, 1)
--ease-in: cubic-bezier(0.4, 0, 1, 1)
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1)
```

## 组件样式

### 按钮样式
- **主按钮**: 蓝色渐变背景 + 发光效果
- **次要按钮**: 透明背景 + 蓝色边框
- **悬停效果**: 轻微上浮 + 发光增强
- **按下效果**: 轻微缩放 (0.98x)

### 卡片样式
- 半透明玻璃背景
- 细微边框
- 柔和阴影
- 悬停时轻微上浮

### 输入框样式
- 深色背景
- 聚焦时蓝色边框发光
- 平滑的过渡动画

### 渐变背景
```css
--gradient-primary: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 50%, #60a5fa 100%)
--gradient-glow: radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.15) 0%, transparent 70%)
```
