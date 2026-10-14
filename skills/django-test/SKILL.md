---
name: django-test
description: |
  Django 测试相关技能
---

## 工具约定

- 使用 `pytest` 进行测试
- 使用 `factory_boy` 生成测试数据
- 使用 `coverage` 进行代码覆盖率统计

## 结构约定

- **标准目录结构**:

```
backend/
├── manage.py
├── pytest.ini
├── conftest.py
│
├── apps/
│   ├── material/
│   │   ├── models.py
│   │   ├── services.py
│   │   └── tests/
│   │       ├── test_models.py
│   │       └── test_services.py
│   │
│   ├── production/
│   │   ├── models.py
│   │   ├── services.py
│   │   └── tests/
│   │       ├── test_models.py
│   │       └── test_services.py
│   │
│   └── inventory/
│       ├── models.py
│       ├── services.py
│       └── tests/
│           ├── test_models.py
│           └── test_services.py
│
└── tests/
    ├── integration/
    │   ├── test_production_flow.py
    │   └── test_inventory_flow.py
    └── fixtures/
        └── common_data.py
```