// Fixture: top module instantiates `child`, which is defined in another file.
module top (
    input  wire       clk,
    input  wire       rst_n,
    output wire [7:0] result
);

    child u_child (
        .clk   (clk),
        .rst_n (rst_n),
        .result(result)
    );

endmodule
