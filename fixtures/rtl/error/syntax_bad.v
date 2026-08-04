// Fixture: 已知语法错误 (error class)
// 用途: 验证工具在语法错误输入下不崩溃、不伪造成功结果。
// 已知错误:
//   1) module 端口列表的 ")" 未闭合
//   2) 缺少 endmodule
// 设计说明: 轻量正则工具不做语法编译, 无法"报告语法错误";
//           本 fixture 用于验证失败处理路径的鲁棒性, 而非语法检查能力。
module syntax_bad (
    input  wire       clk,
    input  wire       rst_n
    output reg  [7:0] q
    // 注: 此处缺少闭合的 ")"
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            q <= 8'd0;
        else
            q <= q + 8'd1;
    // 缺少 endmodule
