---
title: Django Migration 保护规范
description: Django migration 的生成、检查与历史文件保护
applicable_path: "backend/apps/**/migrations/**"
---

# Django Migration 规范

- 数据结构变更遵循 `django-schema` 中的流程：先修改 Model，再运行 Django `makemigrations` 生成 migration，并检查 operations、依赖关系和历史链。
- 不从零手写普通 schema migration。数据迁移或特殊数据库操作确有需要时，在新的 migration 中添加，并说明原因。
- 已提交或已部署的 migration 是数据库演进历史。除非用户明确要求修复历史 migration 并确认影响，否则不要修改、删除或重命名它们，也不要改动其依赖关系或 operations。
- 允许读取 migration 以了解 schema 历史；不要连接或迁移生产数据库。
- 此规则不禁止通过 `makemigrations` 新增 migration，也不限制在新 migration 中实现必要的数据迁移或特殊操作。
