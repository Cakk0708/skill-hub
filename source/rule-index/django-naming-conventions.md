---
title: Django 命名约定
description: Django Model、字段和 REST URL 的命名参考
applicable_path: "backend/apps/**/models.py; backend/apps/**/models/*.py; backend/apps/**/urls.py; backend/apps/**/urls/*.py"
---

# Django 命名约定

新增命名或调整既有名称前，先检查项目约定及其对数据库、URL、调用方的影响。不要仅为统一风格重命名已发布的 Model、表、字段或 URL。

项目沿用本项目已有命名和相邻代码风格。以下为适用相应项目约定时的常见写法：

## Model 与字段

- 新建 Model 类通常使用单数 PascalCase。
- 需要显式设置表名时，按项目约定使用 `{app_label}_{model_snake_case}`；Django 默认表名可用时不必额外声明 `db_table`。
- 项目若统一时间和备注字段名，新增字段沿用既有名称，例如 `created_at`、`updated_at` 和 `remark`。不要为了改名破坏现有数据库或 API 契约。

```python
class DeliveryOrder(models.Model):
    class Meta:
        db_table = "logistics_delivery_order"
```

## REST URL

- 新 URL 的资源名、复数形式和大小写遵循项目现有路由约定及公开 API 契约。
- 项目的新 REST URL 使用 kebab-case 和复数资源名，例如 `delivery-orders/`；维护既有 URL 时保留已发布路径，除非任务明确包含迁移。
