---
paths:
  - "frontend-h5"
---

# 设计风格规范 — 风格

> 本规范适用于所有前端页面与组件设计，Claude 在生成任何 UI 前必须严格遵守以下规则。

---

## 🎨 色彩系统（Color System）

### 主色调
```css
--color-primary:       #58CC02; /* 核心绿色，用于主按钮、进度条、选中态 */
--color-primary-dark:  #4CAF00; /* 悬停/按下态 */
--color-primary-light: #D7F5B1; /* 浅绿背景、标签底色 */
```

### 辅助色
```css
--color-error:         #FF4B4B; /* 错误、失败、警告 */
--color-error-light:   #FFE0E0;
--color-warning:       #FFC800; /* 连续打卡、奖励、提醒 */
--color-warning-light: #FFF4CC;
--color-info:          #1CB0F6; /* 信息提示、蓝色互动元素 */
--color-info-light:    #DDF4FF;
--color-purple:        #CE82FF; /* 会员、高级内容 */
--color-purple-light:  #F4DDFF;
```

### 中性色
```css
--color-bg:            #FFFFFF; /* 主背景 */
--color-bg-secondary:  #F7F7F7; /* 次级背景、卡片底色 */
--color-border:        #E5E5E5; /* 分割线、边框 */
--color-text-primary:  #3C3C3C; /* 主文字 */
--color-text-secondary:#777777; /* 次级文字、说明文字 */
--color-text-disabled: #AFAFAF; /* 禁用文字 */
```

### 用色原则
- 绿色（`--color-primary`）为绝对主导色，所有 CTA 按钮、关键进度指示必须使用
- 背景保持白色或极浅灰，不使用深色背景（除特殊暗模式场景）
- 辅助色只用于特定语义（红=错误，黄=奖励，蓝=信息），不随意混用
- 禁止使用渐变紫色、科技感蓝黑等与品牌不符的配色

---

## 🔤 字体与排版（Typography）

### 字体选择
```css
--font-primary: 'Nunito', 'DIN Round Pro', 'Varela Round', sans-serif;
/* 优先使用圆润、粗壮的无衬线字体 */
```

### 字重规范
- **标题**：`font-weight: 800`（ExtraBold），视觉冲击强
- **副标题 / 按钮**：`font-weight: 700`（Bold）
- **正文**：`font-weight: 600`（SemiBold）
- **说明文字**：`font-weight: 500`（Medium）
- 禁止使用 300/400 细字重，整体需要显得饱满有力

### 字号比例
```css
--text-xs:   12px;
--text-sm:   14px;
--text-base: 16px;
--text-lg:   18px;
--text-xl:   20px;
--text-2xl:  24px;
--text-3xl:  30px;
--text-4xl:  36px;
```

### 排版原则
- 文字对齐以居中为主（尤其是激励性文案、标题）
- 行高（line-height）保持 1.4～1.6，保证易读性
- 字母间距（letter-spacing）标题略为 0.5px，正文保持默认

---

## 📐 圆角与间距（Border Radius & Spacing）

### 圆角系统
```css
--radius-sm:   8px;   /* 小型元素：标签、badge */
--radius-md:   12px;  /* 输入框、小卡片 */
--radius-lg:   16px;  /* 卡片、弹窗 */
--radius-xl:   20px;  /* 大按钮、主卡片 */
--radius-full: 9999px; /* 胶囊按钮、头像、进度条 */
```
- **所有按钮默认使用 `--radius-full`（胶囊形）**
- 卡片、面板使用 `--radius-lg` 或 `--radius-xl`
- 禁止出现直角（radius: 0）元素，保持整体圆润感

### 间距系统
```css
--space-1:  4px;
--space-2:  8px;
--space-3:  12px;
--space-4:  16px;
--space-5:  20px;
--space-6:  24px;
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
```
- 内容区域 padding 不低于 `--space-4`（16px）
- 组件间距保持规律性，使用 4px 基础单位的倍数

---

## 🧩 组件规范（Component Rules）

### 按钮（Button）
```css
/* 主按钮 */
background: var(--color-primary);
color: #FFFFFF;
font-weight: 700;
font-size: 16px;
border-radius: var(--radius-full);
padding: 14px 32px;
border: none;
/* 底部阴影制造立体感（Duolingo 标志性效果）*/
box-shadow: 0 4px 0 #3FA000;
transition: transform 0.1s, box-shadow 0.1s;

/* 按下态 */
transform: translateY(2px);
box-shadow: 0 2px 0 #3FA000;
```

