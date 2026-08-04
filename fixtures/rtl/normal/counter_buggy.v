// counter_buggy.v — 故意注入逻辑错误的计数器 DUT（用于 Milestone3 Case B 验收）
//
// 正确行为应为：enable 时在 clk 上升沿 cnt <= cnt + 1。
// 注入错误：enable 时 cnt <= cnt + 2（自检测 testbench 用参考模型比较应输出 mismatch）。
//
// 该文件仅用于验证"testbench 能识别故意注入的 DUT 错误"，不应合并到正式工程。

module counter_buggy #(
    parameter WIDTH = 8
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 enable,
    output reg  [WIDTH-1:0]     cnt
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= {WIDTH{1'b0}};
        end else if (enable) begin
            cnt <= cnt + 2;   // BUG: 应为 +1
        end
    end

endmodule
