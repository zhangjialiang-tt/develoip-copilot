<!-- 接口清单模板：端口与参数来自 extract_interfaces.py --json。字段与工具输出一一对应。 -->
# 接口清单：<顶层模块名>

## 参数（parameters）
| 模块 | 参数名 | 默认值 | 说明 |
|---|---|---|---|
| <mod> | <name> | <default> | <可选> |

## 端口（ports）
| 模块 | 方向 | 位宽 | 信号名 | 关联时钟/复位 | 备注 |
|---|---|---|---|---|---|
| <mod> | input/output/inout | <[msb:lsb]> | <name> | <clk/rst 关联> | <可选> |

## 校验
- [ ] 端口数与 RTL 实际定义一致（以 extract_interfaces 输出为准）
- [ ] 位宽已解析；未解析者标 `[0:0]` 并在备注写"待确认"
