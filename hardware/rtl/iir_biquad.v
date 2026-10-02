// Direct-form II transposed section. Coefficients and samples use Q3.13.
// Saturate before feedback; wide state prevents overflow before output clamping.
module iir_biquad #(
    parameter DATA_WIDTH=16, FRAC_BITS=13,
    parameter signed [31:0] B0=8192, B1=0, B2=0, A1=0, A2=0
)(input clk,input rst,input i_valid,
  input signed [DATA_WIDTH-1:0] i_data,
  output reg o_valid, output reg signed [DATA_WIDTH-1:0] o_data);
    reg signed [63:0] d1,d2;
    wire signed [63:0] y_acc = i_data * B0 + d1;
    wire signed [63:0] shifted = y_acc >>> FRAC_BITS;
    localparam signed [63:0] HI = (64'sd1 << (DATA_WIDTH-1))-1;
    localparam signed [63:0] LO = -(64'sd1 << (DATA_WIDTH-1));
    wire signed [DATA_WIDTH-1:0] y = shifted>HI ? HI : shifted<LO ? LO : shifted;
    always @(posedge clk or posedge rst) begin
        if(rst) begin d1<=0; d2<=0; o_valid<=0; o_data<=0; end
        else begin
            o_valid<=i_valid;
            if(i_valid) begin
                o_data<=y;
                d1<=i_data*B1-y*A1+d2;
                d2<=i_data*B2-y*A2;
            end
        end
    end
endmodule
