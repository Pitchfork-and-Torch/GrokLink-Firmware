#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

bool gl_audit_init(void);
void gl_audit_deinit(void);

/** Append one audit line (JSONL). actor/action/result/detail are truncated. */
void gl_audit_line(
    const char* actor,
    const char* action,
    const char* result,
    const char* detail);

/** Last line hash for status (simple FNV-1a, not crypto). */
uint32_t gl_audit_last_hash(void);

/** Optional: verify chain file exists / readable */
bool gl_audit_integrity_ok(void);

#ifdef __cplusplus
}
#endif
