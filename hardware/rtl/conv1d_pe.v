// ============================================================================
// NeuroSomno-HDL: Pipelined 1D Convolution Processing Element (conv1d_pe.v)
// Computes streaming 1D convolution over biosignal sliding window in hardware
// ============================================================================

`timescale 1ns / 1ps

module conv1d_pe #(
    parameter KERNEL_SIZE = 10,
    parameter DATA_WIDTH  = 16,
    parameter FRAC_BITS   = 13
) (
    input wire clk,
    input wire rst,
    input wire i_valid,
    input wire signed [DATA_WIDTH-1:0] i_data,
    input wire [DATA_WIDTH*KERNEL_SIZE-1:0] kernel_weights,  // Packed 16-bit Q3.13 weights
    input wire signed [DATA_WIDTH-1:0] bias,
    output reg o_valid,
    output reg signed [DATA_WIDTH-1:0] o_data
);

    // Sliding window sample buffer (shift register)
    reg signed [DATA_WIDTH-1:0] window [0:KERNEL_SIZE-1];
    reg [$clog2(KERNEL_SIZE+1)-1:0] fill_count;
    reg window_full;

    // Unpack weights into internal array
    wire signed [DATA_WIDTH-1:0] weights [0:KERNEL_SIZE-1];
    genvar k;
    generate
        for (k = 0; k < KERNEL_SIZE; k = k + 1) begin : g_unpack_weights
            assign weights[k] = kernel_weights[(k+1)*DATA_WIDTH-1 : k*DATA_WIDTH];
        end
    endgenerate

    // Stage 1: Shift register updates on each valid input
    integer i;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            fill_count <= 0;
            window_full <= 0;
            for (i = 0; i < KERNEL_SIZE; i = i + 1) begin
                window[i] <= 0;
            end
        end else if (i_valid) begin
            // Shift older samples rightward, insert newest at index 0
            for (i = KERNEL_SIZE - 1; i > 0; i = i - 1) begin
                window[i] <= window[i-1];
            end
            window[0] <= i_data;

            if (fill_count < KERNEL_SIZE) begin
                fill_count <= fill_count + 1;
                if (fill_count == KERNEL_SIZE - 1) begin
                    window_full <= 1;
                end
            end
        end
    end

    // Stage 2: Parallel Multiplication Tree (Registered)
    reg signed [31:0] products [0:KERNEL_SIZE-1];
    reg prod_valid;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            prod_valid <= 0;
            for (i = 0; i < KERNEL_SIZE; i = i + 1) begin
                products[i] <= 0;
            end
        end else begin
            prod_valid <= i_valid && window_full;
            if (i_valid && window_full) begin
                for (i = 0; i < KERNEL_SIZE; i = i + 1) begin
                    products[i] <= (window[i] * weights[i]) >>> FRAC_BITS;
                end
            end
        end
    end

    // Stage 3: Accumulation & Clamping (Registered)
    reg signed [31:0] sum_acc;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            o_valid <= 0;
            o_data  <= 0;
            sum_acc <= 0;
        end else if (prod_valid) begin
            sum_acc = {{16{bias[DATA_WIDTH-1]}}, bias};
            for (i = 0; i < KERNEL_SIZE; i = i + 1) begin
                sum_acc = sum_acc + products[i];
            end

            // ReLU zero-clipping + 16-bit signed saturation
            if (sum_acc < 0) begin
                o_data <= 16'sh0000;
            end else if (sum_acc > 32767) begin
                o_data <= 16'sh7FFF;
            end else begin
                o_data <= sum_acc[DATA_WIDTH-1:0];
            end
            o_valid <= 1;
        end else begin
            o_valid <= 0;
        end
    end

endmodule
