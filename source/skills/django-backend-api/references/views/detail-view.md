# 详情 View

- 按请求只读取一次目标实例。可使用项目已有的对象获取 helper；若同一请求的多个 handler 都需要实例，可在 dispatch 中预取并保存在 self.instance。
- 对象不存在时捕获对应 Model.DoesNotExist，并按 `.codex/rules/backend/api-response.md` 的错误契约返回 HTTP 404 和结果码 30001。
- 不要在 get、put、delete 等 handler 中重复执行相同查询。
- 新接口详情数据区块遵循统一响应契约；已有接口维持既有结构，除非任务明确要求迁移。
