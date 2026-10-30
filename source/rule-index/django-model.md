---
title: Django Model 规范
description: Django Model 的字段、关系与 Meta 配置约定
applicable_path: "backend/apps/**/models.py; backend/apps/**/models/*.py"
---

# Django Model 约定

Model 与数据库结构的变更流程以 `django-schema` 为准；本规则补充 Model 的局部写法。

## Model 与 Meta

- 新建 Model 时提供清楚的 `verbose_name`。
- 只有需要固定既有表名或遵循模块显式表名约定时才声明 `db_table`；使用 Django 默认表名时不要重复声明。
- 仅当 Model 由项目自定义权限体系管理且不需要 Django 默认 CRUD 权限时，才设置 `default_permissions = ()`。添加 `permissions` 前检查模块现有做法。
- `Meta` 通常放在字段声明之后。不要为满足格式规则而改动无关方法或 Model。

## 关系字段

- 一对多或多对一使用 `ForeignKey`。
- 多对多关系沿用项目现有模式，并检查是否需要显式 `through` Model；中间 Model 使用指向双方的 `ForeignKey`。
- 修改已有关系前检查 through Model、相关查询和 migration 影响。

```python
class Customer(models.Model):
    tags = models.ManyToManyField(
        "BDM.Tag",
        through="CustomerTag",
        related_name="customers",
    )

    class Meta:
        verbose_name = "客户"


class CustomerTag(models.Model):
    customer = models.ForeignKey("BDM.Customer", on_delete=models.CASCADE)
    tag = models.ForeignKey("BDM.Tag", on_delete=models.CASCADE)
```

MES 项目还需遵循 `.codex/rules/backend/naming-conventions.md` 和
`.codex/rules/backend/enums.md`。其他项目按自身既有命名、枚举规则和相邻 Model 写法执行。
