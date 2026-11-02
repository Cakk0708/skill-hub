---
title: MES前端详情页设计规范
description: MES前端详情页的设计规范
applicable_path: "frontend/src/views/**"
---

## 三态工作模式（`view` / `edit` / `create`）

详情页统一划分为三种工作模式，配合 `useDetailMode`（`frontend/src/composables/useDetailMode.js`）与顶栏等分标签栏（`EqualSplitTabBar`）协同工作：

- **只读浏览态（A01，`mode="view"`，默认）**
  - 在详情页标签（`{模块名} - {编码}`）下默认进入只读结构化看板。
  - **禁止使用置灰的 `disabled` 输入框**展示只读字段，统一使用 `DetailCard` + `DetailKeyValueGrid` 及只读表格展示。
  - **顶部工具栏左侧不显示返回按钮与分割线**，左侧直接以单据标题 + 状态指示胶囊起始；页面切换与关闭统一由顶部 `EqualSplitTabBar` 承载。
- **编辑修改态（B01，`mode="edit"`）**
  - 在当前详情页标签内**原地平滑切换**为多段式表单与可编辑子表视图（支持路由参数 `?mode=edit` 直接进入）。
  - 顶部工具栏左侧显示中性按钮 **`‹ 退出编辑`** 及垂直分割线；点击后执行脏数据检查（`checkDirty`），确认后通过快照回滚（`rollback`）并切回当前标签的 `view` 态，**不关闭当前路由标签**。
  - 单据核心编码字段在编辑态下强制锁定（`disabled`），不允许修改。
- **新建录入态（C01，`mode="create"`）**
  - 对应独立的新增页路由与标签（`{模块名} - 新增`）。
  - 顶部工具栏左侧显示中性按钮 **`✕ 取消新建`** 及垂直分割线；点击后关闭当前新增页标签并回到上一个标签。
  - 核心编码字段留空并展示自动生成占位符（如“系统自动生成 (保存后生效)”）；通过克隆/复制进入新增页时，必须清空原单据编码。
  - 点击“立即创建”接口响应成功后，**关闭当前新增页标签并跳转（`router.replace`）至新生成的单据详情页**；点击“保存并继续新增”则保留常用上下文并重置表单，停留在新增页。

---

## 页面结构与共享组件

MES 前端可复用的详情页组件集中在 `frontend/src/components/DataPages/Detail/`（并由 `@/components/DataPages` 统一导出），由页面按业务需要组合。组件通过属性、插槽和事件提供通用界面能力；页面负责数据请求、权限判断和业务处理。

| 组件 | 名称 | 职责 |
| --- | --- | --- |
| `DetailPageLayout` | 详情页布局容器 | 提供详情页外层滚动视口、背景色、`ParticleBackground` 科技粒子背景、卡片纵向流式间距以及表单标准 4 列 Grid 栅格样式。 |
| `DetailToolbar` | 详情页三态操作栏 | 按 `mode`（`view` / `edit` / `create`）管理左侧退出/取消按钮（`view` 态默认隐藏，`edit` 态显示“‹ 退出编辑”，`create` 态显示“✕ 取消新建”）、单据标题、状态指示胶囊（`statusInfo`）及右侧业务动作与工具按钮（打印、刷新等）。 |
| `DetailCard` | 详情页分段卡片 | 提供带 3px 蓝色垂直标线的分段标题、数量/指标徽标（`badgeText`）、右上角自定义动作插槽（`header-actions`）、折叠/展开过渡控制（`collapsible`）及标准 Grid 卡片主体。 |
| `DetailKeyValueGrid` | 只读键值看板网格 | 用于只读浏览态（A01）展示结构化字段，支持列数配置（默认 4 列）、跨列（`span`）、徽章样式（`badge: 'code' \| 'tag' \| 'attr' \| 'status'`）、辅助单位文本（`subText`）及按字段名具名插槽。 |
| `SubtableToolbar` | 详情子表操作栏 | 用于编辑态/新增态子表上方，提供“新增行”、“插入行”、“复制行”、“删除行”标准按钮与已勾选行数提示徽标（未勾选时插入/复制/删除自动禁用）。 |
| `DetailEmptyState` | 详情空状态引导 | 用于子表或关联区块无数据时的空态展示，支持图标、标题、描述文案、紧凑模式（`compact`）以及主次引导操作按钮（如“从名录批量选择”、“手动新增一行”）。 |

