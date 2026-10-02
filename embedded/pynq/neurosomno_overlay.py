"""
NeuroSomno-HDL: PYNQ Python Driver & Overlay Wrapper
Provides high-level Python API for streaming EEG inferences and reading
telemetry from the NeuroSomno-HDL hardware accelerator on Zynq-7000 (ZedBoard / PYNQ-Z2).
"""

import time
import numpy as np

# Register Address Offsets matching axi_lite_wrapper.v
REG_CTRL      = 0x00  # [0]: Soft Reset, [1]: Start Inference
REG_LAYER     = 0x04  # [3:0]: Layer index
REG_NEURON    = 0x08  # [5:0]: Neuron index
REG_WADDR     = 0x0C  # [11:0]: Weight address offset
REG_WVAL      = 0x10  # [15:0]: 16-bit Q3.13 weight value
REG_BVAL      = 0x14  # [15:0]: 16-bit Q3.13 bias value
REG_WEN       = 0x18  # [0]: Weight write strobe
REG_BWEN      = 0x1C  # [0]: Bias write strobe
REG_NNOUT     = 0x20  # [3:0]: Argmax classification output (0: Normal, 1: Apnea)
REG_STATUS    = 0x24  # [0]: Done flag, [1]: Interrupt pending
REG_AHI_COUNT = 0x28  # [15:0]: Accumulated apnea episodes
REG_AHI_SEV   = 0x2C  # [1:0]: Clinical severity (0: Normal, 1: Mild, 2: Moderate, 3: Severe)

SEVERITY_NAMES = ["Normal", "Mild", "Moderate", "Severe"]

class NeuroSomnoOverlay:
    """Explicit hardware or integer-emulator inference; samples are signed Q3.13.

    Hardware overlays must expose a 16-bit MM2S AXI DMA named dma_name, connected
    to the accelerator input. Each transfer is exactly 784 words with final TLAST.
    Inference calls are serial. Telemetry requires contiguous one-second epochs;
    arbitrary offline batches must not be interpreted as clinical event rates.
    """
    def __init__(self, bitstream_path="neurosomno.bit", base_addr=0x43C00000,
                 *, mode="hardware", dma_name="axi_dma_0", mif_dir=None,
                 timeout_s=1.0, mmio=None, dma=None, allocator=None):
        if mode not in ("hardware", "emulator") or timeout_s <= 0:
            raise ValueError("Specify hardware/emulator mode and a positive timeout")
        self.timeout_s = timeout_s
        self.is_hardware_connected = mode == "hardware"
        self.base_addr = base_addr
        if mode == "emulator":
            import sys
            from pathlib import Path
            root = Path(__file__).resolve().parents[2]
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from python_pipeline.bit_true_emulator import BitTrueNetwork
            self._net = BitTrueNetwork(str(mif_dir or root / "hardware/mif"))
            self.sim_reg = {REG_CTRL: 0, REG_STATUS: 0, REG_NNOUT: 0}
            return
        if mmio is None:
            from pynq import Overlay, MMIO, allocate
            self.ol = Overlay(bitstream_path)
            mmio = MMIO(base_addr, 0x1000)
            dma = getattr(self.ol, dma_name)
            allocator = allocate
        if dma is None or allocator is None:
            raise ValueError("Hardware mode requires MMIO, DMA and buffer allocator")
        self.mmio, self.dma, self._allocate = mmio, dma, allocator
        self._dma_faulted = False

    def write_reg(self, offset, value):
        if self.is_hardware_connected:
            self.mmio.write(offset, int(value))
        else:
            self.sim_reg[offset] = int(value)
            if offset == REG_CTRL:
                self.sim_reg[REG_STATUS] = 0
                if value & 1:
                    self.sim_reg[REG_NNOUT] = 0

    def read_reg(self, offset):
        if self.is_hardware_connected:
            return self.mmio.read(offset)
        if offset in (REG_AHI_COUNT, REG_AHI_SEV):
            raise NotImplementedError("Offline emulator has no observation-time telemetry")
        return self.sim_reg.get(offset, 0)

    def soft_reset(self):
        self.write_reg(REG_CTRL, 1)
        self.write_reg(REG_CTRL, 0)

    def _wait(self, predicate, deadline, message):
        while not predicate():
            if time.monotonic() >= deadline:
                raise TimeoutError(message)
            time.sleep(0.0001)

    def _dma_idle(self):
        if self.dma.sendchannel.error:
            raise RuntimeError("DMA reported a hardware transfer error")
        return self.dma.sendchannel.idle

    def predict_sample(self, eeg_sample_784):
        if self.is_hardware_connected and self._dma_faulted:
            raise RuntimeError("DMA was aborted; reinitialize the hardware overlay before retrying")
        values = np.asarray(eeg_sample_784)
        if values.shape != (784,):
            raise ValueError("Input must be a one-dimensional 784-word Q3.13 vector")
        if values.dtype.kind in "US":
            if any(len(x) != 16 or set(x)-{'0', '1'} for x in values.tolist()):
                raise ValueError("Expected 16-bit binary strings")
            words = np.array([int(x, 2) for x in values], dtype=np.int32)
            values = np.where(words >= 32768, words - 65536, words)
        if values.dtype.kind not in "iu" or np.any(values < -32768) or np.any(values > 32767):
            raise ValueError("Expected signed 16-bit Q3.13 integers, not floating-point EEG")
        values = values.astype(np.int16)
        self.write_reg(REG_CTRL, 2)
        if not self.is_hardware_connected:
            pred, _ = self._net.infer_sample(values)
            self.sim_reg[REG_NNOUT] = pred
            self.sim_reg[REG_STATUS] = 3
            return pred
        deadline = time.monotonic() + self.timeout_s
        buffer = None
        try:
            self._wait(lambda: not (self.read_reg(REG_STATUS) & 1), deadline,
                       "Accelerator did not clear completion on start")
            buffer = self._allocate(shape=(784,), dtype=np.int16)
            buffer[:] = values
            buffer.flush()
            self.dma.sendchannel.transfer(buffer)
            self._wait(self._dma_idle, deadline, "DMA transfer timed out")
            self.dma.sendchannel.wait()  # Complete PYNQ buffer/transfer bookkeeping after idle.
            self._wait(lambda: self.read_reg(REG_STATUS) & 1, deadline,
                       "Accelerator inference timed out")
            return self.read_reg(REG_NNOUT) & 1
        except BaseException:
            # A buffer must not be freed while the DMA still owns it.
            self._dma_faulted = True
            try:
                self.dma.sendchannel.stop()
            except BaseException:
                # Keep ownership until the platform can reset a broken DMA.
                self._inflight_buffer = buffer
                buffer = None
                raise
            finally:
                self.soft_reset()
            raise
        finally:
            if buffer is not None:
                buffer.freebuffer()

    infer_sample = predict_sample

    def get_clinical_telemetry(self):
        count = self.read_reg(REG_AHI_COUNT) & 0xffff
        sev = self.read_reg(REG_AHI_SEV) & 3
        return {"ahi_episodes": count, "severity_code": sev,
                "severity_grade": SEVERITY_NAMES[sev],
                "time_contract": "one contiguous one-second epoch per inference"}
