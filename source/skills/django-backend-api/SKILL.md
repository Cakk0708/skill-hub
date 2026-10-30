---
name: django-backend-api
description: >
  在实现或维护 MES Django API、View、Serializer，或迁移其前后端字段契约时使用。按接口类型选择实现参考并保留既有公开契约；接口文档工作使用 api-docs。
---

# MES 后端 API

用于接口实现和维护。接口文档内容仍由 `api-docs` skill 负责。

## 工作流程

1. 先判断任务是新增接口、明确迁移公开契约，还是修复既有接口。修复时检查同模块的 URL、View、Serializer 和调用方，保留既有 HTTP 方法、参数名、权限及响应格式。
2. 新增 API 或明确调整公开契约时，读取 [api-response.md](../../rules/backend/api-response.md)。若涉及前端消费字段，同时读取 [前端 API 数据约定](../../rules/frontend/api-data.md)，检索并更新 API 模块及页面中的请求参数、请求体、响应字段、嵌套字段、枚举元数据和错误处理。不要只改后端 Serializer。
3. 按接口类型读取 [通用 View 约定](references/views.md) 和一个对应参考：列表、详情或枚举。简要列表沿用列表响应结构，用简要列表 Serializer，不单独定义分页协议。
4. 修改 Serializer 时读取 [Serializer 命名](references/serializers/naming.md) 和本次涉及的类型参考。不要加载无关类型。
5. 新 URL 命名参考 [Model 与 URL 命名](../../rules/backend/naming-conventions.md)。枚举定义或枚举 API 还需参考 [Django 枚举约定](../../rules/backend/enums.md)。
6. 如果任务明确包含 `docs/api/` 接口文档，再使用 `api-docs` skill，并按公开 wire 字段名记录实际行为；说明与内部 Serializer 字段名的映射。

## 按类型选择参考

### View

- [通用 View 约定](references/views.md)
- 列表或简要列表：[列表 View](references/views/list-view.md)
- 详情：[详情 View](references/views/detail-view.md)
- 枚举：[枚举 View](references/views/enum-view.md)

### Serializer

- 命名：[Serializer 命名](references/serializers/naming.md)
- 写入：[写入 Serializer](references/serializers/write-serializer.md)
- 列表项：[列表 Serializer](references/serializers/list-serializer.md)
- 详情：[详情 Serializer](references/serializers/detail-serializer.md)
- 简要列表项：[简要列表 Serializer](references/serializers/simple-serializer.md)
- 查询参数：[查询参数 Serializer](references/serializers/params-serializer.md)
- 批量删除：[批量删除 Serializer](references/serializers/delete-serializer.md)
