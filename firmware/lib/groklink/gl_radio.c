/**
 * Radio lock + circuit breaker.
 */
#include "gl_radio.h"
#include "gl_config.h"
#include "gl_audit.h"

#include <string.h>

#if defined(GROKLINK_USE_FURI)
#include <furi.h>
#include <furi_hal.h>
#endif

#ifndef GL_RADIO_BREAKER_THRESHOLD
#define GL_RADIO_BREAKER_THRESHOLD 3
#endif
#ifndef GL_RADIO_BREAKER_COOLDOWN_MS
#define GL_RADIO_BREAKER_COOLDOWN_MS 30000
#endif

static bool s_locked;
static bool s_breaker_open;
static uint32_t s_faults;
static uint32_t s_breaker_open_ms;
static char s_last_fault[48];

#if defined(GROKLINK_USE_FURI)
static FuriMutex* s_mutex;
#endif

void gl_radio_init(void) {
    s_locked = false;
    s_breaker_open = false;
    s_faults = 0;
    s_breaker_open_ms = 0;
    s_last_fault[0] = '\0';
#if defined(GROKLINK_USE_FURI)
    s_mutex = furi_mutex_alloc(FuriMutexTypeNormal);
#endif
    gl_audit_line("radio", "init", "allow", "radio lock ready");
}

void gl_radio_deinit(void) {
#if defined(GROKLINK_USE_FURI)
    if(s_mutex) {
        furi_mutex_free(s_mutex);
        s_mutex = NULL;
    }
#endif
    s_locked = false;
}

bool gl_radio_breaker_open(void) {
#if defined(GROKLINK_USE_FURI)
    if(s_breaker_open) {
        uint32_t now = furi_get_tick();
        if(s_breaker_open_ms && (now - s_breaker_open_ms) > GL_RADIO_BREAKER_COOLDOWN_MS) {
            gl_radio_breaker_reset();
        }
    }
#endif
    return s_breaker_open;
}

void gl_radio_breaker_reset(void) {
    s_breaker_open = false;
    s_faults = 0;
    s_breaker_open_ms = 0;
    s_last_fault[0] = '\0';
    gl_audit_line("radio", "breaker_reset", "allow", "");
}

void gl_radio_breaker_force_open(const char* reason) {
    s_breaker_open = true;
    s_faults = GL_RADIO_BREAKER_THRESHOLD;
    if(reason) {
        strncpy(s_last_fault, reason, sizeof(s_last_fault) - 1);
        s_last_fault[sizeof(s_last_fault) - 1] = '\0';
    } else {
        strncpy(s_last_fault, "force_open", sizeof(s_last_fault) - 1);
    }
#if defined(GROKLINK_USE_FURI)
    s_breaker_open_ms = furi_get_tick();
#endif
    gl_radio_force_safe();
    gl_audit_line("radio", "breaker_force_open", "deny", s_last_fault);
}

void gl_radio_note_fault(const char* reason) {
    s_faults++;
    if(reason) {
        strncpy(s_last_fault, reason, sizeof(s_last_fault) - 1);
        s_last_fault[sizeof(s_last_fault) - 1] = '\0';
    }
    if(s_faults >= GL_RADIO_BREAKER_THRESHOLD) {
        s_breaker_open = true;
#if defined(GROKLINK_USE_FURI)
        s_breaker_open_ms = furi_get_tick();
#endif
        gl_audit_line("radio", "breaker_open", "deny", s_last_fault);
    } else {
        gl_audit_line("radio", "fault", "deny", s_last_fault);
    }
}

void gl_radio_note_ok(void) {
    if(!s_breaker_open) s_faults = 0;
}

uint32_t gl_radio_fault_count(void) {
    return s_faults;
}

const char* gl_radio_last_fault(void) {
    return s_last_fault;
}

bool gl_radio_lock(uint32_t timeout_ms) {
    if(gl_radio_breaker_open()) return false;
#if defined(GROKLINK_USE_FURI)
    if(!s_mutex) return false;
    if(furi_mutex_acquire(s_mutex, timeout_ms) != FuriStatusOk) return false;
    s_locked = true;
    return true;
#else
    (void)timeout_ms;
    if(s_locked) return false;
    s_locked = true;
    return true;
#endif
}

void gl_radio_unlock(void) {
#if defined(GROKLINK_USE_FURI)
    if(s_mutex && s_locked) {
        s_locked = false;
        furi_mutex_release(s_mutex);
    }
#else
    s_locked = false;
#endif
}

void gl_radio_force_safe(void) {
#if defined(GROKLINK_USE_FURI)
    /* Best-effort radio quiet; ignore if never started */
    furi_hal_subghz_idle();
    furi_hal_subghz_sleep();
#endif
    gl_radio_unlock();
    gl_audit_line("radio", "force_safe", "allow", "");
}

bool gl_radio_can_start(void) {
    return !gl_radio_breaker_open();
}
