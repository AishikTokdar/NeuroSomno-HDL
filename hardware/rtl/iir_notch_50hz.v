// Generated from scipy.signal at fs=128 Hz; causal streaming filter.
module iir_notch_50hz #(parameter DATA_WIDTH=16, FRAC_BITS=13)(
input clk,input rst,input i_valid,input signed [DATA_WIDTH-1:0] i_data,
output o_valid,output signed [DATA_WIDTH-1:0] o_data);
    iir_biquad #(.DATA_WIDTH(DATA_WIDTH),.FRAC_BITS(FRAC_BITS),
.B0(7914),.B1(12236),.B2(7914),.A1(12236),.A2(7637)) section(clk,rst,i_valid,i_data,o_valid,o_data);
endmodule
