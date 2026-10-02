// ============================================================================
// NeuroSomno-HDL: Apnea-Hypopnea Index (AHI) Clinical Tracker (ahi_tracker.v)
// Accumulates apnea events, scores hourly severity, and triggers safety alarms
// ============================================================================

`timescale 1ns / 1ps

module ahi_tracker (
    input wire clk,
    input wire rst,
    input wire i_valid,                  // Strobe on each inference sample
    input wire [3:0] i_class,             // 0 = Normal, 1 = Apnea
    input wire clr_counter,              // Software register clear strobe
    output reg [15:0] o_ahi_count,       // Total qualified apnea events
    output reg [1:0] o_severity,         // 0: Normal, 1: Mild, 2: Moderate, 3: Severe
    output reg o_alarm_intr              // Asserts if apnea episode > 30 seconds
);

    // Clinical apnea definition: continuous cessation >= 10 seconds
    reg [7:0] consecutive_apnea_sec;
    reg in_apnea_event;

    // Severity Levels (AASM Guidelines):
    // Normal:   AHI < 5
    // Mild:     5 <= AHI < 15
    // Moderate: 15 <= AHI < 30
    // Severe:   AHI >= 30
    localparam SEV_NORMAL   = 2'b00;
    localparam SEV_MILD     = 2'b01;
    localparam SEV_MODERATE = 2'b10;
    localparam SEV_SEVERE   = 2'b11;

    always @(posedge clk or posedge rst) begin
        if (rst || clr_counter) begin
            consecutive_apnea_sec <= 0;
            in_apnea_event        <= 0;
            o_ahi_count           <= 0;
            o_severity            <= SEV_NORMAL;
            o_alarm_intr          <= 0;
        end else if (i_valid) begin
            if (i_class == 4'd1) begin
                consecutive_apnea_sec <= consecutive_apnea_sec + 1;

                // Threshold 1: Qualified clinical apnea episode (>= 10 seconds)
                if (consecutive_apnea_sec >= 8'd10 && !in_apnea_event) begin
                    in_apnea_event <= 1;
                    o_ahi_count    <= o_ahi_count + 1;
                end

                // Threshold 2: Critical hypoxia hazard alarm (> 30 seconds)
                if (consecutive_apnea_sec >= 8'd30) begin
                    o_alarm_intr <= 1;
                end
            end else begin
                // Return to normal respiration
                consecutive_apnea_sec <= 0;
                in_apnea_event        <= 0;
                o_alarm_intr          <= 0;
            end

            // Update clinical severity grade
            if (o_ahi_count < 16'd5) begin
                o_severity <= SEV_NORMAL;
            end else if (o_ahi_count < 16'd15) begin
                o_severity <= SEV_MILD;
            end else if (o_ahi_count < 16'd30) begin
                o_severity <= SEV_MODERATE;
            end else begin
                o_severity <= SEV_SEVERE;
            end
        end
    end

endmodule
