# 查询参数 Serializer

参数字段由具体接口决定，不要求每个查询 Serializer 都包含同一组字段。

对遵循新 API 约定的分页列表：

- page 从 1 开始，最小值为 1。
- page_size 为正整数，并遵循接口约定的最大值。
- keywords、order_no 等筛选字段仅在该接口支持时定义。
- 新接口查询字段使用 snake_case；维护已有接口时保留其公开参数名称，包括既有 camelCase 参数。
- 查询参数 Serializer 负责校验和规范化输入；分页与查询集的组织方式遵循所在模块的结构。

~~~python
from rest_framework import serializers


class ListParamsSerializer(serializers.Serializer):
    keywords = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        default=20,
    )
    order_no = serializers.CharField(required=False, allow_blank=True)
~~~

响应中的 pagination 字段遵循 `.codex/rules/backend/api-response.md`；查询参数 Serializer 不另行定义响应分页结构。
