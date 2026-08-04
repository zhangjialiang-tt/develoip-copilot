# Fixtures 约定

## 目录结构

每个 Skill 的 fixtures 按场景类型组织：

```
fixtures/<skill-name>/
├── normal/       # 正常输入
├── error/        # 包含已知错误的输入
├── incomplete/   # 不完整输入
└── real/         # 真实工程样例
```

## 原则

- normal：输入完整、格式正确、预期输出明确
- error：包含已知错误类型，用于验证 Skill 能识别问题
- incomplete：缺少关键字段，用于验证阻断逻辑
- real：来自实际项目，记录成功/失败/工具缺口

## 状态

当前为空，待各 Skill 实现时补充。
