# Serializer 命名

新增 Serializer 使用资源名加用途后缀。资源模块足够明确时，可以沿用模块内简短名称，例如 ListSerializer 或 DetailSerializer。

| 用途 | 后缀 | 示例 |
|---|---|---|
| 写入 | WriteSerializer | CustomerWriteSerializer |
| 列表项 | ListSerializer | CustomerListSerializer |
| 详情 | DetailSerializer | CustomerDetailSerializer |
| 简要列表项 | SimpleSerializer | CustomerSimpleSerializer |
| 删除请求 | DeleteSerializer | CustomerDeleteSerializer |
| 查询参数 | ParamsSerializer 或 ListParamsSerializer | CustomerParamsSerializer |

同一模块内避免多个含义不同的类都使用无法区分的通用名称。修改已有名称时注意所有导入和调用点。
