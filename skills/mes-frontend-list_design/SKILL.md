---
name: mes-frontend-list_design
description:
  涉及 MES 前端列表页设计、实现或调整时触发。
  本技能规范 DataPages 列表组件的职责与组合方式，统一列表页布局、交互和视觉规则。
---

## 页面结构与共享组件

MES 前端可复用的列表页组件集中在 `frontend/src/components/DataPages/List/`，由页面按业务需要组合，不要求每个页面固定使用全部组件。组件通过属性、插槽和事件提供通用界面能力；页面负责数据请求、权限判断和业务处理。

| 组件 | 职责 |
| --- | --- |
| `ListPageLayout` | 列表页布局容器；提供 `background`、`toolbar`、`group-list`、默认内容、`footer` 和 `overlays` 插槽。 |
| `ListPageToolbar` | 通用列表操作栏；提供新增、复制、批量删除、操作组、导入导出等控件，并通过事件把操作交给页面处理。 |
| `ListPageFilter` | 通用筛选区；支持条件筛选、快捷筛选、查询、重置和本地保存；`shellOnly` 模式可供自定义筛选内容复用外框和操作区。 |
| `ListPageGroupTree` | 可拖宽的分组树侧栏；分组数据和增删改、选中等业务操作由页面提供和处理。 |
| `ListPageTable` | 表格核心；负责行列渲染、排序、选择、树形数据、行操作、汇总、单元格插槽和列偏好设置。 |
| `LegacyListTableAdapter` | 旧表格接口的兼容层；转换旧列配置和事件，并处理字典列、行选择及日志/消息单元格。 |
| `ListPagePagination` | 分页栏；提供每页条数、页码跳转和选择统计，通过事件通知页面。 |
| `FilterActions` | 可独立复用的筛选操作按钮组。 |
| `ParticleBackground` | 粒子背景组件的共享封装；从 `@/components/DataPages` 或 `DataPages/Shared` 使用。 |

### 组件使用与样式约束

- 新建或重构列表页时，优先使用 `ListPageLayout`、`ListPageToolbar`、`ListPageFilter`、`ListPageGroupTree`、`ListPageTable` 和 `ListPagePagination` 等共享组件；按页面实际需要选用，不要在页面中重写筛选区、分组树、表格或分页。
- 字段元数据筛选需要远程关联选择等扩展能力时，使用共享组合组件 `SearchConditions`；旧表格公开属性或事件契约暂时无法迁移时，使用 `LegacyListTableAdapter`。不要在页面中另造筛选器、表格或适配层。
- 页面只通过共享组件公开的属性、事件和插槽传递业务数据与行为，不增加只服务单个页面的视觉配置。
- 不在页面样式中覆盖 `.table-card`、筛选条、表头/表体或分页容器的内边距、间距、尺寸、颜色和边框。标准组件缺少共用样式能力时，应修改共享组件本身，让使用该组件的列表保持一致。

### 列表页组合方式

- `ListPageLayout` 的 `toolbar` 插槽承载 `ListPageToolbar`；有分组时把 `ListPageGroupTree` 放入 `group-list` 插槽；默认插槽内容位于右侧 `.table-card`，通常放筛选区和表格；把 `ListPagePagination` 放入 `footer` 插槽，使其与右侧表格区同宽。
- `background` 和 `overlays` 插槽分别用于背景与浮层。粒子背景使用共享封装 `ParticleBackground`。
- 新页面直接使用 `ListPageTable`。已有页面仍依赖旧表格属性或事件时使用 `LegacyListTableAdapter` 维持兼容，避免在适配层外重复实现旧契约。
- 列表关联的详情视图可使用 `frontend/src/components/DataPages/Detail/DetailPageLayout.vue`；列表页规则不替代详情表单自身的业务和交互要求。

### 顶部操作条

`ListPageToolbar` 提供以下常见操作控件，实际显示项和操作组由页面按本模块业务选择：

- **新增和复制**：可配置显示；复制需有已选记录。
- **批量删除**：可配置显示；默认在没有选中记录时禁用。
- **操作组**：默认提供提交/撤销、审核/反审核和启用/禁用等组，也可通过 `actionGroups` 配置本模块的操作。
- **导入导出**：可分别控制显示和禁用状态。

`ListPageToolbar` 统一操作栏的布局和交互样式。页面可通过组件公开的属性及 `prefix`、`actions`、`extra-actions`、`tools` 插槽配置本模块需要的操作，并在页面中处理组件发出的事件；不要在页面中另行搭建一套操作栏。

### 搜索过滤条

搜索过滤条为组合式条件搜索，可通过点击"新增条件组合"按钮添加多个搜索条件。

#### 按钮介绍

- **字段**: 可搜索字段来自模块 enums 接口返回的 fieldsMetadata 字段列表
- **搜索条件**: 根据枚举接口返回的字段类型描述的字段类型，不同字段类型对应不同的搜索条件
  - **包含**: 仅文本型
  - **不包含**: 仅文本型
  - **等于**: 通用
  - **不等于**: 通用
  - **开头为**: 仅文本型
  - **结尾为**: 仅文本型
  - **大于**: 仅数值类型
  - **小于**: 仅数值类型
  - **早于**: 仅日期类型
  - **晚于**: 仅日期类型
  - **不早于**: 仅日期类型
  - **不晚于**: 仅日期类型
