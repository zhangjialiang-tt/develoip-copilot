// Fixture: 不完整输入 (incomplete class) - 截断
// 用途: 验证工具在模块声明被截断、缺少 body 与 endmodule 时不崩溃、
//       不伪造成功, 并返回有界结果。
module truncated (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] q
