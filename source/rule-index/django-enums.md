---
title: Django 枚举规范
description: Django 模型枚举定义与枚举 API 的约定
applicable_path: "backend/**/enums.py; backend/**/enums/**/*.py"
---

# Django 枚举约定

- 新增或修改枚举前，检查相邻 Model、Serializer、View 和调用方，保留已发布的枚举值与展示标签。
- 用作 Django 字段 choices 的枚举，按字段类型和项目惯例选用 `models.TextChoices` 或 `models.IntegerChoices`。
- 只有项目约定要求或枚举 API 需要统一组织时，才将枚举集中放入 `Choices` 类并提供列表转换方法；不要为所有枚举无条件增加重复的输出函数。
- 枚举 API 的字段和响应结构遵循项目现有响应契约；MES 项目另需遵循 `django-backend-api` skill。View 不应复制或另造一份枚举字典。
- MES 项目还需遵循 `.codex/rules/backend/enums.md`；其他项目沿用本项目已有的枚举约定。

```python
class Choices:
    class OperationTypes(models.TextChoices):
        CREATE = "CREATE", "创建"
        VIEW = "VIEW", "查看"
        CHANGE = "CHANGE", "修改"
        DELETE = "DELETE", "删除"

    @staticmethod
    def output():
        return {
            "operationTypes": [
                {"value": item.value, "label": item.label}
                for item in Choices.OperationTypes
            ],
        }
```
