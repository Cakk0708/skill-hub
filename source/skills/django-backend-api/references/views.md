# Django View 约定

- 新增 View 延续本项目的 APIView 组织方式；除非任务明确采用其他架构，不新增与项目模式不一致的 generic view 或 viewset。
- View 负责 HTTP 请求、权限、参数校验和响应组装；有可复用或复杂的业务流程时，放入项目现有的业务层/服务层。不要把本规则解释成所有旧 View 都必须立即重构。
- 新增 API 或明确迁移响应契约时，响应结构遵循 `.codex/rules/backend/api-response.md`。维护既有接口时保留原有公开格式。
- 新 View 命名使用资源名和用途后缀，例如 CustomerListView、CustomerDetailView、CustomerSimpleView、CustomerEnumView。
- 若同一文件需要放多个 View，沿用相邻文件的组织顺序；不要为了排序规则大范围移动无关代码。
- 新 API 的公开查询参数使用 `camelCase`；query middleware 会将参数名转换成 View 和 Serializer 使用的 `snake_case`。新增分页参数在线上名为 `pageSize`，内部字段可命名为 `page_size`。
- 查询参数值不会自动转换。尤其是 `query` 等承载筛选表达式的字符串，按其解析器契约处理；不要仅凭外层参数名推断表达式内的字段名也会转换。
- 维护既有接口时保留其已发布的公开参数名。
