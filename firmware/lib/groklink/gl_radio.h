/**
 * Global radio lock + fault circuit breaker for SubGHz (service safety).
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void gl_radio_init(void);
void gl_radio_deinit(void);

/** Exclusive radio access. Returns false if breaker open or busy timeout. */
bool gl_radio_lock(uint32_t timeout_ms);
void gl_radio_unlock(void);

bool gl_radio_breaker_open(void);
void gl_radio_breaker_reset(void);
/** Lab/research: force breaker open immediately (blocks radio until reset/cooldown). */
void gl_radio_breaker_force_open(const char* reason);
void gl_radio_note_fault(const char* reason);
void gl_radio_note_ok(void);

uint32_t gl_radio_fault_count(void);
const char* gl_radio_last_fault(void);

/** Force radio idle/sleep and unlock (fail-safe after errors). */
void gl_radio_force_safe(void);

/** True if RPC/mission may start radio work. */
bool gl_radio_can_start(void);

#ifdef __cplusplus
}
#endif
