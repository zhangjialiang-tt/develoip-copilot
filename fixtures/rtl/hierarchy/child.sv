// Fixture: child module, instantiated by top.sv (cross-file resolution).
module child (
    input  wire       clk,
    input  wire       rst_n,
    output wire [7:0] result
);

    assign result = 8'd0;

endmodule
