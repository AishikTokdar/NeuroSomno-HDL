module layer4 (
    input clk,
    input rst,
    input i_valid,
    input [15:0] i_data,
    output reg o_valid,
    output reg [15:0] o_data,
    input wen,
    input [11:0] waddr,
    input [15:0] wdata,
    input [3:0] layer_sel,
    input [5:0] neuron_sel,
    input bias_wen,
    input [15:0] bias_wdata
);
    wire [15:0] n_out [0:9];
    wire n_valid [0:9];
    genvar i;
    generate
        for (i = 0; i < 10; i = i + 1) begin: g_neurons
            neuron #(
                .layerNo(4),
                .neuronNo(i),
                .numWeight(10),
                .actType("sigmoid")
            ) n_inst (
                .clk(clk),
                .rst(rst),
                .i_valid(i_valid),
                .i_data(i_data),
                .o_valid(n_valid[i]),
                .o_data(n_out[i]),
                .wen(wen && (layer_sel == 4'd4) && (neuron_sel == i)),
                .waddr(waddr),
                .wdata(wdata),
                .bias_wen(bias_wen && (layer_sel == 4'd4) && (neuron_sel == i)),
                .bias_wdata(bias_wdata)
            );
        end
    endgenerate
    reg [15:0] outputs [0:9];
    reg [3:0] shift_cnt;
    reg state;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            shift_cnt <= 0;
            state <= 0;
            o_valid <= 0;
            o_data <= 0;
        end else begin
            o_valid <= 0;
            if (state == 0) begin
                if (n_valid[0]) begin
                    integer j;
                    for (j = 0; j < 10; j = j + 1) begin
                        outputs[j] <= n_out[j];
                    end
                    shift_cnt <= 0;
                    state <= 1;
                end
            end else if (state == 1) begin
                o_data <= outputs[shift_cnt];
                o_valid <= 1;
                shift_cnt <= shift_cnt + 1;
                if (shift_cnt == 9) begin
                    state <= 0;
                end
            end
        end
    end
endmodule
