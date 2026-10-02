# Current architecture

The active core accepts preprocessed signed Q3.13 vectors and computes a
784–30–30–10–2 FCN. ReLU/ReLU/sigmoid/linear activations match training and export.
Class 0 is normal, class 1 apnea; ties choose normal. Neurons pipeline synchronous
weight reads with input/valid, shift each signed product by 13, accumulate, add
bias and saturate. Sigmoid indexes `((saturated_input >> 6) + 512) & 1023`.
The layer serializers stream all neuron outputs forward.

The standalone convolution/pooling/IIR modules are not connected to the FCN top.
Offline preprocessing is zero-phase; streaming filters are causal. They cannot
replace the trained model's preprocessing without separate validation/retraining.

## Register map and transactions

| Offset | Register | Meaning |
|---|---|---|
| 0x00 | CTRL | Bit 0 holds reset; bit 1 pulses START and reads zero |
| 0x04 | LAYER | Layer 1–4 |
| 0x08 | NEURON | Zero-based neuron |
| 0x0C | WADDR | Weight index |
| 0x10 | WVAL | Q3.13 weight in low 16 bits |
| 0x14 | BVAL | Q3.13 bias in low 16 bits |
| 0x18 | WEN | Bit 0 programs selected weight |
| 0x1C | BWEN | Bit 0 programs selected bias |
| 0x20 | NNOUT | Normal=0, apnea=1 |
| 0x24 | STATUS | Bit 0 DONE, bit 1 inference interrupt pending |
| 0x28 | EVENT_COUNT | Saturating episode count |
| 0x2C | RATE_GRADE | Experimental event-rate grade |

AW and W channels are independent and have one pending slot each. Responses/data
remain stable under backpressure. WSTRB supports byte writes. Decode uses the low
six address bits; unaligned/unmapped offsets return SLVERR. Configure weights
only while idle. START clears DONE; software reset clears running, pipeline,
completion, prediction and telemetry.

A frame has exactly 784 handshakes with TLAST only on the last word. READY drops
after that beat until completion and another START. Gaps are permitted. Early or
missing TLAST aborts the frame; timeout/reset/retry is required. Calls are serial.
The interrupt is completion OR the duration alarm: poll STATUS.DONE to distinguish
inference completion from an alarm.

## Observation time

Each valid classification represents one new contiguous second by default, the
window stride. Count an episode on the tenth positive epoch, once until a negative
epoch. Duration/counts saturate. Severity compares episodes × 3600 against observed
seconds × 5/15/30. An alarm asserts after 30 observed positive seconds. This is an
experimental event rate, not validated clinical AHI or measured sleep time.
Offline arbitrary batches must not be treated as clinical telemetry.

## Physical integration

This is an IP core, not a board image. Connect PS AXI-Lite and a 16-bit MM2S DMA
stream with final TLAST; configure addresses, clocks, resets and interrupts for
the selected board. The ZedBoard XDC is an incomplete pin example. No bitstream
or block design is supplied. Vendor routed timing, electrical constraints, actual
DMA/interrupt delivery and measured power remain unverified.
