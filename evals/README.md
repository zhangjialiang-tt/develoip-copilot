# Evals 约定

## 目录结构

```
evals/<skill-name>/
├── eval_<name>.py     # 评估脚本
└── fixtures/          # 评估使用的测试数据（可选，可引用 fixtures/）
```

## 原则

- 每个 Skill 至少包含 4 类 fixture（normal/error/incomplete/real）
- 评估脚本应可独立运行（pytest）
- 评估结果应有明确的 PASS/FAIL 输出

## 状态

当前为空，待各 Skill 实现时补充。
