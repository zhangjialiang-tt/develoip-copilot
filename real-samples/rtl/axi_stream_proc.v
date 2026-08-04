// Real-world sample (sanitized): AXI-Stream packet processor
//
// 来源: 脱敏自图像处理流水线数据接收模块
// 复杂度: 中等 (参数化位宽 + 状态机 + 同文件子模块实例化 + 生成使能)
// 已知问题:
//   - 内部 en_div 为 clk/2 使能分频, 不是真实时钟; 工具可能启发式误判为生成时钟
//   - 子模块 sync_fifo 与本模块同文件, 跨文件回填不适用
// 用途: 验证 rtl-architecture-analysis 在接近真实复杂度下的实用性
module axi_stream_proc #(
    parameter int DATA_W = 32,
    parameter int DEPTH  = 16
) (
    input  wire                 clk,
    input  wire                 rst_n,
    // AXI-Stream slave
    input  wire                 s_valid,
    input  wire [DATA_W-1:0]    s_data,
    output wire                 s_ready,
    // AXI-Stream master
    output reg                  m_valid,
    output reg  [DATA_W-1:0]    m_data,
    input  wire                 m_ready,
    // status
    output reg  [7:0]           pkt_count
);

    localparam IDLE = 2'd0, RECV = 2'd1, PROC = 2'd2, SEND = 2'd3;
    reg [1:0] state, next_state;

    // 生成使能 (clk/2) — 不是真实时钟, 仅作为使能使用
    reg en_div;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) en_div <= 1'b0;
        else        en_div <= ~en_div;
    end

    // 同文件子模块实例化
    wire [DATA_W-1:0] fifo_q;
    wire               fifo_empty;
    sync_fifo #(.WIDTH(DATA_W), .DEPTH(DEPTH)) u_fifo (
        .clk(clk), .rst_n(rst_n),
        .wr_en(s_valid & s_ready), .din(s_data),
        .rd_en(en_div), .dout(fifo_q), .empty(fifo_empty)
    );

    assign s_ready = !fifo_empty;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= IDLE;
            m_valid   <= 1'b0;
            pkt_count <= 8'd0;
        end else begin
            state <= next_state;
            if (state == SEND && m_ready) begin
                m_valid   <= 1'b1;
                m_data    <= fifo_q;
                pkt_count <= pkt_count + 8'd1;
            end else begin
                m_valid <= 1'b0;
            end
        end
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: if (s_valid)          next_state = RECV;
            RECV: if (!fifo_empty)      next_state = PROC;
            PROC:                       next_state = SEND;
            SEND: if (m_ready)          next_state = (s_valid ? RECV : IDLE);
            default:                    next_state = IDLE;
        endcase
    end
endmodule

module sync_fifo #(
    parameter int WIDTH = 32,
    parameter int DEPTH = 16
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 wr_en,
    input  wire [WIDTH-1:0]     din,
    input  wire                 rd_en,
    output reg  [WIDTH-1:0]     dout,
    output reg                  empty
);
    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [$clog2(DEPTH)-1:0] wptr, rptr;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            empty <= 1'b1; wptr <= 0; rptr <= 0;
        end else begin
            if (wr_en) mem[wptr] <= din;
            if (rd_en && !empty) dout <= mem[rptr];
            if (wr_en && !rd_en) empty <= 1'b0;
            if (!wr_en && rd_en && (rptr == wptr - 1)) empty <= 1'b1;
            if (wr_en) wptr <= wptr + 1'b1;
            if (rd_en && !empty) rptr <= rptr + 1'b1;
        end
    end
endmodule
