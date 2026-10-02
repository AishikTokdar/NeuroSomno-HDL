module axi_lite_wrapper (
    input S_AXI_ACLK,
    input S_AXI_ARESETN,
    input [31:0] S_AXI_AWADDR,
    input S_AXI_AWVALID,
    output S_AXI_AWREADY,
    input [31:0] S_AXI_WDATA,
    input [3:0] S_AXI_WSTRB,
    input S_AXI_WVALID,
    output S_AXI_WREADY,
    output reg [1:0] S_AXI_BRESP,
    output reg S_AXI_BVALID,
    input S_AXI_BREADY,
    input [31:0] S_AXI_ARADDR,
    input S_AXI_ARVALID,
    output S_AXI_ARREADY,
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
    reg [31:0] reg_ctrl, reg_layer, reg_neuron, reg_waddr, reg_wval, reg_bval;
    reg [31:0] reg_nn_out;
    reg reg_done;
    reg aw_pending, w_pending;
    reg [31:0] awaddr, wvalue;
    reg [3:0] wstrobe;
    wire [31:0] write_mask={{8{wstrobe[3]}},{8{wstrobe[2]}},{8{wstrobe[1]}},{8{wstrobe[0]}}};
    function [31:0] merge_bytes;
        input [31:0] previous, value;
        begin merge_bytes=(previous & ~write_mask) | (value & write_mask); end
    endfunction
    assign S_AXI_AWREADY = S_AXI_ARESETN && !aw_pending && !S_AXI_BVALID;
    assign S_AXI_WREADY = S_AXI_ARESETN && !w_pending && !S_AXI_BVALID;
    assign S_AXI_ARREADY = S_AXI_ARESETN && !S_AXI_RVALID;
    assign o_layer_sel = reg_layer[3:0];
    assign o_neuron_sel = reg_neuron[5:0];
    assign o_waddr = reg_waddr[11:0];
    assign o_wdata = reg_wval[15:0];
    assign o_bias_wdata = reg_bval[15:0];
    always @(posedge S_AXI_ACLK or negedge S_AXI_ARESETN) begin
        if (!S_AXI_ARESETN) begin
            aw_pending <= 0; w_pending <= 0; awaddr <= 0; wvalue <= 0; wstrobe<=0;
            S_AXI_BVALID <= 0; S_AXI_BRESP <= 0;
            reg_ctrl <= 0; reg_layer <= 0; reg_neuron <= 0;
            reg_waddr <= 0; reg_wval <= 0; reg_bval <= 0;
            o_reset <= 0; o_start <= 0; o_wen <= 0; o_bias_wen <= 0;
        end else begin
            o_start <= 0; o_wen <= 0; o_bias_wen <= 0;
            if (S_AXI_AWVALID && S_AXI_AWREADY) begin
                aw_pending <= 1; awaddr <= S_AXI_AWADDR;
            end
            if (S_AXI_WVALID && S_AXI_WREADY) begin
                w_pending <= 1; wvalue <= S_AXI_WDATA; wstrobe<=S_AXI_WSTRB;
            end
            if (S_AXI_BVALID && S_AXI_BREADY) S_AXI_BVALID <= 0;
            if (aw_pending && w_pending && !S_AXI_BVALID) begin
                aw_pending <= 0; w_pending <= 0;
                S_AXI_BVALID <= 1; S_AXI_BRESP <= 0;
                case (awaddr[5:0])
                    32'h00: begin
                        reg_ctrl <= merge_bytes(reg_ctrl,wvalue) & 32'h1;
                        if(wstrobe[0]) o_reset <= wvalue[0];
                        o_start <= wstrobe[0] && wvalue[1] && !wvalue[0];
                    end
                    32'h04: reg_layer <= merge_bytes(reg_layer,wvalue);
                    32'h08: reg_neuron <= merge_bytes(reg_neuron,wvalue);
                    32'h0c: reg_waddr <= merge_bytes(reg_waddr,wvalue);
                    32'h10: reg_wval <= merge_bytes(reg_wval,wvalue);
                    32'h14: reg_bval <= merge_bytes(reg_bval,wvalue);
                    32'h18: o_wen <= wstrobe[0] && wvalue[0];
                    32'h1c: o_bias_wen <= wstrobe[0] && wvalue[0];
                    default: S_AXI_BRESP <= 2'b10;
                endcase
            end
        end
    end
    always @(posedge S_AXI_ACLK or negedge S_AXI_ARESETN) begin
        if (!S_AXI_ARESETN) begin
            S_AXI_RVALID <= 0; S_AXI_RDATA <= 0; S_AXI_RRESP <= 0;
            reg_nn_out <= 0; reg_done <= 0; intr <= 0;
        end else begin
            if (i_done) begin
                reg_nn_out <= {28'd0, i_class}; reg_done <= 1; intr <= 1;
            end
            if (o_start || o_reset) begin
                reg_done <= 0; intr <= 0;
                if (o_reset) reg_nn_out <= 0;
            end
            if (S_AXI_RVALID && S_AXI_RREADY) S_AXI_RVALID <= 0;
            if (S_AXI_ARVALID && S_AXI_ARREADY) begin
                S_AXI_RVALID <= 1; S_AXI_RRESP <= 0;
                case (S_AXI_ARADDR[5:0])
                    32'h00: S_AXI_RDATA <= reg_ctrl;
                    32'h04: S_AXI_RDATA <= reg_layer;
                    32'h08: S_AXI_RDATA <= reg_neuron;
                    32'h0c: S_AXI_RDATA <= reg_waddr;
                    32'h10: S_AXI_RDATA <= reg_wval;
                    32'h14: S_AXI_RDATA <= reg_bval;
                    32'h20: S_AXI_RDATA <= reg_nn_out;
                    32'h24: S_AXI_RDATA <= {30'd0,intr,reg_done};
                    32'h28: S_AXI_RDATA <= {16'd0,i_ahi_count};
                    32'h2c: S_AXI_RDATA <= {30'd0,i_ahi_sev};
                    default: begin S_AXI_RDATA <= 0; S_AXI_RRESP <= 2'b10; end
                endcase
            end
        end
    end
endmodule
