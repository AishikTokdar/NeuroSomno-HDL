// Generated from scipy.signal at fs=128 Hz; causal streaming filter.
module iir_bandpass #(parameter DATA_WIDTH=16, FRAC_BITS=13)(
input clk,input rst,input i_valid,input signed [DATA_WIDTH-1:0] i_data,
output o_valid,output signed [DATA_WIDTH-1:0] o_data);
    wire [4:0] valid;
    wire signed [DATA_WIDTH-1:0] data [0:4];
    assign valid[0]=i_valid; assign data[0]=i_data;
    assign o_valid=valid[4]; assign o_data=data[4];
    iir_biquad #(.DATA_WIDTH(DATA_WIDTH),.FRAC_BITS(FRAC_BITS),.B0(2207),.B1(4413),.B2(2207),.A1(5527),.A2(1195)) section_0(clk,rst,valid[0],data[0],valid[1],data[1]);
    iir_biquad #(.DATA_WIDTH(DATA_WIDTH),.FRAC_BITS(FRAC_BITS),.B0(8192),.B1(16384),.B2(8192),.A1(7468),.A2(4368)) section_1(clk,rst,valid[1],data[1],valid[2],data[2]);
    iir_biquad #(.DATA_WIDTH(DATA_WIDTH),.FRAC_BITS(FRAC_BITS),.B0(8192),.B1(-16384),.B2(8192),.A1(-16013),.A2(7826)) section_2(clk,rst,valid[2],data[2],valid[3],data[3]);
    iir_biquad #(.DATA_WIDTH(DATA_WIDTH),.FRAC_BITS(FRAC_BITS),.B0(8192),.B1(-16384),.B2(8192),.A1(-16228),.A2(8041)) section_3(clk,rst,valid[3],data[3],valid[4],data[4]);
endmodule
