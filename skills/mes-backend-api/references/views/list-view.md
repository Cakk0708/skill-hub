# 列表 View

- 新增 API 的列表响应结构遵循 `.codex/rules/backend/api-response.md`；维护既有接口时保留其公开格式。
- 查询先应用全部筛选，再计算 total 和分页切片。page 从 1 开始，page_size 必须大于 0。
- 列表项由对应 ListSerializer 提供。简要列表只缩减字段，使用 SimpleSerializer，并沿用相同列表响应结构。
- 新 API 查询参数使用 snake_case；维护既有接口时保留现有公开参数名。
