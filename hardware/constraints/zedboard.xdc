# Incomplete external-pin example only; not a board-level implementation.
# AXI/stream ports belong inside a PS/DMA block design, with board-specific clocks/resets.
create_clock -period 10.000 -name clk [get_ports clk]
set_property PACKAGE_PIN Y9 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]
set_property PACKAGE_PIN Y11 [get_ports intr]
set_property IOSTANDARD LVCMOS33 [get_ports intr]
