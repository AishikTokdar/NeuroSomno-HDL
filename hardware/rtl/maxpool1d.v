// ============================================================================
// NeuroSomno-HDL: Streaming 1D Max Pooling Module (maxpool1d.v)
// Reduces biosignal temporal dimensionality with configurable window & stride
// ============================================================================

`timescale 1ns / 1ps

module maxpool1d #(
    parameter POOL_SIZE  = 2,
    parameter STRIDE     = 2,
    parameter DATA_WIDTH = 16
) (
    input wire clk,
    input wire rst,
    input wire i_valid,
    input wire signed [DATA_WIDTH-1:0] i_data,
    output reg o_valid,
    output reg signed [DATA_WIDTH-1:0] o_data
);

    reg signed [DATA_WIDTH-1:0] max_reg;
    reg [$clog2(POOL_SIZE+1)-1:0] count;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            max_reg <= -16'sh8000;
            count   <= 0;
            o_valid <= 0;
            o_data  <= 0;
        end else begin
            o_valid <= 0;
            if (i_valid) begin
                if (count == 0) begin
                    max_reg <= i_data;
                    count   <= count + 1;
                end else begin
                    if (i_data > max_reg) begin
                        max_reg <= i_data;
                    end
                    count <= count + 1;
                    if (count == POOL_SIZE - 1) begin
                        o_valid <= 1;
                        if (i_data > max_reg) begin
                            o_data <= i_data;
                        end else begin
                            o_data <= max_reg;
                        end
                        count <= 0;
                        max_reg <= -16'sh8000;
                    end
                end
            end
        end
    end

endmodule