- 按钮必须有底部 box-shadow 制造"3D 压陷感"
- 禁用态使用 `--color-text-disabled` + `--color-border` 背景
- 危险操作使用 `--color-error` 主色按钮

### 卡片（Card）
```css
background: #FFFFFF;
border-radius: var(--radius-lg);
border: 2px solid var(--color-border);
box-shadow: 0 2px 8px rgba(0,0,0,0.06);
padding: var(--space-6);
```

### 输入框（Input）
```css
border: 2px solid var(--color-border);
border-radius: var(--radius-md);
padding: 12px 16px;
font-size: 16px;
font-weight: 600;
transition: border-color 0.2s;

/* 聚焦态 */
border-color: var(--color-primary);
outline: none;
box-shadow: 0 0 0 3px var(--color-primary-light);
```

### 进度条（Progress Bar）
```css
height: 16px;
border-radius: var(--radius-full);
background: var(--color-bg-secondary);
/* 填充部分 */
background: var(--color-primary);
border-radius: var(--radius-full);
transition: width 0.4s ease;
```

### 徽章 / 标签（Badge）
```css
border-radius: var(--radius-full);
font-weight: 700;
font-size: 12px;
padding: 4px 10px;
/* 根据语义选择对应颜色变量 */
```

---

## 🎭 插画与图标（Illustration & Icons）

- 优先使用**圆润卡通风格**的插画和 emoji，避免写实图片
- 图标使用填充型（filled）而非线框型（outlined），视觉更饱满
- 吉祥物/角色插画可适当使用，增加趣味性
- 图标尺寸遵循 16 / 20 / 24 / 32px 规格

---

## ✨ 动效规范（Animation）

### 基础过渡
```css
--transition-fast:   0.1s ease;
--transition-base:   0.2s ease;
--transition-slow:   0.3s ease-in-out;
```

### 必须实现的动效
1. **按钮按下**：translateY(2px) + box-shadow 压缩（0.1s）
2. **正确答案**：绿色闪光 + 轻微弹跳（scale 1 → 1.05 → 1）
3. **错误答案**：红色闪烁 + 左右抖动（shake keyframe）
4. **页面切换**：淡入 + 上移（opacity 0→1, translateY 10px→0）
5. **进度增加**：进度条平滑扩展（width transition 0.4s）

### 动效原则
- 动效时长控制在 100ms～400ms，不做慢动作
- 使用 `ease` 或 `ease-out`，不使用 `linear`
- 每个交互必须有即时视觉反馈（< 100ms 响应）

---

## 🏆 游戏化元素（Gamification）

- 连续打卡（Streak）使用 🔥 火焰图标 + 黄色高亮
- 经验值（XP）使用 ⚡ 闪电图标 + 黄色
- 完成成就使用大号 ✨ 动画 + 绿色庆祝效果
- 生命值（Hearts）使用 ❤️ + 红色
- 界面中适当出现激励性文案（"太棒了！"、"继续保持！"）

---

## 🚫 禁止项（Never Do）

- ❌ 禁止使用渐变色背景（linear-gradient 紫色/蓝色）
- ❌ 禁止使用深色主题（dark mode）作为默认
- ❌ 禁止使用直角（border-radius: 0）
- ❌ 禁止使用细字重（font-weight < 500）
- ❌ 禁止使用 Inter、Roboto、Arial 等无个性字体
- ❌ 禁止图标使用 outlined 线框风格
- ❌ 禁止按钮缺少立体 box-shadow 效果
- ❌ 禁止页面元素缺少过渡动画（所有交互必须有反馈）

---

## ✅ 检查清单（Pre-delivery Checklist）

在交付任何 UI 前，确认以下内容：
- [ ] 主按钮是否为绿色胶囊形 + 底部阴影
- [ ] 所有圆角是否 ≥ 8px
- [ ] 字重是否 ≥ 600（正文）、≥ 700（按钮/标题）
- [ ] 色彩是否只使用规范内的变量
- [ ] 交互元素是否有 hover/active 动效
- [ ] 错误/成功状态是否有对应颜色反馈
- [ ] 整体是否传达出**活泼、轻松、游戏化**的氛围
