`timescale 1ns/1ps
module tb_top_sim;
    reg clk;
    reg rst;
    reg [15:0] s_axis_tdata;
    reg s_axis_tvalid;
    wire s_axis_tready;
    reg s_axis_tlast;
    reg [31:0] S_AXI_AWADDR;
    reg S_AXI_AWVALID;
    wire S_AXI_AWREADY;
    reg [31:0] S_AXI_WDATA;
    reg S_AXI_WVALID;
    wire S_AXI_WREADY;
    wire [1:0] S_AXI_BRESP;
    wire S_AXI_BVALID;
    reg S_AXI_BREADY;
    reg [31:0] S_AXI_ARADDR;
    reg S_AXI_ARVALID;
    wire S_AXI_ARREADY;
    wire [31:0] S_AXI_RDATA;
    wire [1:0] S_AXI_RRESP;
    wire S_AXI_RVALID;
    reg S_AXI_RREADY;
    wire intr;
    zynet_top uut (
        .clk(clk),
        .rst(rst),
        .s_axis_tdata(s_axis_tdata),
        .s_axis_tvalid(s_axis_tvalid),
        .s_axis_tready(s_axis_tready),
        .s_axis_tlast(s_axis_tlast),
        .S_AXI_AWADDR(S_AXI_AWADDR),
        .S_AXI_AWVALID(S_AXI_AWVALID),
        .S_AXI_AWREADY(S_AXI_AWREADY),
        .S_AXI_WDATA(S_AXI_WDATA),
        .S_AXI_WSTRB(4'hf),
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
        .intr(intr)
    );
    always #5 clk = ~clk;
    reg [15:0] test_mem [0:30*784-1];
    reg [3:0] test_labels [0:29];
    integer i, j, correct_count;
    real accuracy;
    initial begin #5000000; $fatal(1,"Simulation watchdog expired"); end
    initial begin
        clk = 0;
        rst = 1;
        s_axis_tdata = 0;
        s_axis_tvalid = 0;
        s_axis_tlast = 0;
        S_AXI_AWADDR = 0;
        S_AXI_AWVALID = 0;
        S_AXI_WDATA = 0;
        S_AXI_WVALID = 0;
        S_AXI_BREADY = 1;
        S_AXI_ARADDR = 0;
        S_AXI_ARVALID = 0;
        S_AXI_RREADY = 1;
        correct_count = 0;
        $readmemb("test_data.txt", test_mem);
        $readmemb("test_labels.txt", test_labels);
        #100;
        rst = 0;
        #50;
        for (i = 0; i < 30; i = i + 1) begin
            send_data(i);
            wait_for_interrupt();
            read_and_verify(i);
            #100;
        end
        accuracy = (correct_count * 100.0) / 30.0;
        $display("Overall Accuracy: %f", accuracy);
        #100;
        $finish;
    end
    task send_data(input integer sample_idx);
        begin
            @(negedge clk);
            S_AXI_AWADDR=0; S_AXI_WDATA=2;
            S_AXI_AWVALID=1; S_AXI_WVALID=1;
            @(posedge clk);
            while(!(S_AXI_AWREADY && S_AXI_WREADY)) @(posedge clk);
            @(negedge clk); S_AXI_AWVALID=0; S_AXI_WVALID=0;
            @(posedge clk); while(!S_AXI_BVALID) @(posedge clk);
            if(S_AXI_BRESP!==0) $fatal(1,"AXI write failed");
            for(j=0;j<784;j=j+1) begin
                @(negedge clk);
                s_axis_tdata=test_mem[sample_idx*784+j];
                s_axis_tvalid=1; s_axis_tlast=(j==783);
                @(posedge clk); while(!s_axis_tready) @(posedge clk);
                // Deliberate input gaps exercise the synchronous weight pipeline.
                if(j%13==0) begin
                    @(negedge clk); s_axis_tvalid=0; s_axis_tlast=0;
                end
            end
            @(negedge clk); s_axis_tvalid=0; s_axis_tlast=0;
        end
    endtask
    task wait_for_interrupt;
        begin
            @(posedge clk); while(!intr) @(posedge clk);
        end
    endtask
    task read_and_verify(input integer sample_idx);
        reg [31:0] rd_val;
        begin
            @(negedge clk); S_AXI_ARADDR=32'h20; S_AXI_ARVALID=1;
            @(posedge clk); while(!S_AXI_ARREADY) @(posedge clk);
            @(negedge clk); S_AXI_ARVALID=0;
            @(posedge clk); while(!S_AXI_RVALID) @(posedge clk);
            if(S_AXI_RRESP!==0) $fatal(1,"AXI read failed");
            rd_val=S_AXI_RDATA;
            if((^rd_val)===1'bx) $fatal(1,"Unknown prediction");
            if(rd_val[3:0]==test_labels[sample_idx]) correct_count=correct_count+1;
            $display("Sample %0d: Pred = %0d, Act = %0d",sample_idx,rd_val[3:0],test_labels[sample_idx]);
        end
    endtask
    integer trace_node;
    always @(negedge clk) begin
        if($test$plusargs("TRACE")) begin
            if(uut.l1.n_valid[0])
                for(trace_node=0;trace_node<30;trace_node=trace_node+1)
                    $display("TRACE %0d 1 %0d %0d",i,trace_node,$signed(uut.l1.n_out[trace_node]));
            if(uut.l2.n_valid[0])
                for(trace_node=0;trace_node<30;trace_node=trace_node+1)
                    $display("TRACE %0d 2 %0d %0d",i,trace_node,$signed(uut.l2.n_out[trace_node]));
            if(uut.l3.n_valid[0])
                for(trace_node=0;trace_node<10;trace_node=trace_node+1)
                    $display("TRACE %0d 3 %0d %0d",i,trace_node,$signed(uut.l3.n_out[trace_node]));
            if(uut.l4.n_valid[0])
                for(trace_node=0;trace_node<2;trace_node=trace_node+1)
                    $display("TRACE %0d 4 %0d %0d",i,trace_node,$signed(uut.l4.n_out[trace_node]));
        end
    end
endmodule
