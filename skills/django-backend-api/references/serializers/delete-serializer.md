# 批量删除 Serializer

本规则只适用于请求体一次删除多条记录的批量删除接口。通过 URL 主键删除单条资源时，不要求额外创建 ids Serializer。

批量删除请求应校验 ids 非空，并校验每个主键对应的记录确实存在。若删除还受关联数据约束，在专用校验或业务层中明确处理。

~~~python
from rest_framework import serializers

from apps.BDM.customer.models import Cust


class CustomerDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Cust.objects.all(),
        ),
        required=True,
        allow_empty=False,
        error_messages={
            "required": "ids 不能为空",
            "empty": "ids 不能为空",
        },
    )
~~~

使用项目现有的删除事务和关联检查方式。不要把复杂业务删除逻辑藏在字段声明中。
