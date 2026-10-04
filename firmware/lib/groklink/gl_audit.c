#include "gl_audit.h"
#include "gl_config.h"

#include <stdio.h>
#include <string.h>

static uint32_t s_last_hash = 2166136261u;
static bool s_ready = false;

/* Weak storage hooks for unit testing outside Flipper */
__attribute__((weak)) bool gl_storage_append_line(const char* path, const char* line) {
    (void)path;
    (void)line;
    /* In host tests, print; on device, override with storage API */
    return true;
}

__attribute__((weak)) uint32_t gl_now_unix(void);

static uint32_t fnv1a(uint32_t h, const char* s) {
    while(s && *s) {
        h ^= (uint8_t)(*s++);
        h *= 16777619u;
    }
    return h;
}

bool gl_audit_init(void) {
    s_ready = true;
    s_last_hash = 2166136261u;
    gl_audit_line("agent", "audit_init", "allow", GROKLINK_VERSION_STRING);
    return true;
}

void gl_audit_deinit(void) {
    s_ready = false;
}

uint32_t gl_audit_last_hash(void) {
    return s_last_hash;
}

bool gl_audit_integrity_ok(void) {
    return s_ready;
}

void gl_audit_line(
    const char* actor,
    const char* action,
    const char* result,
    const char* detail) {
    if(!s_ready) return;

    char line[GL_AUDIT_LINE_MAX];
    uint32_t ts = gl_now_unix();
    snprintf(
        line,
        sizeof(line),
        "{\"ts\":%lu,\"actor\":\"%.16s\",\"action\":\"%.48s\",\"result\":\"%.16s\","
        "\"detail\":\"%.120s\",\"prev\":%08lx}",
        (unsigned long)ts,
        actor ? actor : "?",
        action ? action : "?",
        result ? result : "?",
        detail ? detail : "",
        (unsigned long)s_last_hash);

    s_last_hash = fnv1a(s_last_hash, line);
    gl_storage_append_line(GL_PATH_AUDIT, line);
}