- **筛选值**: 根据搜索条件的不同，筛选值也不同
  - **string**: 输入框
  - **integer**: 输入框
  - **datetime**: 输入框为日期范围选择框
  - **choice**: 对应 enums 接口提供的 options 作为下拉框可选值
- **新增条件组合**: 创建一个新的 字段 + 搜索条件 + 筛选值 的组合
- **查询**: 执行搜索
- **重置**: 重置所有搜索条件
- **保存**: 保存当前搜索条件（缓存到浏览器 localStorage）

#### 缓存方式介绍

筛选配置保存在当前浏览器的 `localStorage`，默认按账号及 `modelPart`（未提供时按当前路由）区分；可通过 `storageKey` 指定存储键。沿用 `filterConfig` 工具和共享组件的存储约定，不要在页面中另行构造缓存键。

### API 字段与筛选元数据

- 前端请求参数和 API 响应对象键遵循 [`frontend/api-data.md`](../../rules/frontend/api-data.md) 的 camelCase 约定，例如 `pageSize`、`totalPages` 和行字段 `disableFlag`。
- enums 接口的 `fieldsMetadata` 对象键会自动转换，例如 `field_type` 变成 `fieldType`；但 `fieldsMetadata.key` 是字符串值，不会自动转换。不要把它默认当作表格行属性。
- 配置表格列时，`prop` 必须对应响应行中的 camelCase 字段。若元数据 `key` 是蛇形，只在构造列配置时映射成驼峰，并保留原始元数据供筛选使用。
- 搜索条件若序列化成 `query` 等字符串，表达式中的字段名不会被 camel-case middleware 改写。当前 flattened query 使用后端解析器约定的字段名（例如 `disable_flag`）；除非同步迁移后端解析器和元数据，不要单独把 DSL 值改成驼峰。

### 分组表格主体

分组表格主体用于展示分组数据，大部分模块没有分组，只有部分模块有分组；
分组表格主体占左侧独立列；搜索过滤条、核心表格主体、底部统计与分页在右侧主列纵向排列。

布局关系结构如下：
```
- 列表主体（左右布局）
  - 分组表格主体
  - 右侧主列（纵向布局）
    - 搜索过滤条
    - 核心表格主体
    - 底部统计与分页
```

在 `ListPageLayout` 中按以下位置组合：`ListPageGroupTree` 放入 `group-list` 插槽，作为左侧区域独立于 `.table-card`；默认插槽中的搜索过滤条和核心表格放在右侧 `.table-card`；`ListPagePagination` 放入 `footer` 插槽，在右侧主列中紧接表格卡片下方、与表格区同宽。不要把分组树放进 `.table-card`，也不要让分页横跨分组区和表格区。

有分组的列表页使用分组树侧栏筛选右侧表格数据，通常包含：

- 分组筛选
- 分组内容（核心表格主体）
  - 全部
  - 子列

### 核心表格主体

每个数据表格包含以下列：

- **勾选框**: 用于选择行
- **字段列**: 根据模块 enums 接口返回的 fieldsMetadata 字段列表
  - name 为展示列名称
  - visble 为 true 的可展示到列
  - sortble 为 true 的可列支持排序
  - fieldType 
    - 为 choice 的列不能直接展示 value，需用 value 值匹配到对应 options 后展示
    - 为 boolean 的直接展示`是`与`否`
- **操作**: 操作列，包含编辑、删除、更多按钮
  - 编辑
  - 删除
  - 更多
    - 复制：通用
    - 禁用: 字段中包含 disbleFlag 且值为 false 时显示
    - 启用: 字段中包含 disbleFlag 且值为 true 时显示
    - 提交: 字段中包含 status 且值为 PENDING 时显示
    - 撤销: 字段中包含 status 且值为 IN_PROGRESS 时显示
    - 审核: 字段中包含 status 且值为 IN_PROGRESS 时显示
    - 反审核: 字段中包含 status 且值为 REVIEWED 时显示

#### 表格交互

- **表格滚动**: 表格内容超出允许高度时，允许横向滚动，但勾选框列与操作列保持固定不参与滚动

### 底部统计与分页

- 统计块
  - 统计数据总数（全页）
  - 统计选中行数
- 分页组件
  - 单页展示数量选择器
  - 页面选择器
    - 上一页
    - 临近页
    - 本页
    - 临近页
    - 下一页
  - 页跳转

## 组件路径

- `frontend/src/components/DataPages/List`
- `frontend/src/components/DataPages/Shared`
- `frontend/src/components/DataPages/Detail`
- 元数据扩展筛选组合组件：`frontend/src/components/SearchConditions`

## 设计要求

- **视觉对齐**: 要求设计内容遵循“视觉对齐”原则
- **视觉一致性**: 要求设计内容遵循“视觉一致性”原则

