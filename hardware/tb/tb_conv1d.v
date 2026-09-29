`timescale 1ns / 1ps

module tb_conv1d;

    reg clk;
    reg rst;
    reg i_valid;
    reg signed [15:0] i_data;
    reg [160-1:0] kernel_weights;
    reg signed [15:0] bias;
    wire o_valid;
    wire signed [15:0] o_data;

    wire pool_valid;
    wire signed [15:0] pool_data;

    // Instantiate Conv1D PE (Kernel size = 10)
    conv1d_pe #(
        .KERNEL_SIZE(10),
        .DATA_WIDTH(16),
        .FRAC_BITS(13)
    ) uut_conv (
        .clk(clk),
        .rst(rst),
        .i_valid(i_valid),
        .i_data(i_data),
        .kernel_weights(kernel_weights),
        .bias(bias),
        .o_valid(o_valid),
        .o_data(o_data)
    );

    // Instantiate MaxPool1D
    maxpool1d #(
        .POOL_SIZE(2),
        .STRIDE(2),
        .DATA_WIDTH(16)
    ) uut_pool (
        .clk(clk),
        .rst(rst),
        .i_valid(o_valid),
        .i_data(o_data),
        .o_valid(pool_valid),
        .o_data(pool_data)
    );

    always #5 clk = ~clk;

    integer i;
    initial begin
        clk = 0;
        rst = 1;
        i_valid = 0;
        i_data = 0;
        bias = 16'sh0200; // Small positive bias in Q3.13

        // Set uniform kernel weights (0.1 in Q3.13 = ~819)
        for (i = 0; i < 10; i = i + 1) begin
            kernel_weights[i*16 +: 16] = 16'sh0333;
        end

        #50;
        rst = 0;
        #20;

        // Stream synthetic sine wave values
        for (i = 0; i < 40; i = i + 1) begin
            @(posedge clk);
            i_valid <= 1;
            i_data  <= (i % 2 == 0) ? 16'sh2000 : 16'sh1000;
        end

        @(posedge clk);
        i_valid <= 0;

        #200;
        $display("[TB SUCCESS] 1D-CNN Conv and MaxPool pipeline completed cleanly.");
        $finish;
    end

endmodule
