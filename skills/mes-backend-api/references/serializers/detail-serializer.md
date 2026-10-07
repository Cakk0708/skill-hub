
# 详情 Serializer

详情字段和命名遵循接口的公开响应契约。新 API 按 `.codex/rules/backend/api-response.md` 中的 snake_case 示例命名；维护既有接口时保留已发布字段名。

- 字段顺序可先列简单标量，再列嵌套或计算字段，便于阅读；接口已有明确字段顺序时以其为准。
- 详情数据按统一响应契约组织，不要无差别序列化全部 Model 字段。

~~~python
class CustomerDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status_label = serializers.CharField(source="get_status_display")
    assigned_user = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_assigned_user(self, obj):
        return {"id": obj.assigned_user_id, "name": obj.assigned_user.name}

    def get_tags(self, obj):
        return list(obj.tags.values("id", "name"))
~~~
