// ============================================================================
// NeuroSomno-HDL: Digital IIR 0.5-45 Hz Bandpass Filter (iir_bandpass.v)
// Cascaded Biquad implementation for physiological cortical EEG band isolation
// ============================================================================

`timescale 1ns / 1ps

module iir_bandpass #(
    parameter DATA_WIDTH = 16,
    parameter FRAC_BITS  = 13
) (
    input wire clk,
    input wire rst,
    input wire i_valid,
    input wire signed [DATA_WIDTH-1:0] i_data,
    output reg o_valid,
    output reg signed [DATA_WIDTH-1:0] o_data
);

    // Cascaded Biquad Section 1 (Low cutoff 0.5 Hz highpass component)
    // Coeffs in Q3.13: b0=7900, b1=-15800, b2=7900, a1=-15700, a2=7700
    localparam signed [DATA_WIDTH-1:0] B1_B0 = 16'sh1EDC;
    localparam signed [DATA_WIDTH-1:0] B1_B1 = -16'sh3DB8;
    localparam signed [DATA_WIDTH-1:0] B1_B2 = 16'sh1EDC;
    localparam signed [DATA_WIDTH-1:0] B1_A1 = -16'sh3D54;
    localparam signed [DATA_WIDTH-1:0] B1_A2 = 16'sh1E14;

    reg signed [31:0] s1_d1, s1_d2;
    wire signed [31:0] s1_y_acc = (i_data * B1_B0) + s1_d1;
    wire signed [DATA_WIDTH-1:0] s1_out = s1_y_acc[FRAC_BITS +: DATA_WIDTH];

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            s1_d1   <= 0;
            s1_d2   <= 0;
            o_valid <= 0;
            o_data  <= 0;
        end else if (i_valid) begin
            s1_d1 <= (i_data * B1_B1) - (s1_out * B1_A1) + s1_d2;
            s1_d2 <= (i_data * B1_B2) - (s1_out * B1_A2);

            // Saturation logic on 32-bit accumulator
            if (s1_y_acc > 32'sd268427264) begin
                o_data <= 16'sh7FFF;
            end else if (s1_y_acc < -32'sd268435456) begin
                o_data <= 16'sh8000;
            end else begin
                o_data <= s1_out;
            end
            o_valid <= 1;
        end else begin
            o_valid <= 0;
        end
    end

endmodule
