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

static void strip_json_comments(char* s) {
    char* r = s;
    char* w = s;
    int in_str = 0;
    while(*r) {
        if(in_str) {
            if(*r == '\\' && r[1]) {
                *w++ = *r++;
                *w++ = *r++;
                continue;
            }
            if(*r == '"') in_str = 0;
            *w++ = *r++;
            continue;
        }
        if(*r == '"') {
            in_str = 1;
            *w++ = *r++;
            continue;
        }
        if(r[0] == '/' && r[1] == '/') {
            r += 2;
            while(*r && *r != '\n') r++;
            continue;
        }
        if(r[0] == '/' && r[1] == '*') {
            r += 2;
            while(*r && !(r[0] == '*' && r[1] == '/')) r++;
            if(*r) r += 2;
            continue;
        }
        *w++ = *r++;
    }
    *w = '\0';
}

static const char* json_array_after_key(const char* buf, const char* key) {
    char pat[48];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char* p = buf;
    size_t klen = strlen(pat);
    while((p = strstr(p, pat)) != NULL) {
        const char* q = p + klen;
        while(*q == ' ' || *q == '\t' || *q == '\r' || *q == '\n') q++;
        if(*q != ':') {
            p += klen;
            continue;
        }
        q++;
        while(*q == ' ' || *q == '\t' || *q == '\r' || *q == '\n') q++;
        if(*q == '[') return q + 1;
        p += klen;
    }
    return NULL;
}

/* Same unit rule as the OS loader. Applied only to array entries. */
static uint32_t listed_to_hz(uint32_t v) {
    return v > 10000u ? v : v * 1000000u;
}

static void append_banned_array(GlSafetyState* st, const char* arr) {
    if(!arr) return;
    const char* p = arr;
    while(*p && st->banned_freq_count < 32) {
        while(*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n' || *p == ',') p++;
        if(*p == ']' || *p == '\0') return;
        if(*p == '"') {
            p++;
            while(*p && *p != '"') {
                if(*p == '\\' && p[1]) p += 2;
                else p++;
            }
            if(*p == '"') p++;
            continue;
        }
        if(*p >= '0' && *p <= '9') {
            char* end = NULL;
            unsigned long raw = strtoul(p, &end, 10);
            if(end && end != p) {
                st->banned_freq_hz[st->banned_freq_count++] = listed_to_hz((uint32_t)raw);
                p = end;
                continue;
            }
        }
        p++;
    }
}

static void cap_cstr(char* buf, size_t cap, size_t len) {
    if(cap == 0) return;
    if(len >= cap) len = cap - 1;
    buf[len] = '\0';
}

bool gl_safety_reload_blacklist(GlSafetyState* st) {
    if(!st) return false;
    st->banned_freq_count = 0;
    st->banned_gpio_count = 0;

    char buf[1024];
    size_t len = 0;
    if(gl_storage_read_file(GL_PATH_BLACKLIST "/freq_mhz.json", buf, sizeof(buf), &len)) {
        cap_cstr(buf, sizeof(buf), len);
        strip_json_comments(buf);
        append_banned_array(st, json_array_after_key(buf, "banned_centers_hz"));
        append_banned_array(st, json_array_after_key(buf, "banned_mhz"));
    }

    len = 0;
    if(gl_storage_read_file(GL_PATH_BLACKLIST "/gpio_pins.json", buf, sizeof(buf), &len)) {
        cap_cstr(buf, sizeof(buf), len);
        strip_json_comments(buf);
        const char* p = json_array_after_key(buf, "banned_pins");
        if(p) {
            while(*p && *p != ']' && st->banned_gpio_count < 16) {
                while(*p == ' ' || *p == ',' || *p == '\n' || *p == '\r' || *p == '\t') p++;
                if(*p == ']' || *p == '\0') break;
                if(*p == '"') {
                    p++;
                    while(*p && *p != '"') {
                        if(*p == '\\' && p[1]) p += 2;
                        else p++;
                    }
                    if(*p == '"') p++;
                    continue;
                }
                if((*p >= '0' && *p <= '9') || *p == '-') {
                    char* end = NULL;
                    long v = strtol(p, &end, 10);
                    if(end && end != p) {
                        st->banned_gpio[st->banned_gpio_count++] = (int32_t)v;
                        p = end;
                        continue;
                    }
                }
                p++;
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
