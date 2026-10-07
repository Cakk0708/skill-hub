# 列表 Serializer

列表 Serializer 只表示列表项字段，不负责分页响应外层。新增 API 的分页结构遵循 `.codex/rules/backend/api-response.md`；已有接口保持原契约。

- 明确声明字段时，简单标量字段放在嵌套或计算字段之前，便于阅读。
- ModelSerializer 的 Meta.fields 顺序就是输出顺序；按接口字段顺序维护。
- 字段是否能通过查询集取得，属于查询优化和数据建模问题，不要仅因使用 SerializerMethodField 就视为错误。

~~~python
class CustomerListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status_label = serializers.CharField(source="get_status_display")

    class Meta:
        model = Cust
        fields = ["id", "name", "status_label"]
~~~
