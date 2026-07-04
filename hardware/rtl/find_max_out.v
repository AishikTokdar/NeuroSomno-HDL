module find_max_out (
    input clk,
    input rst,
    input i_valid,
    input [15:0] i_data,
    output reg o_valid,
    output reg [3:0] o_class
);
    reg signed [15:0] max_val;
    reg [3:0] max_idx;
    reg [3:0] cnt;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            max_val <= -16'sh8000;
            max_idx <= 0;
            cnt <= 0;
            o_valid <= 0;
            o_class <= 0;
        end else begin
            o_valid <= 0;
            if (i_valid) begin
                if (cnt == 0) begin
                    max_val <= i_data;
                    max_idx <= 0;
                    cnt <= 1;
                end else begin
                    cnt <= cnt + 1;
                    if ($signed(i_data) > $signed(max_val)) begin
                        max_val <= i_data;
                        max_idx <= cnt;
                    end
                    if (cnt == 9) begin
                        cnt <= 0;
                        o_valid <= 1;
                        o_class <= ($signed(i_data) > $signed(max_val)) ? cnt : max_idx;
                    end
                end
            end
        end
    end
end
