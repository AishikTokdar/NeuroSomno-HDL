// Binary logits, normal=0, apnea=1. Ties choose normal (numpy argmax).
module find_max_out(input clk,input rst,input i_valid,input [15:0] i_data,
                    output reg o_valid,output reg [3:0] o_class);
    reg have_first;
    reg signed [15:0] first;
    always @(posedge clk or posedge rst) begin
        if (rst) begin have_first<=0; first<=0; o_valid<=0; o_class<=0; end
        else begin
            o_valid<=0;
            if(i_valid) begin
                if(!have_first) begin first<=i_data; have_first<=1; end
                else begin
                    have_first<=0; o_valid<=1;
                    o_class<=($signed(i_data)>first) ? 4'd1 : 4'd0;
                end
            end
        end
    end
endmodule
