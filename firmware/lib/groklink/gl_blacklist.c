/**
 * Load blacklists from SD JSON (simple extractors).
 */
#include "gl_safety.h"
#include "gl_config.h"
#include "gl_audit.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#if defined(GROKLINK_USE_FURI)

extern bool gl_storage_read_file(const char* path, char* buf, size_t cap, size_t* out_len);

bool gl_safety_reload_blacklist(GlSafetyState* st) {
    if(!st) return false;
    st->banned_freq_count = 0;
    st->banned_gpio_count = 0;

    char buf[1024];
    size_t len = 0;
    if(gl_storage_read_file(GL_PATH_BLACKLIST "/freq_mhz.json", buf, sizeof(buf), &len)) {
        /* Parse numbers after banned_centers_hz array crudely */
        const char* p = strstr(buf, "banned_centers_hz");
        if(p) {
            p = strchr(p, '[');
            if(p) {
                p++;
                while(*p && *p != ']' && st->banned_freq_count < 32) {
                    while(*p == ' ' || *p == ',' || *p == '\n' || *p == '\r' || *p == '\t') p++;
                    if(*p == ']') break;
                    if(*p >= '0' && *p <= '9') {
                        st->banned_freq_hz[st->banned_freq_count++] = (uint32_t)strtoul(p, (char**)&p, 10);
                    } else {
                        p++;
                    }
                }
            }
        }
    }

    if(gl_storage_read_file(GL_PATH_BLACKLIST "/gpio_pins.json", buf, sizeof(buf), &len)) {
        const char* p = strstr(buf, "banned_pins");
        if(p) {
            p = strchr(p, '[');
            if(p) {
                p++;
                while(*p && *p != ']' && st->banned_gpio_count < 16) {
                    while(*p == ' ' || *p == ',' || *p == '\n' || *p == '\r' || *p == '\t') p++;
                    if(*p == ']') break;
                    if((*p >= '0' && *p <= '9') || *p == '-') {
                        st->banned_gpio[st->banned_gpio_count++] = (int32_t)strtol(p, (char**)&p, 10);
                    } else {
                        p++;
                    }
                }
            }
        }
    }

    char detail[48];
    snprintf(
        detail,
        sizeof(detail),
        "freq=%u gpio=%u",
        (unsigned)st->banned_freq_count,
        (unsigned)st->banned_gpio_count);
    gl_audit_line("agent", "blacklist_reload", "allow", detail);
    return true;
}

#endif
