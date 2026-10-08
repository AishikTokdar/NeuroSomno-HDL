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
