"""Software-only project audit. Does not alter trained weights or production code.

Run: python tests/audit_project.py --iverilog PATH --vvp PATH
Behavioral regressions cover the repaired project and reject reintroduced defects.
Temporary simulation/training files are removed automatically. Evidence is saved
to results/verification/evidence.json; missing tools are recorded as skips, never passes.
"""
import argparse
import ast
import contextlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_pipeline"))
sys.path.insert(0, str(ROOT / "embedded/pynq"))
EVIDENCE = {}
IVERILOG = None
VVP = None


def simulate(name, source, modules, timeout=20, overrides=None):
    if not IVERILOG or not VVP:
        raise unittest.SkipTest("Icarus Verilog / vvp unavailable")
    with tempfile.TemporaryDirectory(prefix="neurosomno-audit-") as tmp:
        tmp = Path(tmp)
        bench = tmp / (name + ".v")
        bench.write_text(source, encoding="utf-8")
        binary = tmp / "simulation.vvp"
        sources = []
        for module in modules:
            if overrides and module in overrides:
                path = tmp / module
                path.write_text(overrides[module], encoding="utf-8")
            else:
                path = ROOT / "hardware/rtl" / module
            sources.append(str(path))
        compile_result = subprocess.run(
            [IVERILOG, "-g2012", "-Wall", "-s", name, "-o", str(binary),
             *sources, str(bench)],
            capture_output=True, text=True, timeout=30,
        )
        EVIDENCE[name + "_compile"] = compile_result.stdout + compile_result.stderr
        if compile_result.returncode:
            raise AssertionError(EVIDENCE[name + "_compile"])
        try:
            result = subprocess.run([VVP, str(binary)], cwd=ROOT / "hardware/mif",
                                    capture_output=True, text=True, timeout=timeout)
            EVIDENCE[name] = result.stdout + result.stderr
            if result.returncode:
                raise AssertionError(EVIDENCE[name])
            return EVIDENCE[name]
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or b""
            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            EVIDENCE[name] = "TIMEOUT\n" + output
            raise AssertionError(f"{name}: simulation exceeded {timeout}s; see evidence.json")


