// Fixture: parameter with paren default, vectored inline-width ports,
// SystemVerilog always_ff with low-active async reset, and a generated clock.
module param_vectored #(
    parameter WIDTH = 8,
    parameter DEPTH = $clog2(WIDTH)
)(
    input  wire               clk,
    input  wire               rst_n,
    input  wire [WIDTH-1:0]   data_in,
    output reg  [WIDTH-1:0]   data_out
);

    typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;
    state_t state, next_state;

    // FSM: low-active asynchronous reset
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    // Generated clock: divide main clock
    reg clk_div;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            clk_div <= 1'b0;
        else
            clk_div <= ~clk;
    end

    // Synchronous reset example on a different block
    reg [WIDTH-1:0] sync_reg;
    always @(posedge clk) begin
        if (rst)
            sync_reg <= {WIDTH{1'b0}};
        else
            sync_reg <= data_in;
    end

    assign data_out = sync_reg;

endmodule
