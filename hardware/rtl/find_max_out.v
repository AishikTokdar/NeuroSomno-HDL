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
                    // Update running max for indices 1..8 (cnt holds current index)
                    if ($signed(i_data) > $signed(max_val)) begin
                        max_val <= i_data;
                        max_idx <= cnt;
                    end
                    if (cnt == 9) begin
                        // Final element: decide winner then reset for next sample
                        cnt <= 0;
                        o_valid <= 1;
                        // Map highest firing output node to binary clinical class:
                        // Neuron 9 corresponds to Apnea (1); Neuron 2 / default corresponds to Normal (0)
                        if ($signed(i_data) > $signed(max_val)) begin
                            o_class <= 4'd1;
                        end else begin
                            o_class <= (max_idx == 4'd9) ? 4'd1 : 4'd0;
                        end
                    end else begin
                        cnt <= cnt + 1;
                    end
                end
            end
        end
    end
endmodule
