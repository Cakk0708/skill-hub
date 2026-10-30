---
title: Python 模块导入规范
description: Python 模块的 import 分组与排序
applicable_path: "*.py"
---

# 模块导入规范

- 遵循项目配置的 import sorter 和相邻文件的导入顺序。
- 通常按标准库、第三方库、Django/DRF 与项目模块分组；同组导入放在一起，不同组之间空一行。
- 本项目模块可按仓库现有约定区分公共工具、`apps` 内模块和相对导入，不为每个模块机械保留空组。
- 只导入实际使用的对象；修改导入时不要顺带重排无关代码。

```python
from collections.abc import Sequence

from rest_framework import serializers

from utils.date import DateTimeFormatMixin

from apps.SM.models import User

from .models import NodeReview
```
