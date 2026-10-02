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

    reg signed [DATA_WIDTH-1:0] history [0:POOL_SIZE-1];
    reg signed [DATA_WIDTH-1:0] best;
    integer fill, countdown, j;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            fill <= 0; countdown <= 0; o_valid <= 0; o_data <= 0;
            for(j=0;j<POOL_SIZE;j=j+1) history[j]<=0;
        end else begin
            o_valid <= 0;
            if(i_valid) begin
                for(j=POOL_SIZE-1;j>0;j=j-1) history[j]<=history[j-1];
                history[0]<=i_data;
                if(fill<POOL_SIZE) fill<=fill+1;
                if(fill>=POOL_SIZE-1) begin
                    if(countdown==0) begin
                        best=i_data;
                        for(j=0;j<POOL_SIZE-1;j=j+1)
                            if(history[j]>best) best=history[j];
                        o_data<=best; o_valid<=1; countdown<=STRIDE-1;
                    end else countdown<=countdown-1;
                end
            end
        end
    end
endmodule