class ProjectAudit(unittest.TestCase):
    def memory_fixture(self, destination, omitted=None):
        source = ROOT / 'hardware/mif'
        for path in source.iterdir():
            if path.is_file() and path.name != omitted:
                shutil.copy2(path, Path(destination)/path.name)

    def test_memory_rejects_nonbinary_words(self):
        from validate_memory import validate_assets
        with tempfile.TemporaryDirectory() as tmp:
            self.memory_fixture(tmp)
            path = Path(tmp)/'b_1_0.mif'
            path.write_text('000000000000000X\n',encoding='ascii')
            report = validate_assets(tmp)
            self.assertFalse(report['valid'])
            self.assertTrue(any('16-bit binary' in error for error in report['errors']))

    def test_memory_requires_every_active_file(self):
        from validate_memory import validate_assets
        with tempfile.TemporaryDirectory() as tmp:
            self.memory_fixture(tmp,omitted='w_4_1.mif')
            report = validate_assets(tmp)
            self.assertFalse(report['valid'])
            self.assertIn('Missing active parameter file: w_4_1.mif',report['errors'])

    def test_memory_checksums_detect_valid_bit_changes(self):
        from validate_memory import validate_assets
        with tempfile.TemporaryDirectory() as tmp:
            self.memory_fixture(tmp)
            path = Path(tmp)/'w_1_0.mif'
            data = path.read_text(encoding='ascii')
            path.write_text(('1' if data[0]=='0' else '0')+data[1:],encoding='ascii')
            report = validate_assets(tmp)
            self.assertFalse(report['valid'])
            self.assertTrue(any('w_1_0.mif: checksum' in error for error in report['errors']))

    def test_source_syntax(self):
        for path in [*ROOT.glob("python_pipeline/*.py"), *ROOT.glob("embedded/**/*.py")]:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        notebook = json.loads((ROOT / "embedded/pynq/demo_inference.ipynb").read_text())
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                ast.parse("".join(cell["source"]))

    def test_mif_shapes_and_format(self):
        from bit_true_emulator import load_mif_array
        directory = ROOT / "hardware/mif"
        for layer, neurons, inputs in [(1, 30, 784), (2, 30, 30), (3, 10, 30), (4, 2, 10)]:
            for n in range(neurons):
                for prefix, expected in [("w", inputs), ("b", 1)]:
                    path = directory / f"{prefix}_{layer}_{n}.mif"
                    words = path.read_text().split()
                    self.assertEqual(len(words), expected, str(path))
                    self.assertTrue(all(len(w) == 16 and set(w) <= {"0", "1"} for w in words))
        self.assertEqual(len(load_mif_array(directory / "sig_rom.mem")), 1024)
        self.assertEqual(len(load_mif_array(directory / "test_data.txt")), 30 * 784)
        self.assertEqual(len((directory / "test_labels.txt").read_text().split()), 30)

    def test_documented_fixture_accuracy(self):
        import numpy as np
        from bit_true_emulator import BitTrueNetwork, load_mif_array
        directory = ROOT / "hardware/mif"
        network = BitTrueNetwork(str(directory))
        samples = load_mif_array(directory / "test_data.txt").reshape(-1, 784)
        labels = [int(x, 2) for x in (directory / "test_labels.txt").read_text().split()]
        predictions = [network.infer_sample(x)[0] for x in samples]
        count = int(np.sum(np.array(predictions) == labels))
        EVIDENCE["emulator_fixture"] = {"correct": count, "total": len(labels), "predictions": predictions, "labels": labels}
        self.assertGreaterEqual(count, 26, "Documented 86.67%-90% requires at least 26/30")

    def test_emulator_rejects_short_input(self):
        from bit_true_emulator import BitTrueNetwork
        network = BitTrueNetwork(str(ROOT / "hardware/mif"))
        with self.assertRaises(ValueError):
            network.infer_sample([0])

    def test_export_handles_small_test_split(self):
        import numpy as np
        from export_weights import export_test_vectors
        with tempfile.TemporaryDirectory(prefix="neurosomno-small-export-") as tmp:
            tmp = Path(tmp)
            np.savez(tmp / "data.npz", X_test=np.zeros((2, 2816), dtype=np.float32),
                     Y_test=np.array([0, 1], dtype=np.int64))
            with contextlib.redirect_stdout(io.StringIO()):
                export_test_vectors(str(tmp / "data.npz"), str(tmp / "mif"))
            self.assertEqual(len((tmp / "mif/test_labels.txt").read_text().split()), 2)

    def test_original_top_bench_completes(self):
        source = (ROOT / "hardware/tb/tb_top_sim.v").read_text()
        output = simulate("tb_top_sim", "`timescale 1ns/1ps\n" + source,
                          [p.name for p in (ROOT / "hardware/rtl").glob("*.v")])
        self.assertIn("Overall Accuracy", output)

    def test_stalled_top_has_known_layer_outputs(self):
        source = (ROOT / "hardware/tb/tb_top_sim.v").read_text()
        source = source.replace("module tb_top_sim;", "module audit_top;")
        source = source.replace("    integer trace_node;", "    always @(negedge clk) if(uut.l1.n_valid[0] && (^uut.l1.n_out[0])===1'bx) $fatal(1,\"Unknown L1\");\n    integer trace_node;")
        output = simulate("audit_top", source, [p.name for p in (ROOT / "hardware/rtl").glob("*.v")])
        self.assertIn("Overall Accuracy", output)
        self.assertEqual(sum("Pred =" in line for line in output.splitlines()), 30)

    def test_neuron_known_dot_product(self):
        source = '''`timescale 1ns/1ps
module audit_neuron;
reg clk=0, rst=1, valid=0, wen=0, bwen=0;
reg signed [15:0] data=0, wd=0; reg [11:0] wa=0;
wire ov; wire [15:0] od;
always #5 clk=~clk;
neuron #(.numWeight(3)) dut(clk,rst,valid,data,ov,od,wen,wa,wd,bwen,16'sd2048);
always @(negedge clk) if (ov) $display("RESULT=%h", od);
initial begin
repeat(2) @(negedge clk); rst=0; wen=1; wd=8192; wa=0;
@(negedge clk); wa=1; wd=-16384;
@(negedge clk); wa=2; wd=4096;
@(negedge clk); wen=0; bwen=1;
@(negedge clk); bwen=0;
@(negedge clk); valid=1; data=8192;
@(negedge clk); data=4096;
@(negedge clk); data=16384;
@(negedge clk); valid=0;
repeat(10) @(negedge clk); $finish;
end
endmodule'''
        output = simulate("audit_neuron", source, ["neuron.v", "weight_memory.v", "relu.v", "sig_rom.v"])
        self.assertIn("RESULT=2800", output, "1*1 + .5*(-2) + 2*.5 + .25 must equal 1.25 (10240)")

    def test_conv_includes_last_window(self):
        source = '''`timescale 1ns/1ps
module audit_conv;
reg clk=0,rst=1,valid=0; reg signed [15:0] data=0;
wire ov; wire signed [15:0] od; integer count=0;
always #5 clk=~clk;
conv1d_pe #(.KERNEL_SIZE(2)) dut(clk,rst,valid,data,{16'd8192,16'd8192},16'd0,ov,od);
always @(negedge clk) if(ov) begin count=count+1; $display("CONV=%0d",od); end
initial begin
repeat(2) @(negedge clk); rst=0;
@(negedge clk); valid=1; data=100;
@(negedge clk); data=200;
@(negedge clk); data=300;
@(negedge clk); valid=0;
repeat(6) @(negedge clk); $display("COUNT=%0d",count); $finish;
end
endmodule'''
        output = simulate("audit_conv", source, ["conv1d_pe.v"])
        self.assertIn("COUNT=2", output)
        self.assertIn("CONV=500", output)

    def test_maxpool_stride_one(self):
        source = '''`timescale 1ns/1ps
module audit_pool;
reg clk=0,rst=1,valid=0; reg signed [15:0] data=0;
wire ov; wire signed [15:0] od; integer count=0;
always #5 clk=~clk;
maxpool1d #(.POOL_SIZE(2),.STRIDE(1)) dut(clk,rst,valid,data,ov,od);
always @(negedge clk) if(ov) begin count=count+1; $display("POOL=%0d",od); end
initial begin
repeat(2) @(negedge clk); rst=0;
@(negedge clk); valid=1; data=100;
@(negedge clk); data=200;
@(negedge clk); data=300;
@(negedge clk); valid=0;
repeat(4) @(negedge clk); $display("COUNT=%0d",count); $finish;
end
endmodule'''
        output = simulate("audit_pool", source, ["maxpool1d.v"])
        self.assertIn("COUNT=2", output)

    def test_notch_stability(self):
        import numpy as np
        source = (ROOT / "hardware/rtl/iir_notch_50hz.v").read_text()
        values = {key: int(value)/8192 for key, value in re.findall(r"\.(B[012]|A[12])\((-?\d+)\)", source)}
        poles = np.roots([1, values['A1'], values['A2']])
        EVIDENCE['notch_poles'] = [[float(z.real), float(z.imag)] for z in poles]
        self.assertTrue(np.all(np.abs(poles)<1))
        from scipy.signal import freqz
        _, response = freqz([values['B0'], values['B1'], values['B2']], [1,values['A1'],values['A2']], worN=[2*np.pi*50/128])
        self.assertLess(abs(response[0]), .01)

    def test_bandpass_rejects_60hz(self):
        import numpy as np
        from scipy.signal import sosfreqz
        source = (ROOT / "hardware/rtl/iir_bandpass.v").read_text()
        values = [int(value)/8192 for _,value in re.findall(r"\.(B[012]|A[12])\((-?\d+)\)", source)]
        sections=[]
        for i in range(0,len(values),5):
            b0,b1,b2,a1,a2=values[i:i+5]
            sections.append([b0,b1,b2,1,a1,a2])
            self.assertTrue(np.all(np.abs(np.roots([1,a1,a2]))<1))
        self.assertEqual(len(sections),4)
        _, response = sosfreqz(sections, worN=[2*np.pi*.1/128,2*np.pi*10/128,2*np.pi*60/128])
        EVIDENCE['bandpass_gain_.1_10_60hz']=np.abs(response).tolist()
        self.assertLess(abs(response[0]), .05)
        self.assertLess(abs(response[2]), .05)
        self.assertGreater(abs(response[1]), .9)

    def test_ahi_tenth_second_counts_event(self):
        source = '''`timescale 1ns/1ps
module audit_ahi;
reg clk=0,rst=1,valid=0; wire [15:0] count; wire [1:0] sev; wire alarm;
always #5 clk=~clk;
ahi_tracker dut(clk,rst,valid,4'd1,1'b0,count,sev,alarm);
initial begin
repeat(2) @(negedge clk); rst=0; valid=1;
repeat(10) @(negedge clk); valid=0;
$display("EVENTS_AT_10=%0d",count); $finish;
end
endmodule'''
        output = simulate("audit_ahi", source, ["ahi_tracker.v"])
        self.assertIn("EVENTS_AT_10=1", output)

    def test_axi_write_responses_survive_backpressure(self):
        source = '''`timescale 1ns/1ps
module audit_axi_write;
reg clk=0,rstn=0,av=0,wv=0,br=0; reg [31:0] wd=0;
wire ar,wr,bv; integer accepted=0,responses=0;
always #5 clk=~clk;
axi_lite_wrapper dut(.S_AXI_ACLK(clk),.S_AXI_ARESETN(rstn),
.S_AXI_WSTRB(4'hf),.S_AXI_AWADDR(32'h10),.S_AXI_AWVALID(av),.S_AXI_AWREADY(ar),
.S_AXI_WDATA(wd),.S_AXI_WVALID(wv),.S_AXI_WREADY(wr),
.S_AXI_BVALID(bv),.S_AXI_BREADY(br),
.S_AXI_ARADDR(32'd0),.S_AXI_ARVALID(1'b0),.S_AXI_RREADY(1'b0),
.i_class(4'd0),.i_done(1'b0),.i_ahi_count(16'd0),.i_ahi_sev(2'd0));
always @(posedge clk) begin
if(rstn && av && ar && wv && wr) accepted=accepted+1;
if(rstn && bv && br) responses=responses+1;
end
task write(input [31:0] data);
begin
@(negedge clk); wd=data; av=1; wv=1;
@(posedge clk); while(!(ar && wr)) @(posedge clk);
@(negedge clk); av=0; wv=0;
end endtask
initial begin
repeat(2) @(negedge clk); rstn=1;
write(111);
fork
begin write(222); end
begin repeat(8) @(negedge clk); br=1; end
join
repeat(8) @(negedge clk);
$display("ACCEPTED=%0d RESPONSES=%0d",accepted,responses); $finish;
end
initial begin #2000; $fatal(1,"AXI timeout"); end
endmodule'''
        output = simulate("audit_axi_write", source, ["axi_lite_wrapper.v"])
        self.assertIn("ACCEPTED=2 RESPONSES=2", output)

    def test_axi_read_data_held_during_backpressure(self):
        source = '''`timescale 1ns/1ps
module audit_axi_read;
reg clk=0,rstn=0,av=0; reg [31:0] addr=0;
wire ar,rv; wire [31:0] rd;
always #5 clk=~clk;
axi_lite_wrapper dut(.S_AXI_ACLK(clk),.S_AXI_ARESETN(rstn),
.S_AXI_WSTRB(4'hf),.S_AXI_AWADDR(32'd0),.S_AXI_AWVALID(1'b0),.S_AXI_WDATA(32'd0),
.S_AXI_WVALID(1'b0),.S_AXI_BREADY(1'b1),.S_AXI_ARADDR(addr),
.S_AXI_ARVALID(av),.S_AXI_ARREADY(ar),.S_AXI_RDATA(rd),
.S_AXI_RVALID(rv),.S_AXI_RREADY(1'b0),.i_class(4'd0),.i_done(1'b0),
.i_ahi_count(16'd123),.i_ahi_sev(2'd2));
task read(input [31:0] data);
begin
@(negedge clk); addr=data; av=1;
@(posedge clk); while(!ar) @(posedge clk);
@(negedge clk); av=0;
end endtask
initial begin
repeat(2) @(negedge clk); rstn=1;
read(32'h28);
repeat(2) @(negedge clk); $display("FIRST=%0d",rd);
// A second request must not overwrite an unconsumed first response.
addr=32'h2c; av=1;
repeat(8) @(negedge clk);
$display("HELD=%0d",rd); $finish;
end
endmodule'''
        output = simulate("audit_axi_read", source, ["axi_lite_wrapper.v"])
        self.assertIn("FIRST=123", output)
        self.assertIn("HELD=123", output)

    def test_pynq_fallback_uses_samples(self):
        import numpy as np
        from neurosomno_overlay import NeuroSomnoOverlay
        from bit_true_emulator import BitTrueNetwork, load_mif_array
        with contextlib.redirect_stdout(io.StringIO()):
            overlay = NeuroSomnoOverlay("missing-audit-bitstream.bit", mode="emulator")
        if overlay.is_hardware_connected:
            self.skipTest("Do not exercise a physical board")
        directory = ROOT / "hardware/mif"
        x = load_mif_array(directory / "test_data.txt").reshape(-1, 784)[1]
        expected = BitTrueNetwork(str(directory)).infer_sample(x)[0]
        actual = overlay.predict_sample(x)
        EVIDENCE["pynq_fallback"] = {"actual": actual, "emulator_expected": expected}
        self.assertEqual(actual, expected)

    def test_pynq_timeout_raises(self):
        from neurosomno_overlay import NeuroSomnoOverlay
        from unittest.mock import MagicMock
        mmio, dma = MagicMock(), MagicMock()
        mmio.read.return_value = 0
        dma.sendchannel.idle = True
        dma.sendchannel.error = False
        buffer = MagicMock()
        overlay = NeuroSomnoOverlay(mode="hardware", mmio=mmio, dma=dma,
                                   allocator=lambda **kw: buffer, timeout_s=.01)
        with self.assertRaises(TimeoutError):
            overlay.predict_sample([0] * 784)
        dma.sendchannel.transfer.assert_called_once_with(buffer)
        dma.sendchannel.stop.assert_called_once()
        buffer.freebuffer.assert_called_once()

    def test_export_preserves_trained_classifier(self):
        import torch
        from train_model import NeuroSomnoFCN
        from export_weights import export_model_weights
        model = NeuroSomnoFCN()
        # Equal FC4 outputs, but a learned class-1 output-head bias.
        with torch.no_grad():
            for param in model.parameters():
                param.zero_()
            model.fc4.bias[1] = 1
        with tempfile.TemporaryDirectory(prefix="neurosomno-export-") as tmp:
            checkpoint = Path(tmp)/"model.pt"
            torch.save(model.state_dict(), checkpoint)
            with contextlib.redirect_stdout(io.StringIO()):
                export_model_weights(str(checkpoint), str(Path(tmp)/"mif"))
            from bit_true_emulator import BitTrueNetwork
            hardware_pred = BitTrueNetwork(str(Path(tmp)/"mif")).infer_sample([0]*784)[0]
            model_pred = int(model(torch.zeros(1, 784)).argmax(1).item())
            EVIDENCE["export_classifier"] = {"trained": model_pred, "exported": hardware_pred}
            self.assertEqual(hardware_pred, model_pred, "Export silently discards out_head")

    def test_preprocessing_and_training_smoke(self):
        import numpy as np
        import torch
        from preprocess_eeg import generate_synthetic_patient, apply_filters, segment_signals, normalize_zscore
        from train_model import NeuroSomnoFCN, Hybrid1DCNN, downsample_signals, apply_smote
        torch.set_num_threads(2)
        c3,c4,y = generate_synthetic_patient(duration_sec=120)
        x, labels = segment_signals(apply_filters(c3), apply_filters(c4), y)
        self.assertEqual(x.shape, (110, 2816))
        self.assertTrue(np.isfinite(x).all())
        self.assertTrue(np.isfinite(normalize_zscore(np.ones(1408))).all())
        balanced, targets = apply_smote(x, labels)
        self.assertEqual(int(sum(targets == 0)), int(sum(targets == 1)))
        for model, inputs in [(NeuroSomnoFCN(), torch.from_numpy(downsample_signals(balanced[:4]))),
                              (Hybrid1DCNN(), torch.from_numpy(balanced[:4]).unsqueeze(1))]:
            logits = model(inputs)
            self.assertEqual(tuple(logits.shape), (4,2))
            torch.nn.functional.cross_entropy(logits, torch.from_numpy(targets[:4])).backward()
            self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_patient_splits_are_disjoint(self):
        import numpy as np
        from preprocess_eeg import run_preprocessing_pipeline
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.npz'
            run_preprocessing_pipeline(tmp, str(path))
            with np.load(path) as data:
                groups = [set(data['subjects_' + s]) for s in ('train', 'val', 'test')]
                self.assertTrue(all(groups))
                self.assertFalse(groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2])
                for split in ('train', 'val', 'test'):
                    self.assertEqual(set(data['Y_' + split]), {0, 1})

    def test_edf_missing_annotations_is_rejected(self):
        from preprocess_eeg import run_preprocessing_pipeline
        from unittest.mock import patch, MagicMock
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'patient.edf').touch()
            with patch.dict(sys.modules, {'mne': MagicMock()}):
                with self.assertRaises(FileNotFoundError):
                    run_preprocessing_pipeline(tmp, str(Path(tmp) / 'data.npz'))

    def test_hardware_driver_transfers_signed_input(self):
        import numpy as np
        from unittest.mock import MagicMock
        from neurosomno_overlay import NeuroSomnoOverlay, REG_STATUS, REG_NNOUT
        mmio, dma, buffer = MagicMock(), MagicMock(), MagicMock()
        done = [False]
        mmio.read.side_effect = lambda addr: (int(done[0]) if addr == REG_STATUS else 1)
        dma.sendchannel.transfer.side_effect = lambda buf: done.__setitem__(0, True)
        dma.sendchannel.idle = True
        dma.sendchannel.error = False
        overlay = NeuroSomnoOverlay(mmio=mmio, dma=dma, allocator=lambda **kw: buffer)
        sample = np.arange(784, dtype=np.int16) - 400
        self.assertEqual(overlay.predict_sample(sample), 1)
        self.assertTrue(np.array_equal(buffer.__setitem__.call_args.args[1], sample))
        buffer.flush.assert_called_once()
        buffer.freebuffer.assert_called_once()
        dma.sendchannel.wait.assert_called_once()
        with self.assertRaises(ValueError):
            overlay.predict_sample(sample.astype(float))

    def test_axi_independent_channels_and_byte_writes(self):
        source = '''`timescale 1ns/1ps
module audit_axi_bytes;
reg clk=0,rstn=0,av=0,wv=0,rv=0; reg[31:0] wd=0; reg[3:0] st=15;
wire ar,wr,bv,rr,rdv; wire[31:0] rd;
always #5 clk=~clk;
axi_lite_wrapper dut(.S_AXI_ACLK(clk),.S_AXI_ARESETN(rstn),
.S_AXI_AWADDR(32'h10),.S_AXI_AWVALID(av),.S_AXI_AWREADY(ar),
.S_AXI_WDATA(wd),.S_AXI_WSTRB(st),.S_AXI_WVALID(wv),.S_AXI_WREADY(wr),
.S_AXI_BREADY(1'b1),.S_AXI_BVALID(bv),.S_AXI_ARADDR(32'h10),
.S_AXI_ARVALID(rv),.S_AXI_ARREADY(rr),.S_AXI_RVALID(rdv),.S_AXI_RDATA(rd),
.S_AXI_RREADY(1'b1),.i_done(1'b0),.i_class(4'd0),.i_ahi_count(16'd0),.i_ahi_sev(2'd0));
initial begin
repeat(2) @(negedge clk); rstn=1;
// AW arrives first. Its address must remain latched until the later W beat.
@(negedge clk); av=1;
@(posedge clk); while(!ar) @(posedge clk);
@(negedge clk); av=0;
repeat(3) @(negedge clk); wd=32'h12345678; wv=1;
@(posedge clk); while(!wr) @(posedge clk);
@(negedge clk); wv=0;
@(posedge clk); while(!bv) @(posedge clk);
// Next transaction: W arrives first, and only the low byte is enabled.
@(negedge clk); wd=32'hdeadbeab; st=1; wv=1;
@(posedge clk); while(!wr) @(posedge clk);
@(negedge clk); wv=0;
repeat(3) @(negedge clk); av=1;
@(posedge clk); while(!ar) @(posedge clk);
@(negedge clk); av=0;
@(posedge clk); while(!bv) @(posedge clk);
@(negedge clk); rv=1;
@(posedge clk); while(!rr) @(posedge clk);
@(negedge clk); rv=0;
@(posedge clk); while(!rdv) @(posedge clk);
$display("READ=%h",rd); $finish;
end
initial begin #3000; $fatal(1,"AXI timeout"); end
endmodule'''
        output = simulate('audit_axi_bytes', source, ['axi_lite_wrapper.v'])
        self.assertIn('READ=123456ab', output)

    def test_filters_integer_recurrence_with_gaps(self):
        import numpy as np
        for module in ('iir_notch_50hz', 'iir_bandpass'):
            text = (ROOT / f'hardware/rtl/{module}.v').read_text()
            coefficients = [int(v) for _, v in re.findall(r'\.(B[012]|A[12])\((-?\d+)\)', text)]
            sections = [coefficients[i:i+5] for i in range(0,len(coefficients),5)]
            samples = [1000, -1500, 32767, -32768] + [0]*100
            expected = samples
            for b0,b1,b2,a1,a2 in sections:
                d1=d2=0; values=[]
                for x in expected:
                    y=max(-32768,min(32767,(x*b0+d1)>>13))
                    d1,d2=x*b1-y*a1+d2,x*b2-y*a2
                    values.append(y)
                expected=values
            name = 'audit_' + module
            writes = ''.join(f'@(negedge clk); valid=1; data={x}; @(negedge clk); valid=0;\n' for x in samples)
            source = f'''`timescale 1ns/1ps
module {name};
reg clk=0,rst=1,valid=0; reg signed[15:0] data=0;
wire ov; wire signed[15:0] od;
always #5 clk=~clk;
{module} dut(clk,rst,valid,data,ov,od);
always @(negedge clk) if(ov) $display("FILTER=%0d",od);
initial begin repeat(2) @(negedge clk); rst=0;
{writes}
repeat(10) @(negedge clk); $finish; end
endmodule'''
            output = simulate(name, source, [module + '.v', 'iir_biquad.v'])
            actual=[int(v) for v in re.findall(r'FILTER=(-?\d+)',output)]
            self.assertEqual(actual, expected, module)

    def test_malformed_frame_and_soft_reset_recover(self):
        source = (ROOT / 'hardware/tb/tb_top_sim.v').read_text().replace('module tb_top_sim;', 'module audit_reset;')
        prefix = '''        control_write(2);
        @(negedge clk); s_axis_tvalid=1; s_axis_tlast=1;
        @(posedge clk); while(!s_axis_tready) @(posedge clk);
        @(negedge clk); s_axis_tvalid=0; s_axis_tlast=0;
        repeat(4) @(negedge clk);
        if(s_axis_tready!==0) $fatal(1,"Malformed frame did not abort");
        control_write(2);
        @(negedge clk); s_axis_tvalid=1; s_axis_tdata=123;
        repeat(10) @(negedge clk);
        s_axis_tvalid=0;
        control_write(1);
        repeat(4) @(negedge clk);
        if(s_axis_tready!==0 || uut.axil.reg_done!==0) $fatal(1,"Soft reset did not clear state");
        control_write(0);
'''
        source = source.replace('        for (i = 0; i < 30;', prefix + '        for (i = 0; i < 30;', 1)
        source = source.replace('    task send_data', '''    task control_write(input [31:0] value);
        begin
            @(negedge clk); S_AXI_AWADDR=0; S_AXI_WDATA=value;
            S_AXI_AWVALID=1; S_AXI_WVALID=1;
            @(posedge clk); while(!(S_AXI_AWREADY && S_AXI_WREADY)) @(posedge clk);
            @(negedge clk); S_AXI_AWVALID=0; S_AXI_WVALID=0;
            @(posedge clk); while(!S_AXI_BVALID) @(posedge clk);
            repeat(2) @(negedge clk);
        end
    endtask
    task send_data''', 1)
        output = simulate('audit_reset', source, [p.name for p in (ROOT / 'hardware/rtl').glob('*.v')])
        self.assertEqual(sum('Pred =' in row for row in output.splitlines()),30)
        self.assertIn('Overall Accuracy: 100.',output)

    def test_event_rate_uses_observation_time(self):
        source = '''`timescale 1ns/1ps
module audit_event_rate;
reg clk=0,rst=1,valid=0; reg[3:0] kind=0;
wire[15:0] count; wire[1:0] grade; wire alarm; integer i;
always #5 clk=~clk;
ahi_tracker dut(clk,rst,valid,kind,1'b0,count,grade,alarm);
initial begin
repeat(2) @(negedge clk); rst=0; valid=1;
for(i=0;i<5;i=i+1) begin
kind=1; repeat(10) @(negedge clk);
kind=0; @(negedge clk);
end
repeat(3545) @(negedge clk);
$display("AT_HOUR count=%0d grade=%0d",count,grade);
repeat(3600) @(negedge clk);
$display("AT_TWO_HOURS count=%0d grade=%0d",count,grade);
kind=1; repeat(300) @(negedge clk);
$display("LONG_EVENT count=%0d alarm=%0d duration=%0d",count,alarm,dut.consecutive_apnea_sec);
$finish;
end
endmodule'''
        output = simulate('audit_event_rate',source,['ahi_tracker.v'])
        self.assertIn('AT_HOUR count=5 grade=1',output)
        self.assertIn('AT_TWO_HOURS count=5 grade=0',output)
        self.assertIn('LONG_EVENT count=6 alarm=1 duration=300',output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iverilog", default=shutil.which("iverilog"))
    parser.add_argument("--vvp", default=shutil.which("vvp"))
    args = parser.parse_args()
    IVERILOG, VVP = args.iverilog, args.vvp
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProjectAudit)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    EVIDENCE["environment"] = {"python": sys.version, "iverilog": IVERILOG, "vvp": VVP,
                               "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    EVIDENCE["summary"] = {"tests": result.testsRun, "failures": len(result.failures),
                           "errors": len(result.errors), "skipped": len(result.skipped),
                           "details": [(str(test), reason) for test, reason in result.failures + result.errors]}
    output = ROOT / "results/verification/evidence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(EVIDENCE, indent=2), encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
