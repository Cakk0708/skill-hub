---
title: django-api-docs
description: 根据 backend/apps 中的实际实现和项目公开契约记录接口行为
applicable_path: "backend/**"
---

## 文档结构

- 接口文档统一输出到 `docs/api/`，按 APP、子模块组织，每个接口使用独立 Markdown 文件；同一路径的多个方法可以在同一文件分项记录。
- 新增接口时同步补齐文档；修改已有权限、请求或响应时同步记录实际变化。公共权限规则可集中说明，各接口文档引用对应规则。
- 记录真实 URL、HTTP 方法、参数、权限、HTTP 状态和响应体。未变更的旧接口字段可以链接既有实现作为核对依据，不将未实现能力写成已交付行为。
- 本项目响应规范为 [Duolingo API 响应契约](./backend/api-response.md)，与「客户自助端建设」已确认总纲一致。
- 不将其他项目的响应或自动字段转换约定套用于本项目，也不在文档同步过程中擅自迁移接口契约。

## 字段与响应

- 记录客户端实际发送、接收的字段名。业务新字段使用 camelCase，Token 字段保留 access_token、refresh_token；旧字段按实际公开契约记录。
- 当前没有自动 casing 转换；Model/Serializer 内部映射以实际 source 和 View 组装逻辑为准。
- 新接口成功示例：`{"msg":"success","data":{}}`；无数据操作返回 `{"msg":"success","data":null}`。
- 新认证接口错误示例：`{"msg":"error","data":{"detail":"刷新凭证无效或已撤销"}}`；字段错误示例：`{"msg":"error","data":{"newPassword":["密码校验失败"]}}`。
- 不要求 code、errors、request_id 或整数结果码；既有 DRF `{detail}`、顶层 items 或 data.list 等差异要明确写出。
- 分页参数、基准和响应按接口实际实现记录；后续客户列表约定 data.items + data.pagination（page、pageSize、total），不得据此重写旧列表协议。
- 详情返回业务所需的公开字段；不强制三段式布局，不暴露未经检查的 Model 全部字段。

## HTTP 状态

| 状态 | 含义 |
|---|---|
| 200 | 操作成功 |
| 400 | 参数或业务校验失败 |
| 401 | 未认证或凭证无效 |
| 403 | 身份、状态或权限不允许 |
| 404 | 资源不存在或越权 |
| 409 | 接口实际实现的冲突 |

退出撤销提交的 refresh token，改密撤销已有刷新凭证；不宣称 access token 被即时注销。客户禁用、用户停用、组织丢失等实时状态限制与 Token 到期语义分别记录。
