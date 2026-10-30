---
title: Django Serializer 规范
description: Django REST Framework Serializer 的字段、命名与请求参数约定
applicable_path: "backend/**/serializers.py; backend/**/serializers/**/*.py"
---

# Django Serializer 约定

MES 项目的 Serializer 实现细则以 `django-backend-api` skill 为准；其他项目遵循各自现有 API 约定。新增或修改接口前，检查相邻 View、Serializer 和调用方，并保留已发布的公开字段、请求体和查询参数，除非任务明确要求迁移契约。

## Serializer 命名规范

新增 Serializer 使用资源名和用途后缀。资源模块足够明确时，可沿用模块内的简短名称；同一模块内避免多个含义不同的类都使用无法区分的通用名称。

| 用途 | 命名后缀 | 示例 |
|---|---|---|
| 写入 | `WriteSerializer` | `CustomerWriteSerializer` |
| 列表项 | `ListSerializer` | `CustomerListSerializer` |
| 简要列表项 | `SimpleSerializer` | `CustomerSimpleSerializer` |
| 详情 | `DetailSerializer` | `CustomerDetailSerializer` |
| 删除请求 | `DeleteSerializer` | `CustomerDeleteSerializer` |
| 查询参数 | `ParamsSerializer` 或 `ListParamsSerializer` | `CustomerParamsSerializer` |

修改已有名称时检查所有导入和调用点。

## 字段命名与映射

- MES 新接口的 Serializer 属性使用 Python `snake_case`；项目 parser/renderer 将公开 JSON 的 `camelCase` 字段映射到 Serializer 属性。例如外部字段 `projectNodeId` 对应内部 `project_node_id`。
- 不要同时声明 snake_case 和 camelCase 两套字段，也不要为同一 casing 转换再添加硬编码别名。维护既有接口时先确认 parser/renderer 行为，并保留线上字段名。
- 外部字段对应的 Model 属性名不同时，通过 `source` 显式映射。
- 关联模型 ID 使用带合适 `queryset` 的 `PrimaryKeyRelatedField` 校验关联记录是否存在；不要用 `IntegerField` 代替对象关联校验。

```python
from rest_framework import serializers


class DeliverableWriteSerializer(serializers.Serializer):
    """创建交付物序列化器。"""

    project_node_id = serializers.PrimaryKeyRelatedField(
        source="project_node",
        queryset=ProjectNode.objects.all(),
        error_messages=serializer_func.error_data,
    )
    assigned_user_id = serializers.PrimaryKeyRelatedField(
        source="assigned_user",
        queryset=User.objects.all(),
        error_messages=serializer_func.error_data,
    )
```

以下写法会导致 MES 的 parser/renderer 无法按约定完成字段映射，或跳过关联对象存在性校验：

```python
# 错误：字段名没有使用 Serializer 内部 snake_case
projectNodeId = serializers.PrimaryKeyRelatedField(...)

# 错误：整数本身不会校验关联模型记录是否存在
project_node_id = serializers.IntegerField()
```

## 批量删除 Serializer

此约定仅适用于请求体一次删除多条记录的批量接口。通过 URL 主键删除单条资源时，不要求额外创建 `ids` Serializer。

- 批量删除必须接收非空的 `ids` 列表。
- `ids` 使用 `ListField`，其 `child` 使用带 `queryset` 的 `PrimaryKeyRelatedField`，以校验每个 ID 对应的记录。
- 设置 `required=True`、`allow_empty=False` 和清楚的中文校验提示。
- 有关联数据或业务约束时，在专用校验方法或业务层显式处理；遵循项目现有删除事务和关联检查流程。

```python
from rest_framework import serializers


class CustomerDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Customer.objects.all(),
        ),
        required=True,
        allow_empty=False,
        error_messages={
            "required": "ids 不能为空",
            "empty": "ids 不能为空",
        },
    )

    def validate_ids(self, value):
        for customer in value:
            if customer.accounts.exists():
                raise serializers.ValidationError(
                    f'客户“{customer.name}”存在关联账户，无法删除'
                )
        return value
```

