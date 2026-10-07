# 枚举 View

枚举 View 使用资源名加 EnumView 后缀。新增接口的响应外层遵循 `.codex/rules/backend/api-response.md`，枚举 View 只负责组织 `data` 中的选项。

`data.choices` 的枚举值和展示标签由 `.codex/rules/backend/enums.md` 定义。不要在 View 中复制另一份枚举字典。
