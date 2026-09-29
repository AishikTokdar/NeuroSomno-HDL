module relu (
    input signed [31:0] i_data,
    output reg [15:0] o_data
);
    always @(*) begin
        if (i_data <= 0) begin
            o_data = 16'h0000;
        end else if (i_data > 32767) begin
            o_data = 16'h7FFF;
        end else begin
            o_data = i_data[15:0];
        end
    end
endmodule