拿到已校验的实例后，由项目既有删除流程执行操作，例如：

```python
from django.db import transaction


def delete_customers(customers):
    with transaction.atomic():
        for customer in customers:
            customer.delete()
```

错误示例：

```python
# 错误：单条删除接口不应被强行改为批量请求
class CustomerDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()

# 错误：无法校验记录是否存在
ids = serializers.ListField(child=serializers.IntegerField())

# 错误：允许缺失或空列表绕过批量删除输入校验
ids = serializers.ListField(
    child=serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
)
```

## 查询参数 Serializer

查询参数按接口实际支持的筛选项声明；不要求每个 Serializer 固定包含 `keywords`、`page` 或排序字段。MES 新接口的公开字段使用 camelCase，query middleware 转换后，Serializer 使用 snake_case 属性。页码从 1 开始，页大小为正数且不得超过项目约定上限。

```python
from django.db import models
from rest_framework import serializers


class ListParamsSerializer(serializers.Serializer):
    """订单列表查询参数。"""

    keywords = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    page = serializers.IntegerField(
        required=False,
        min_value=1,
        default=1,
    )
    page_size = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        default=20,
    )
    order_no = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def get_queryset(self, queryset):
        query = models.Q()
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            query &= models.Q(
                organization=request.user.organization,
            )

        if order_no := self.validated_data.get("order_no"):
            query &= models.Q(order_no=order_no)

        if keywords := self.validated_data.get("keywords"):
            query &= (
                models.Q(account__username__icontains=keywords)
                | models.Q(account__nickname__icontains=keywords)
                | models.Q(account__email__icontains=keywords)
                | models.Q(account__phone__icontains=keywords)
                | models.Q(account__remark__icontains=keywords)
                | models.Q(account__customer__name__icontains=keywords)
            )

        return queryset.filter(query)
```

分页由列表 View 在筛选后处理，页码从 1 开始：

```python
page = serializer.validated_data.get("page", 1)
page_size = serializer.validated_data.get("page_size", 20)
total = queryset.count()
start = (page - 1) * page_size
items = queryset[start : start + page_size]
```

响应的分页字段遵循项目统一 API 契约；查询参数 Serializer 不另行定义响应包装格式。

## Simple Serializer

简要列表 Serializer 只返回页面或组件需要的字段，不自动序列化整个 Model。字段声明可先列基础类型，再列嵌套或计算字段；按接口需要明确 `Meta.fields`。

```python
from rest_framework import serializers


class CustomerSimpleSerializer(serializers.ModelSerializer):
    """客户简要信息，仅返回 id、code、name。"""

    class Meta:
        model = Customer
        fields = ["id", "code", "name"]
```

## Detail Serializer

详情 Serializer 只声明公开接口需要的字段。Serializer 属性使用 snake_case，由项目 renderer 输出公开 camelCase 键；维护旧接口时以其线上字段名为准。可先列基础字段，再列嵌套或计算字段。

```python
from rest_framework import serializers


class CustomerDetailSerializer(serializers.Serializer):
    """客户详情序列化器。"""

    id = serializers.IntegerField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    assigned_user = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_assigned_user(self, obj):
        return {
            "id": obj.assigned_user_id,
            "name": obj.assigned_user.name,
        }

    def get_tags(self, obj):
        return list(obj.tags.values("id", "name"))
```

不要将未经检查的全部 Model 字段直接暴露给 API；嵌套或计算字段可以使用 `SerializerMethodField`，不应仅因字段由方法计算就禁止使用。

## List Serializer

列表 Serializer 描述列表项，不负责分页响应外层。ModelSerializer 的 `Meta.fields` 顺序就是列表项字段顺序；按公开契约维护字段。

```python
from rest_framework import serializers


class CustomerListSerializer(serializers.ModelSerializer):
    """客户列表项。"""

    id = serializers.IntegerField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    class Meta:
        model = Customer
        fields = ["id", "name", "is_active", "created_at"]
```

新 API 的列表容器和分页结构遵循项目 API 响应契约；已有接口维持原响应格式。
