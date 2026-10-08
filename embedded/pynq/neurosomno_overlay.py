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
    """Wrapper class interfacing PYNQ MMIO and DMA with the hardware accelerator."""
    def __init__(self, bitstream_path="neurosomno.bit", base_addr=0x43C00000):
        self.base_addr = base_addr
        self.is_hardware_connected = False
        
        try:
            from pynq import Overlay, MMIO
            self.ol = Overlay(bitstream_path)
            self.mmio = MMIO(base_addr, 0x1000)
            self.is_hardware_connected = True
            print(f"[INFO] Successfully loaded PYNQ overlay: {bitstream_path}")
        except (ImportError, Exception) as e:
            print(f"[NOTE] Running in simulated software mode ({e}). Real board not required.")
            self.sim_reg = {REG_CTRL: 0, REG_STATUS: 1, REG_NNOUT: 0, REG_AHI_COUNT: 0, REG_AHI_SEV: 0}

    def write_reg(self, offset, value):
        """Writes a 32-bit word to an AXI-Lite register."""
        if self.is_hardware_connected:
            self.mmio.write(offset, int(value))
        else:
            self.sim_reg[offset] = int(value)

    def read_reg(self, offset):
        """Reads a 32-bit word from an AXI-Lite register."""
        if self.is_hardware_connected:
            return self.mmio.read(offset)
        return self.sim_reg.get(offset, 0)

    def soft_reset(self):
        """Pulses soft reset signal to reset pipeline accumulators."""
        self.write_reg(REG_CTRL, 1)
        time.sleep(0.001)
        self.write_reg(REG_CTRL, 0)

    def predict_sample(self, eeg_sample_784):
        """Sends a 784-element EEG vector into the accelerator and returns predicted class."""
        assert len(eeg_sample_784) == 784, "Input sample must contain exactly 784 points."
        
        # Trigger start
        self.write_reg(REG_CTRL, 2)
        
        # Poll completion flag
        timeout = 1000
        while timeout > 0:
            status = self.read_reg(REG_STATUS)
            if status & 0x01:
                break
            timeout -= 1
            
        pred_class = self.read_reg(REG_NNOUT) & 0x0F
        return pred_class

    def get_clinical_telemetry(self):
        """Reads AHI accumulated episode count and severity grade."""
        ahi_count = self.read_reg(REG_AHI_COUNT) & 0xFFFF
        sev_code = self.read_reg(REG_AHI_SEV) & 0x03
        return {
            "ahi_episodes": ahi_count,
            "severity_code": sev_code,
            "severity_grade": SEVERITY_NAMES[sev_code]
        }
