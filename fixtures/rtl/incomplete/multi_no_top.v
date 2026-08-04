// Fixture: 不完整输入 (incomplete class) - 多模块无单一顶层
// 用途: 验证工具在存在多个平级模块、缺少明确顶层时不臆造顶层,
//       正确列出所有模块供调用方(skill/agent)判定。
module fifo_ctrl (
    input  wire clk,
    input  wire rst_n,
    output reg       full
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) full <= 1'b0;
    end
endmodule

module arbiter #(
    parameter integer IDX = 2
) (
    input  wire clk,
    input  wire rst_n,
    output reg  [IDX-1:0] grant
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) grant <= {IDX{1'b0}};
    end
endmodule

module crc8 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] din,
    output reg  [7:0] dout
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) dout <= 8'h0;
    end
endmodule