### 配套 Composables

| Composable | 路径 | 职责 |
| --- | --- | --- |
| `useDetailMode` | `frontend/src/composables/useDetailMode.js` | 管理 `view` / `edit` / `create` 模式状态、权限前置校验（`checkCanEdit`）、数据快照（`takeSnapshot`）、脏检查（`checkDirty`）与放弃修改回滚（`rollback`）。 |
| `useDetailTabTitle` | `frontend/src/composables/useDetailTabTitle.js` | 在详情页获取到单据数据后调用 `setDetailCode(code)`，动态将顶部标签栏标题更新为 `{模块名} - {编码}` 并同步写入最近访问单据记录。 |

---

## 页面组合与布局规范

### 整体布局层级

```text
- DetailPageLayout（外层纵向滚动容器 + 粒子背景）
  - DetailToolbar（或基于 DetailToolbar 封装的模块级三态 Toolbar）
  - 只读浏览态视图（v-if="isView"）
    - DetailCard（基础信息卡片）
      - DetailKeyValueGrid（4 列键值看板）
    - DetailCard（子表/关联配置卡片，带 badgeText 如 "共 N 项"）
      - 只读 el-table 或 DetailEmptyState（无数据时）
    - DetailCard（审计与系统追踪信息，可默认展开或折叠）
  - 编辑/新建表单视图（v-else-if="isEdit || isCreate"）
    - DetailCard（基础信息表单卡片，内部 el-form 自动按 4 列 Grid 排列）
    - DetailCard（子表编辑卡片）
      - SubtableToolbar（新增行 / 插入行 / 复制行 / 删除行）
      - 可编辑 el-table 或 DetailEmptyState（带引导新增动作）
```

### 顶部操作栏（`DetailToolbar`）三态动作约定

- **左侧区域（`.toolbar-left`）**：
  - `view` 态：`[单据标题] [状态胶囊]`（无返回按钮与分割线）
  - `edit` 态：`[‹ 退出编辑] | [单据修改标题] [● 编辑修改态 · 待保存]`
  - `create` 态：`[✕ 取消新建] | [新建单据标题] [● 新建待录入 · 系统分配临时编码]`
- **右侧区域（`.toolbar-right`）**：
  - `view` 态：次级工具按钮（打印单据、复制单据、业务操作下拉菜单）+ 状态动作（停用/启用、删除）+ 主操作高亮按钮（`编辑修改`）+ 图标刷新按钮。
  - `edit` 态：`重置修改` + `业务操作` + `删除单据`（按权限与状态）+ 主操作高亮按钮（`保存修改`）。
  - `create` 态：`清空重置` + `引用克隆` + 柔和主操作按钮（`保存并继续新增`）+ 主操作高亮按钮（`立即创建`）。

### 组件使用与样式约束

- 新建或重构详情页/新增页时，必须使用 `DetailPageLayout`、`DetailToolbar`、`DetailCard`、`DetailKeyValueGrid`、`SubtableToolbar`、`DetailEmptyState` 等共享组件，不要在业务页面中自行硬编码顶部操作条或卡片外壳样式。
- 模块专属的三态按钮编排可封装为模块内的 `*Toolbar.vue`（内部包裹 `DetailToolbar` 并透传 `:mode="mode"`），供本模块的 `detail.vue` 与 `add.vue` 共同复用。
- 不在页面私有样式中覆盖 `DetailToolbar`、`DetailCard` 的内边距、圆角、边框和字号规范；确需扩展通用能力时，应修改 `DataPages/Detail/` 下的共享组件并同步更新 `frontend/src/components/DataPages/README.md`。

---

## 测试

使用 Playwright + e2e 对前端页面做功能测试，遵循 `mes-frontend-test` 规范，测试用例存放在 `frontend/e2e/` 目录下。
