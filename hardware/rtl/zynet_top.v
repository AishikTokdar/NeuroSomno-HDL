module zynet_top (
    input clk,
    input rst,
    input [15:0] s_axis_tdata,
    input s_axis_tvalid,
    output s_axis_tready,
    input s_axis_tlast,
    input [31:0] S_AXI_AWADDR,
    input S_AXI_AWVALID,
    output S_AXI_AWREADY,
    input [31:0] S_AXI_WDATA,
    input S_AXI_WVALID,
    output S_AXI_WREADY,
    output [1:0] S_AXI_BRESP,
    output S_AXI_BVALID,
    input S_AXI_BREADY,
    input [31:0] S_AXI_ARADDR,
    input S_AXI_ARVALID,
    output S_AXI_ARREADY,
    output [31:0] S_AXI_RDATA,
    output [1:0] S_AXI_RRESP,
    output S_AXI_RVALID,
    input S_AXI_RREADY,
    output intr
);
    wire soft_rst;
    wire start;
    wire [3:0] layer_sel;
    wire [5:0] neuron_sel;
    wire [11:0] waddr;
    wire [15:0] wdata;
    wire wen;
    wire [15:0] bias_wdata;
    wire bias_wen;
    wire [3:0] out_class;
    wire [15:0] ahi_count;
    wire [1:0] ahi_sev;
    wire ahi_alarm_intr;
    axi_lite_wrapper axil (
        .S_AXI_ACLK(clk),
        .S_AXI_ARESETN(!rst),
        .S_AXI_AWADDR(S_AXI_AWADDR),
        .S_AXI_AWVALID(S_AXI_AWVALID),
        .S_AXI_AWREADY(S_AXI_AWREADY),
        .S_AXI_WDATA(S_AXI_WDATA),
        .S_AXI_WVALID(S_AXI_WVALID),
        .S_AXI_WREADY(S_AXI_WREADY),
        .S_AXI_BRESP(S_AXI_BRESP),
        .S_AXI_BVALID(S_AXI_BVALID),
        .S_AXI_BREADY(S_AXI_BREADY),
        .S_AXI_ARADDR(S_AXI_ARADDR),
        .S_AXI_ARVALID(S_AXI_ARVALID),
        .S_AXI_ARREADY(S_AXI_ARREADY),
        .S_AXI_RDATA(S_AXI_RDATA),
        .S_AXI_RRESP(S_AXI_RRESP),
        .S_AXI_RVALID(S_AXI_RVALID),
        .S_AXI_RREADY(S_AXI_RREADY),
        .o_reset(soft_rst),
        .o_start(start),
        .o_layer_sel(layer_sel),
        .o_neuron_sel(neuron_sel),
        .o_waddr(waddr),
        .o_wdata(wdata),
        .o_wen(wen),
        .o_bias_wdata(bias_wdata),
        .o_bias_wen(bias_wen),
        .i_class(out_class),
        .i_done(out_done),
        .i_ahi_count(ahi_count),
        .i_ahi_sev(ahi_sev),
        .intr(intr)
    );
    ahi_tracker ahi_inst (
        .clk(clk),
        .rst(net_rst),
        .i_valid(out_done),
        .i_class(out_class),
        .clr_counter(soft_rst),
        .o_ahi_count(ahi_count),
        .o_severity(ahi_sev),
        .o_alarm_intr(ahi_alarm_intr)
    );
    reg running;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            running <= 0;
        end else begin
            if (start) begin
                running <= 1;
            end else if (out_done) begin
                running <= 0;
            end
        end
    end
    assign s_axis_tready = running;
    wire net_rst = rst || soft_rst;
    wire l1_valid;
    wire [15:0] l1_data;
    layer1 l1 (
        .clk(clk),
        .rst(net_rst),
        .i_valid(s_axis_tvalid && s_axis_tready),
        .i_data(s_axis_tdata),
        .o_valid(l1_valid),
        .o_data(l1_data),
        .wen(wen),
        .waddr(waddr),
        .wdata(wdata),
        .layer_sel(layer_sel),
        .neuron_sel(neuron_sel),
        .bias_wen(bias_wen),
        .bias_wdata(bias_wdata)
    );
    wire l2_valid;
    wire [15:0] l2_data;
    layer2 l2 (
        .clk(clk),
        .rst(net_rst),
        .i_valid(l1_valid),
        .i_data(l1_data),
        .o_valid(l2_valid),
        .o_data(l2_data),
        .wen(wen),
        .waddr(waddr),
        .wdata(wdata),
        .layer_sel(layer_sel),
        .neuron_sel(neuron_sel),
        .bias_wen(bias_wen),
        .bias_wdata(bias_wdata)
    );
    wire l3_valid;
    wire [15:0] l3_data;
    layer3 l3 (
        .clk(clk),
        .rst(net_rst),
        .i_valid(l2_valid),
        .i_data(l2_data),
        .o_valid(l3_valid),
        .o_data(l3_data),
        .wen(wen),
        .waddr(waddr),
        .wdata(wdata),
        .layer_sel(layer_sel),
        .neuron_sel(neuron_sel),
        .bias_wen(bias_wen),
        .bias_wdata(bias_wdata)
    );
    wire l4_valid;
    wire [15:0] l4_data;
    layer4 l4 (
        .clk(clk),
        .rst(net_rst),
        .i_valid(l3_valid),
        .i_data(l3_data),
        .o_valid(l4_valid),
        .o_data(l4_data),
        .wen(wen),
        .waddr(waddr),
        .wdata(wdata),
        .layer_sel(layer_sel),
        .neuron_sel(neuron_sel),
        .bias_wen(bias_wen),
        .bias_wdata(bias_wdata)
    );
    find_max_out fmax (
        .clk(clk),
        .rst(net_rst),
        .i_valid(l4_valid),
        .i_data(l4_data),
        .o_valid(out_done),
        .o_class(out_class)
    );
endmodule
