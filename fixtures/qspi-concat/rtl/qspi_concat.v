module qspi_concat #(parameter FIXED = 1'b0) (
    input  logic [7:0] b0,
    input  logic [7:0] b1,
    input  logic [7:0] b2,
    input  logic [7:0] b3,
    output logic [31:0] word
);
    // Baseline A reproduces the defect: lanes 0/1 and 2/3 are swapped.
    // Baseline B is the authorized fix and preserves QSPI bus order.
    always_comb begin
        if (FIXED)
            word = {b0, b1, b2, b3};
        else
            word = {b1, b0, b3, b2};
    end
endmodule
