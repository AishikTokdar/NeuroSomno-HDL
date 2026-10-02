// Experimental event-rate telemetry, not a validated clinical measurement.
// Each valid classification represents exactly SECONDS_PER_SAMPLE new seconds
// of observation (the window stride, NOT its 11-second width). No missing epochs
// may be omitted. Severity uses events/hour of observed signal, not lifetime count.
module ahi_tracker #(parameter SECONDS_PER_SAMPLE=1) (
    input wire clk, input wire rst, input wire i_valid,
    input wire [3:0] i_class, input wire clr_counter,
    output reg [15:0] o_ahi_count, output reg [1:0] o_severity,
    output reg o_alarm_intr
);
    reg [31:0] consecutive_apnea_sec, observation_sec;
    reg in_apnea_event;
    reg [63:0] duration_next, elapsed_next, events_next;
    always @(posedge clk or posedge rst) begin
        if(rst) begin
            consecutive_apnea_sec<=0; observation_sec<=0; in_apnea_event<=0;
            o_ahi_count<=0; o_severity<=0; o_alarm_intr<=0;
        end else if(clr_counter) begin
            consecutive_apnea_sec<=0; observation_sec<=0; in_apnea_event<=0;
            o_ahi_count<=0; o_severity<=0; o_alarm_intr<=0;
        end else if(i_valid) begin
            elapsed_next={32'd0,observation_sec}+SECONDS_PER_SAMPLE;
            if(elapsed_next>32'hffffffff) elapsed_next=32'hffffffff;
            observation_sec<=elapsed_next[31:0];
            events_next={48'd0,o_ahi_count};
            if(i_class==1) begin
                duration_next={32'd0,consecutive_apnea_sec}+SECONDS_PER_SAMPLE;
                if(duration_next>32'hffffffff) duration_next=32'hffffffff;
                consecutive_apnea_sec<=duration_next[31:0];
                if(duration_next>=10 && !in_apnea_event) begin
                    in_apnea_event<=1;
                    if(o_ahi_count!=16'hffff) events_next=events_next+1;
                end
                o_alarm_intr<=duration_next>30;
            end else begin
                consecutive_apnea_sec<=0; in_apnea_event<=0; o_alarm_intr<=0;
            end
            o_ahi_count<=events_next[15:0];
            if(events_next*3600 < elapsed_next*5) o_severity<=0;
            else if(events_next*3600 < elapsed_next*15) o_severity<=1;
            else if(events_next*3600 < elapsed_next*30) o_severity<=2;
            else o_severity<=3;
        end
    end
endmodule
