#ifndef NEUROSOMNO_HW_H
#define NEUROSOMNO_HW_H

#include <stdint.h>

// Base address for AXI-Lite accelerator registers in Zynq memory map
#define NEUROSOMNO_BASE_ADDR   0x43C00000

// Register Offsets
#define REG_CTRL_OFFSET        0x00
#define REG_LAYER_OFFSET       0x04
#define REG_NEURON_OFFSET      0x08
#define REG_WADDR_OFFSET       0x0C
#define REG_WVAL_OFFSET        0x10
#define REG_BVAL_OFFSET        0x14
#define REG_WEN_OFFSET         0x18
#define REG_BWEN_OFFSET        0x1C
#define REG_NNOUT_OFFSET       0x20
#define REG_STATUS_OFFSET      0x24
#define REG_AHI_COUNT_OFFSET   0x28
#define REG_AHI_SEV_OFFSET     0x2C

// Bitmasks
#define CTRL_SOFT_RST_MASK     0x01
#define CTRL_START_MASK        0x02
#define STATUS_DONE_MASK       0x01
#define STATUS_INTR_MASK       0x02

// Clinical Severity Levels
typedef enum {
    AHI_SEV_NORMAL   = 0,
    AHI_SEV_MILD     = 1,
    AHI_SEV_MODERATE = 2,
    AHI_SEV_SEVERE   = 3
} AHI_Severity_t;

// Function Prototypes
void NeuroSomno_Init(uintptr_t base_addr);
void NeuroSomno_SoftReset(void);
void NeuroSomno_StartInference(void);
int  NeuroSomno_IsDone(void);
uint32_t NeuroSomno_GetPredictedClass(void);
uint16_t NeuroSomno_GetAHICount(void);
AHI_Severity_t NeuroSomno_GetSeverity(void);

#endif // NEUROSOMNO_HW_H
