module tb_neuron;
    reg clk;
    reg rst;
    reg i_valid;
    reg [15:0] i_data;
    wire o_valid;
    wire [15:0] o_data;
    reg wen;
    reg [11:0] waddr;
    reg [15:0] wdata;
    reg bias_wen;
    reg [15:0] bias_wdata;
    neuron #(
        .layerNo(1),
        .neuronNo(0),
        .numWeight(3),
        .mifFile(""),
        .biasMifFile(""),
        .actType("relu")
    ) uut (
        .clk(clk),
        .rst(rst),
        .i_valid(i_valid),
        .i_data(i_data),
        .o_valid(o_valid),
        .o_data(o_data),
        .wen(wen),
        .waddr(waddr),
        .wdata(wdata),
        .bias_wen(bias_wen),
        .bias_wdata(bias_wdata)
    );
    always #5 clk = ~clk;
    initial begin
        clk = 0;
        rst = 1;
        i_valid = 0;
        i_data = 0;
        wen = 0;
        waddr = 0;
        wdata = 0;
        bias_wen = 0;
        bias_wdata = 0;
        #20;
        rst = 0;
        #10;
        wen = 1;
        waddr = 0; wdata = 16'h2000; #10;
        waddr = 1; wdata = 16'hC000; #10;
        waddr = 2; wdata = 16'h1000; #10;
        wen = 0;
        bias_wen = 1;
        bias_wdata = 16'h0800; #10;
        bias_wen = 0;
        #20;
        i_valid = 1;
        i_data = 16'h2000; #10;
        i_data = 16'h1000; #10;
        i_data = 16'h4000; #10;
        i_valid = 0;
        #100;
        $finish;
    end
end
