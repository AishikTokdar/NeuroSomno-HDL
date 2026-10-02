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
    localparam [7:0] layer_digit = 48 + layerNo;
    localparam [7:0] tens_digit = 48 + neuronNo/10;
    localparam [7:0] ones_digit = 48 + neuronNo%10;
    localparam [8*32-1:0] resolved_mif_file = neuronNo<10 ?
        {"w_",layer_digit,"_",ones_digit,".mif"} :
        {"w_",layer_digit,"_",tens_digit,ones_digit,".mif"};
    initial begin
        if (mifFile != "") begin
            $readmemb(mifFile, mem);
        end else begin
            $readmemb(resolved_mif_file, mem);
        end
    end
    always @(posedge clk) begin
        if (ren && raddr < numWeight) begin
            rdata <= mem[raddr];
        end
        if (wen && waddr < numWeight) begin
            mem[waddr] <= wdata;
        end
    end
endmodule
