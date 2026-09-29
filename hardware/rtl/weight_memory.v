module weight_memory #(
    parameter numWeight = 784,
    parameter layerNo = 1,
    parameter neuronNo = 0,
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
    reg [8*32-1:0] resolved_mif_file;
    initial begin
        if (mifFile != "") begin
            $readmemb(mifFile, mem);
        end else begin
            $sformat(resolved_mif_file, "w_%0d_%0d.mif", layerNo, neuronNo);
            $readmemb(resolved_mif_file, mem);
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
endmodule
