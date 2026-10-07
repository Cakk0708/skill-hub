# Django View 约定

- 新增 View 延续本项目的 APIView 组织方式；除非任务明确采用其他架构，不新增与项目模式不一致的 generic view 或 viewset。
- View 负责 HTTP 请求、权限、参数校验和响应组装；有可复用或复杂的业务流程时，放入项目现有的业务层/服务层。不要把本规则解释成所有旧 View 都必须立即重构。
- 新增 API 或明确迁移响应契约时，响应结构遵循 `.codex/rules/backend/api-response.md`。维护既有接口时保留原有公开格式。
- 新 View 命名使用资源名和用途后缀，例如 CustomerListView、CustomerDetailView、CustomerSimpleView、CustomerEnumView。
- 若同一文件需要放多个 View，沿用相邻文件的组织顺序；不要为了排序规则大范围移动无关代码。
- 新查询参数遵循对应 API 契约。新 API 使用 snake_case；已有接口继续接受现有参数名。
