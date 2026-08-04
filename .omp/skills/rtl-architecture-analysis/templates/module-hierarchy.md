<!-- 模块层级模板：来自 build_hierarchy.py --json。跨文件实例须注明定义文件。 -->
# 模块层级：<顶层模块名>

## 层级树
```
<top>
 ├─ child_a (instance: u_a) [定义: file_a.sv]
 │   └─ child_a1 (instance: u_a1)
 └─ child_b (instance: u_b)
```

## 实例化明细
| 父模块 | 子模块 | 实例名 | 定义文件 | 参数覆盖 |
|---|---|---|---|---|
| <parent> | <child> | <inst> | <file / 未解析> | <若有> |

## 校验
- [ ] 无循环依赖
- [ ] 每个子模块均能定位定义文件（跨文件未解析者标"未解析"）
