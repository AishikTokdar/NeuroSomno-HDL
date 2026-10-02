#include "../embedded/c_driver/neurosomno_hw.h"
#include <assert.h>

static uint32_t registers[16];
static uint64_t ticks;
static uint64_t clock_us(void *context) { (void)context; return ticks++; }
static int send_ok(const int16_t *data, size_t count, void *context) {
    (void)context;
    assert(count == 784 && data[0] == -8192);
    registers[REG_NNOUT_OFFSET / 4] = 1;
    registers[REG_STATUS_OFFSET / 4] = STATUS_DONE_MASK;
    return 0;
}
static int send_stuck(const int16_t *data, size_t count, void *context) {
    (void)data; (void)count; (void)context;
    return 0;
}
int main(void) {
    int16_t data[784] = {-8192};
    uint32_t predicted = 9;
    NeuroSomno_Init((uintptr_t)registers);
    assert(NeuroSomno_Predict(data, 783, &predicted, 100, send_ok, clock_us, 0) == -1);
    assert(NeuroSomno_Predict(data, 784, &predicted, 100, send_ok, clock_us, 0) == 0);
    assert(predicted == 1);
    registers[REG_STATUS_OFFSET / 4] = 0;
    predicted = 9;
    assert(NeuroSomno_Predict(data, 784, &predicted, 3, send_stuck, clock_us, 0) == -2);
    assert(predicted == 9);
    return 0;
}
