module axi_lite_wrapper (
    input S_AXI_ACLK,
    input S_AXI_ARESETN,
    input [31:0] S_AXI_AWADDR,
    input S_AXI_AWVALID,
    output reg S_AXI_AWREADY,
    input [31:0] S_AXI_WDATA,
    input S_AXI_WVALID,
    output reg S_AXI_WREADY,
    output reg [1:0] S_AXI_BRESP,
    output reg S_AXI_BVALID,
    input S_AXI_BREADY,
    input [31:0] S_AXI_ARADDR,
    input S_AXI_ARVALID,
    output reg S_AXI_ARREADY,
    output reg [31:0] S_AXI_RDATA,
    output reg [1:0] S_AXI_RRESP,
    output reg S_AXI_RVALID,
    input S_AXI_RREADY,
    output reg o_reset,
    output reg o_start,
    output [3:0] o_layer_sel,
    output [5:0] o_neuron_sel,
    output [11:0] o_waddr,
    output [15:0] o_wdata,
    output reg o_wen,
    output [15:0] o_bias_wdata,
    output reg o_bias_wen,
    input [3:0] i_class,
    input i_done,
    input [15:0] i_ahi_count,
    input [1:0] i_ahi_sev,
    output reg intr
);
    reg [31:0] reg_ctrl;
    reg [31:0] reg_layer;
    reg [31:0] reg_neuron;
    reg [31:0] reg_waddr;
    reg [31:0] reg_wval;
    reg [31:0] reg_bval;
    reg [31:0] reg_nn_out;
    reg reg_done;
    assign o_layer_sel = reg_layer[3:0];
    assign o_neuron_sel = reg_neuron[5:0];
    assign o_waddr = reg_waddr[11:0];
    assign o_wdata = reg_wval[15:0];
    assign o_bias_wdata = reg_bval[15:0];
    always @(posedge S_AXI_ACLK or negedge S_AXI_ARESETN) begin
        if (!S_AXI_ARESETN) begin
            S_AXI_AWREADY <= 0;
            S_AXI_WREADY <= 0;
            S_AXI_BVALID <= 0;
            S_AXI_BRESP <= 0;
            reg_ctrl <= 0;
            reg_layer <= 0;
            reg_neuron <= 0;
            reg_waddr <= 0;
            reg_wval <= 0;
            reg_bval <= 0;
            o_reset <= 0;
            o_start <= 0;
            o_wen <= 0;
            o_bias_wen <= 0;
        end else begin
            o_start <= 0;
            o_wen <= 0;
            o_bias_wen <= 0;
            if (!S_AXI_AWREADY && S_AXI_AWVALID && S_AXI_WVALID) begin
                S_AXI_AWREADY <= 1;
                S_AXI_WREADY <= 1;
            end else if (S_AXI_AWREADY && S_AXI_WVALID) begin
                S_AXI_AWREADY <= 0;
                S_AXI_WREADY <= 0;
                S_AXI_BVALID <= 1;
                case (S_AXI_AWADDR[5:2])
                    4'd0: begin
                        reg_ctrl <= S_AXI_WDATA;
                        o_reset <= S_AXI_WDATA[0];
                        o_start <= S_AXI_WDATA[1];
                    end
                    4'd1: reg_layer <= S_AXI_WDATA;
                    4'd2: reg_neuron <= S_AXI_WDATA;
                    4'd3: reg_waddr <= S_AXI_WDATA;
                    4'd4: reg_wval <= S_AXI_WDATA;
                    4'd5: reg_bval <= S_AXI_WDATA;
                    4'd6: o_wen <= S_AXI_WDATA[0];
                    4'd7: o_bias_wen <= S_AXI_WDATA[0];
                endcase
            end
            if (S_AXI_BVALID && S_AXI_BREADY) begin
                S_AXI_BVALID <= 0;
            end
        end
    end
    always @(posedge S_AXI_ACLK or negedge S_AXI_ARESETN) begin
        if (!S_AXI_ARESETN) begin
            S_AXI_ARREADY <= 0;
            S_AXI_RVALID <= 0;
            S_AXI_RDATA <= 0;
            S_AXI_RRESP <= 0;
            reg_nn_out <= 0;
            reg_done <= 0;
            intr <= 0;
        end else begin
            if (i_done) begin
                reg_nn_out <= {28'd0, i_class};
                reg_done <= 1;
                intr <= 1;
            end
            if (o_start) begin
                reg_done <= 0;
                intr <= 0;
            end
            if (!S_AXI_ARREADY && S_AXI_ARVALID) begin
                S_AXI_ARREADY <= 1;
            end else if (S_AXI_ARREADY) begin
                S_AXI_ARREADY <= 0;
                S_AXI_RVALID <= 1;
                case (S_AXI_ARADDR[5:2])
                    4'd0: S_AXI_RDATA <= reg_ctrl;
                    4'd1: S_AXI_RDATA <= reg_layer;
                    4'd2: S_AXI_RDATA <= reg_neuron;
                    4'd3: S_AXI_RDATA <= reg_waddr;
                    4'd4: S_AXI_RDATA <= reg_wval;
                    4'd5: S_AXI_RDATA <= reg_bval;
                    4'd8: S_AXI_RDATA <= reg_nn_out;
                    4'd9: S_AXI_RDATA <= {30'd0, intr, reg_done};
                    4'd10: S_AXI_RDATA <= {16'd0, i_ahi_count};
                    4'd11: S_AXI_RDATA <= {30'd0, i_ahi_sev};
                    default: S_AXI_RDATA <= 0;
                endcase
            end
            if (S_AXI_RVALID && S_AXI_RREADY) begin
                S_AXI_RVALID <= 0;
            end
        end
    end
end
