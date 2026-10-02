#include "neurosomno_hw.h"

static volatile uint32_t *accel_base = (volatile uint32_t *)NEUROSOMNO_BASE_ADDR;

void NeuroSomno_Init(uintptr_t base_addr) {
    if (base_addr != 0) {
        accel_base = (volatile uint32_t *)base_addr;
    }
    NeuroSomno_SoftReset();
}

void NeuroSomno_SoftReset(void) {
    accel_base[REG_CTRL_OFFSET / 4] = CTRL_SOFT_RST_MASK;
    for (volatile int i = 0; i < 100; i++); // Brief delay
    accel_base[REG_CTRL_OFFSET / 4] = 0;
}

void NeuroSomno_StartInference(void) {
    accel_base[REG_CTRL_OFFSET / 4] = CTRL_START_MASK;
}

int NeuroSomno_IsDone(void) {
    return (accel_base[REG_STATUS_OFFSET / 4] & STATUS_DONE_MASK) ? 1 : 0;
}

uint32_t NeuroSomno_GetPredictedClass(void) {
    return accel_base[REG_NNOUT_OFFSET / 4] & 0x0F;
}

uint16_t NeuroSomno_GetAHICount(void) {
    return (uint16_t)(accel_base[REG_AHI_COUNT_OFFSET / 4] & 0xFFFF);
}

AHI_Severity_t NeuroSomno_GetSeverity(void) {
    return (AHI_Severity_t)(accel_base[REG_AHI_SEV_OFFSET / 4] & 0x03);
}

int NeuroSomno_Predict(const int16_t *samples, size_t count, uint32_t *prediction,
                      uint64_t timeout_us, NeuroSomno_StreamFn send,
                      NeuroSomno_ClockFn clock_us, void *context) {
    if (!samples || count != 784 || !prediction || !timeout_us || !send || !clock_us)
        return -1;
    uint64_t start_us = clock_us(context);
    NeuroSomno_StartInference();
    while (NeuroSomno_IsDone()) {
        if (clock_us(context) - start_us >= timeout_us) {
            NeuroSomno_SoftReset();
            return -2;
        }
    }
    if (send(samples, count, context) != 0) {
        NeuroSomno_SoftReset();
        return -3;
    }
    while (!NeuroSomno_IsDone()) {
        if (clock_us(context) - start_us >= timeout_us) {
            NeuroSomno_SoftReset();
            return -2;
        }
    }
    if (clock_us(context) - start_us >= timeout_us) {
        NeuroSomno_SoftReset();
        return -2;
    }
    *prediction = NeuroSomno_GetPredictedClass();
    return 0;
}
