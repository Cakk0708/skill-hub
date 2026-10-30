---
title: Django View 规范
description: Django REST Framework View 的职责、命名与接口处理约定
applicable_path: "backend/**/views.py; backend/**/views/**/*.py"
---

# Django View 约定

MES 项目的 View 实现细则以 `django-backend-api` skill 为准；其他项目遵循各自现有 API 约定。新增或修改接口前，检查同模块 URL、View、Serializer 和调用方，并保留已发布的 HTTP 方法、权限、参数名及响应格式。只有任务明确要求迁移时才改变公开契约。

## View 职责与基类

- View 是 HTTP 请求与项目业务层之间的接口层，负责请求分发、权限、参数校验及响应组装。
- 可复用或复杂的业务流程放入项目已有的业务层/服务层；不要把本规则解释为必须立即重构所有旧 View。
- MES 新 View 延续项目的 `APIView` 组织方式；除非任务明确采用其他架构，不新增与项目模式不一致的 `generics.*` 或 `viewsets.*`。
- 新接口或明确迁移的响应遵循项目统一 API 响应契约。维护既有接口时保留现有响应格式；使用项目现有响应类，不固定要求 `JsonResponse` 或 DRF `Response`。

## 视图命名规范

新 View 使用资源名加用途后缀，类名采用 PascalCase。

| 用途 | 命名后缀 | 示例 |
|---|---|---|
| 写入 | `WriteView` | `CustomerWriteView` |
| 列表 | `ListView` | `CustomerListView` |
| 简要列表 | `SimpleView` | `CustomerSimpleView` |
| 详情 | `DetailView` | `CustomerDetailView` |
| 枚举 | `EnumView` | `CustomerEnumView` |
| 删除 | `DeleteView` | `CustomerDeleteView` |

## 视图排序规范

新建文件包含多类 View 时，可按下列顺序组织：

1. WriteView
2. ListView
3. DetailView
4. SimpleView
5. EnumView
6. DeleteView

已有文件沿用相邻模块的组织习惯；不要为了排序规则大范围移动或重排无关 View。

## 详情视图

- 每个请求只读取一次目标实例。可使用项目已有的对象获取 helper；若同一请求的多个 handler 都需要该实例，可在 `dispatch` 中预取并保存为 `self.instance`。
- 对象不存在时捕获对应的 `Model.DoesNotExist`，按项目错误响应契约返回 HTTP 404。MES 新 API 使用结果码 `30001`。
- 不要在 `get`、`put`、`delete` 中重复执行同一查询，也不要使用裸 `except`。

```python
from rest_framework import views
from rest_framework.response import Response

from apps.SM.user.models import User

from .serializers import UserDetailSerializer


class UserDetailView(views.APIView):
    def dispatch(self, request, *args, **kwargs):
        try:
            self.instance = User.objects.get(id=kwargs.get("id"))
        except User.DoesNotExist:
            return Response(
                {
                    "code": 30001,
                    "msg": "数据不存在",
                    "data": None,
                    "errors": [],
                },
                status=404,
            )

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        detail_data = {
            "basicData": UserDetailSerializer(self.instance).data,
            "otherData": {},
            "documentData": {"items": []},
        }
        return Response(
            {
                "code": 0,
                "msg": "success",
                "data": detail_data,
                "errors": [],
            }
        )
```

如果只有一个 handler 需要实例，可使用模块现有的对象获取 helper；不必为了使用 `dispatch` 而增加额外状态。

## 列表视图

- 列表先应用全部筛选，再计算筛选后的总数，最后进行分页切片。
- 列表项使用对应的 List Serializer；简要列表使用只返回所需字段的 Simple Serializer，并沿用统一列表响应结构。
- 新 MES API 的公开查询参数使用 `camelCase`，query middleware 会将参数名映射为 View/Serializer 内部的 `snake_case`。例如外部 `pageSize` 映射为内部 `page_size`；参数值不会自动转换。
- 新 MES 分页从第 1 页开始，`page_size` 必须为正数，并遵循项目约定的最大值。维护既有接口时保留原有参数和分页协议。
- 新 API 的列表响应遵循项目约定：`data.items` 始终为数组，分页信息位于 `data.pagination`，包含 `page`、`pageSize`、筛选后的 `total` 和 `totalPages`。不要为已有接口擅自更换既有结构。

```python
from math import ceil

from rest_framework import views
from rest_framework.response import Response

from apps.BDM.customer.models import Customer

from .serializers import CustomerListSerializer, ListParamsSerializer


class CustomerListView(views.APIView):
    def get(self, request, *args, **kwargs):
        params = ListParamsSerializer(
            data=request.query_params,
            context={"request": request},
        )
        params.is_valid(raise_exception=True)

        queryset = params.get_queryset(Customer.objects.all())
        total = queryset.count()
        page = params.validated_data.get("page", 1)
        page_size = params.validated_data.get("page_size", 20)
        start = (page - 1) * page_size
        items = CustomerListSerializer(
            queryset[start : start + page_size],
            many=True,
        ).data

        return Response(
            {
                "code": 0,
                "msg": "success",
                "data": {
                    "items": items,
                    "pagination": {
                        "page": page,
                        "pageSize": page_size,
                        "total": total,
                        "totalPages": ceil(total / page_size) if total else 0,
                    },
                },
                "errors": [],
            }
        )
```

错误做法包括：在筛选前计算总数、在 `data` 下直接返回数组、漏掉分页元数据，或把 MES 新接口的公开参数声明为 snake_case。

## 枚举视图

- 枚举视图类名使用资源名加 `EnumView` 后缀，例如 `CustomerEnumView`。
- 枚举值与展示标签从统一枚举定义读取；View 负责组织响应，不复制另一份枚举字典。
- 响应外层遵循项目 API 契约。以下示例使用 MES 新 API 的统一响应结构。

```python
from rest_framework import views
from rest_framework.response import Response

from .enums import Choices


class CustomerEnumView(views.APIView):
    """返回客户相关枚举选项。"""

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "code": 0,
                "msg": "success",
                "data": {"choices": Choices.output()},
                "errors": [],
            }
        )
```
