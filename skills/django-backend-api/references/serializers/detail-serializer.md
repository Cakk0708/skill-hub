
# 详情 Serializer

详情 Serializer 声明使用 Python `snake_case`，renderer 输出的公开 JSON 键使用 `.codex/rules/backend/api-response.md` 规定的 `camelCase`。维护既有接口时保留已发布的线上字段名；不要把线上命名规则与 Serializer 内部属性名混为一谈。

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
