---
name: mes-backend-schema
description: >
  在修改 MES Django Model、字段、关系或数据库结构时使用。指导检查既有数据和调用、形成兼容改动并生成新的迁移。
---

# MES 后端 Model 与数据库结构

## 工作流程

1. 检查相邻 Model、字段和关系的现有写法，并查找待改字段、表名或关系的查询、序列化和业务层使用点。
2. 判断变更是否会影响已发布字段、表名、关系或数据。保留现有数据库契约；需要重命名或转换数据时，明确兼容方案，不直接改写历史 migration。
3. 按 [Model 约定](references/model.md) 修改 Model。命名参考 [Model 与 URL 命名](../../rules/backend/naming-conventions.md)；枚举字段参考 [Django 枚举约定](../../rules/backend/enums.md)。
4. 结构变化时按 [数据库迁移约定](references/migrations.md) 生成新的 migration，并检查 operations、依赖和历史链。不要连接或迁移生产数据库。
5. 仅做与本次结构变化相关的验证，不顺手格式化或重构无关模块。

## 参考

- [Model 约定](references/model.md)
- [数据库迁移约定](references/migrations.md)
- [Model 与 URL 命名](../../rules/backend/naming-conventions.md)
- [Django 枚举约定](../../rules/backend/enums.md)
