/**
 * Hardware facade  -  thin wrappers over Flipper services.
 * Implementations in gl_hw.c call SubGhz / Nfc / Infrared / Gpio APIs
 * when linked into full firmware; weak stubs for host compile.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

bool gl_hw_init(void);
void gl_hw_release_all(void);

bool gl_hw_subghz_rx(uint32_t freq_hz, uint32_t duration_ms, int32_t* out_pulse_count);
bool gl_hw_subghz_tx_file(const char* path);

bool gl_hw_ir_rx(uint32_t duration_ms);
bool gl_hw_ir_tx_file(const char* path);

bool gl_hw_nfc_read(uint32_t timeout_ms, char* uid_out, size_t uid_cap);

bool gl_hw_gpio_read(uint32_t pin, uint8_t* value);
bool gl_hw_gpio_write(uint32_t pin, uint8_t value);

bool gl_hw_skill_run(const char* skill_id);

#ifdef __cplusplus
}
#endif
