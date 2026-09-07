module neuron #(
    parameter layerNo = 1,
    parameter neuronNo = 0,
    parameter numWeight = 784,
    parameter mifFile = "",
    parameter biasMifFile = "",
    parameter actType = "relu"
) (
    input clk,
    input rst,
    input i_valid,
    input signed [15:0] i_data,
    output reg o_valid,
    output reg [15:0] o_data,
    input wen,
    input [11:0] waddr,
    input signed [15:0] wdata,
    input bias_wen,
    input signed [15:0] bias_wdata
);
    reg [11:0] raddr;
    wire signed [15:0] w_data;
    weight_memory #(
        .numWeight(numWeight),
        .mifFile(mifFile)
    ) wm (
        .clk(clk),
        .ren(i_valid),
        .raddr(raddr),
        .rdata(w_data),
        .wen(wen),
        .waddr(waddr),
        .wdata(wdata)
    );
    reg signed [15:0] bias_mem [0:0];
    initial begin
        if (biasMifFile != "") begin
            $readmemb(biasMifFile, bias_mem);
        end
    end
    always @(posedge clk) begin
        if (bias_wen) begin
            bias_mem[0] <= bias_wdata;
        end
    end
    wire signed [15:0] bias = bias_mem[0];
    reg signed [31:0] acc;
    reg [11:0] cnt;
    reg [1:0] state;
    reg signed [15:0] s_x_reg;
    wire signed [15:0] s_w = w_data;
    reg signed [31:0] prod;
    reg prod_valid;
    always @(posedge clk) begin
        if (i_valid) begin
            s_x_reg <= i_data;
            prod <= (i_data * s_w) >>> 13;
        end
    end
    always @(posedge clk) begin
        prod_valid <= i_valid;
    end
    reg signed [31:0] acc_bias;
    wire signed [15:0] acc_bias_sat = (acc_bias > 32767) ? 16'h7FFF :
                                      (acc_bias < -32768) ? 16'h8000 :
                                      acc_bias[15:0];
    wire [15:0] relu_out;
    relu r_inst (
        .i_data(acc_bias),
        .o_data(relu_out)
    );
    wire [15:0] sig_out;
    sig_rom srom (
        .clk(clk),
        .i_data(acc_bias_sat),
        .o_data(sig_out)
    );
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            raddr <= 0;
            acc <= 0;
            cnt <= 0;
            state <= 0;
            o_valid <= 0;
            o_data <= 0;
            acc_bias <= 0;
        end else begin
            o_valid <= 0;
            if (state == 0) begin
                if (i_valid) begin
                    raddr <= raddr + 1;
                end
                if (prod_valid) begin
                    acc <= acc + prod;
                    cnt <= cnt + 1;
                    if (cnt == numWeight - 1) begin
                        state <= 1;
                        acc_bias <= acc + prod + {{16{bias[15]}}, bias};
                    end
                end
            end else if (state == 1) begin
                if (actType == "relu") begin
                    o_data <= relu_out;
                    o_valid <= 1;
                    raddr <= 0;
                    acc <= 0;
                    cnt <= 0;
                    state <= 0;
                end else begin
                    state <= 2;
                end
            end else if (state == 2) begin
                o_data <= sig_out;
                o_valid <= 1;
                raddr <= 0;
                acc <= 0;
                cnt <= 0;
                state <= 0;
            end
        end
endmodule
