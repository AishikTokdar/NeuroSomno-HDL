// ============================================================================
// NeuroSomno-HDL: Digital IIR 50 Hz Notch Filter Core (iir_notch_50hz.v)
// Suppresses AC powerline hum at fs = 128 Hz in Direct-Form II Transposed
// ============================================================================

`timescale 1ns / 1ps

module iir_notch_50hz #(
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

    // Filter Coefficients in Q3.13 format for fs=128Hz, f0=50Hz, Q=35
    // b0 = 0.9576 (~+7845), b1 = 1.2530 (~+10265), b2 = 0.9576 (~+7845)
    // a1 = -1.2530 (~-10265), a2 = -0.9152 (~-7497)
    localparam signed [DATA_WIDTH-1:0] COEFF_B0 = 16'sh1EA5;
    localparam signed [DATA_WIDTH-1:0] COEFF_B1 = 16'sh2819;
    localparam signed [DATA_WIDTH-1:0] COEFF_B2 = 16'sh1EA5;
    localparam signed [DATA_WIDTH-1:0] COEFF_A1 = -16'sh2819;
    localparam signed [DATA_WIDTH-1:0] COEFF_A2 = -16'sh1D49;

    // Direct-Form II Transposed Delay Registers
    reg signed [31:0] d1;
    reg signed [31:0] d2;

    wire signed [31:0] y_acc;
    wire signed [31:0] b0_x = (i_data * COEFF_B0);
    assign y_acc = b0_x + d1;

    wire signed [DATA_WIDTH-1:0] y_val = y_acc[FRAC_BITS +: DATA_WIDTH];

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            d1      <= 0;
            d2      <= 0;
            o_valid <= 0;
            o_data  <= 0;
        end else if (i_valid) begin
            // Transposed state updates:
            // d1 <= b1*x - a1*y + d2
            // d2 <= b2*x - a2*y
            d1 <= (i_data * COEFF_B1) - (y_val * COEFF_A1) + d2;
            d2 <= (i_data * COEFF_B2) - (y_val * COEFF_A2);

            // Saturation logic
            if (y_acc > 32'sh0FFFFFFF) begin
                o_data <= 16'sh7FFF;
            end else if (y_acc < -32'sh10000000) begin
                o_data <= 16'sh8000;
            end else begin
                o_data <= y_val;
            end
            o_valid <= 1;
        end else begin
            o_valid <= 0;
        end
    end

endmodule
