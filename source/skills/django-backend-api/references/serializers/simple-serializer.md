# 简要列表 Serializer

简要列表 Serializer 返回满足该页面或组件需要的最小字段集，不自动序列化整个 Model。

- 按接口字段顺序明确声明 Meta.fields。
- 只有需要计算或嵌套数据时才添加相应字段。
- Serializer 的命名遵循 naming.md；新增 API 的列表分页格式遵循 `.codex/rules/backend/api-response.md`。

~~~python
class CustomerSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cust
        fields = ["id", "code", "name"]
~~~
