module weight_memory #(
    parameter numWeight = 784,
    parameter mifFile = ""
) (
    input clk,
    input ren,
    input [11:0] raddr,
    output reg [15:0] rdata,
    input wen,
    input [11:0] waddr,
    input [15:0] wdata
);
    reg [15:0] mem [0:numWeight-1];
    initial begin
        if (mifFile != "") begin
            $readmemb(mifFile, mem);
        end
    end
    always @(posedge clk) begin
        if (ren) begin
            rdata <= mem[raddr];
        end
        if (wen) begin
            mem[waddr] <= wdata;
        end
    end
end
