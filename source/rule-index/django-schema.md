---
title: Django Model 与数据库结构变更规范
description: Django Model、字段、关系、数据库表和 migration 变更
applicable_path: "backend/apps/**/models.py; backend/apps/**/models/*.py; backend/apps/**/migrations/**"
---

# Django Model 与数据库迁移约定

## 适用范围

适用于 Django Model、字段、关系、约束、表名和数据库 migration 的新增或修改。即使任务从 API 或业务需求开始，只要需要改变数据库结构，也必须遵循本规范。

## 变更流程

1. 检查相邻 Model、字段和关系的现有写法，并搜索受影响字段、表名或关系在查询、Serializer 和业务层中的使用点。
2. 判断变更对已发布字段、表名、关系和现有数据的影响，保留已有数据库契约。涉及重命名或数据转换时，先明确兼容方案。
3. 按下方 Model 约定修改 Model，并遵循当前项目的命名和枚举约定。MES 项目还需读取 `.codex/rules/backend/naming-conventions.md` 与 `.codex/rules/backend/enums.md`。
4. 结构变化先修改 Model，再使用 Django `makemigrations` 生成新的 migration；检查 operations、依赖关系和历史链。
5. 不从零手写普通 schema migration。确实需要数据迁移或特殊数据库操作时，在新的 migration 中添加，并说明原因。
6. 已提交或已部署的 migration 是数据库演进历史。除非用户明确要求修复历史 migration 并确认影响，否则不要修改、删除或重命名它们。
7. 不连接或迁移生产数据库。只做与本次结构变化相关的验证，不顺手重构或格式化无关模块。

## Model 约定

- 新建 Model 时提供清楚的 `verbose_name`。
- 只有需要固定既有表名或遵循模块显式表名约定时才设置 `db_table`；使用 Django 默认表名时，不要重复声明。
- 只有在 Model 由项目自定义权限体系管理且不需要 Django 默认 CRUD 权限时，才设置 `default_permissions = ()`。自定义 `permissions` 前先确认模块现有做法。
- `Meta` 通常放在字段声明之后；不要为了格式调整无关方法。
- 一对多或多对一使用 `ForeignKey`。
- 多对多关系沿用项目现有模式，并显式检查 `ManyToManyField` 的 `through` Model；中间 Model 用 `ForeignKey` 表达两端关系。
- 修改已有关系前，先检查现有 through Model、相关查询和 migration 影响。

```python
class Customer(models.Model):
    tags = models.ManyToManyField(
        "BDM.Tag",
        through="CustomerTag",
        related_name="customers",
    )


class CustomerTag(models.Model):
    customer = models.ForeignKey("BDM.Customer", on_delete=models.CASCADE)
    tag = models.ForeignKey("BDM.Tag", on_delete=models.CASCADE)
```
