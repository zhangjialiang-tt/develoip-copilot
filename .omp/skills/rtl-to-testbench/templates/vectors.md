# 测试向量说明 — <DUT 顶层模块名>

> 当验证计划选择"定向测试向量"或"向量比对"时使用。自由激励可不填本文件。

## 向量格式

- 文件位置：`<output_dir>/vectors/<name>.vec`
- 字段顺序：`<cycle>, <port_in>=<value>, <expected_port_out>=<value>`
- 注释行以 `#` 开头

## 向量清单

| 向量文件 | 对应用例 | 覆盖点 |
| --- | --- | --- |
| `<name>.vec` | <TCx> | <边界/典型> |

## 示例

```text
# cycle  port_in  expected_port_out
0       0        0
1       1        1
2       1        2
```

## 来源与置信度

- 来源：<用户已知向量 / 参考模型生成 / 推断>
- 置信度：<高/中/低>（低置信度须标注依据，建议补充 self-check 而非依赖固定向量）
