module sig_rom (
    input clk,
    input [15:0] i_data,
    output reg [15:0] o_data
);
    reg [15:0] rom [0:1023];
    initial begin
        $readmemb("sig_rom.mem", rom);
    end
    wire [9:0] index = i_data[15:6] + 10'd512;
    always @(posedge clk) begin
        o_data <= rom[index];
    end
end
