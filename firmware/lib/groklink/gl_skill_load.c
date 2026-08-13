/**
 * Skill registry loader from SD manifests.
 */
#include "gl_skill.h"
#include "gl_audit.h"
#include "gl_config.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#if defined(GROKLINK_USE_FURI)

#include <furi.h>
#include <storage/storage.h>

extern bool gl_storage_read_file(const char* path, char* buf, size_t cap, size_t* out_len);

static GlRiskClass parse_risk(const char* json) {
    if(strstr(json, "active_tx")) return GlRiskActiveTx;
    if(strstr(json, "gpio")) return GlRiskGpioOut;
    if(strstr(json, "contact")) return GlRiskContact;
    if(strstr(json, "system")) return GlRiskSystem;
    return GlRiskPassiveRx;
}

bool gl_skill_registry_reload(GlSkillRegistry* reg) {
    if(!reg) return false;
    reg->count = 0;

    Storage* storage = furi_record_open(RECORD_STORAGE);
    storage_common_mkdir(storage, GL_PATH_SKILLS);

    File* dir = storage_file_alloc(storage);
    if(storage_dir_open(dir, GL_PATH_SKILLS)) {
        char name[64];
        FileInfo info;
        while(storage_dir_read(dir, &info, name, sizeof(name))) {
            if(!(info.flags & FSF_DIRECTORY)) continue;
            if(name[0] == '.') continue;
            if(reg->count >= GL_MAX_SKILLS) break;

            char path[192];
            snprintf(path, sizeof(path), "%s/%s/manifest.json", GL_PATH_SKILLS, name);
            char buf[512];
            size_t len = 0;
            GlSkillInfo* s = &reg->items[reg->count];
            memset(s, 0, sizeof(*s));
            strncpy(s->id, name, sizeof(s->id) - 1);
            strncpy(s->version, "0.0.0", sizeof(s->version) - 1);
            s->risk = GlRiskPassiveRx;
            s->enabled = true;

            if(gl_storage_read_file(path, buf, sizeof(buf), &len)) {
                s->risk = parse_risk(buf);
                if(strstr(buf, "\"has_fap\": true") || strstr(buf, "\"has_fap\":true")) {
                    s->has_fap = true;
                }
                /* Correct string extract: previous double-quote advance captured
                 * inter-field ",\\n  " from pretty-printed manifests and broke skill_list JSON. */
                const char* vp = strstr(buf, "\"version\"");
                if(vp) {
                    const char* p = vp + 9; /* after "version" */
                    while(*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
                    if(*p == ':') {
                        p++;
                        while(*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
                        if(*p == '"') {
                            p++;
                            size_t vi = 0;
                            while(*p && *p != '"' && vi + 1 < sizeof(s->version)) {
                                unsigned char c = (unsigned char)*p++;
                                if(c < 0x20) continue;
                                /* Keep version charset tight for RPC safety */
                                if((c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') ||
                                   (c >= 'A' && c <= 'Z') || c == '.' || c == '_' || c == '-') {
                                    s->version[vi++] = (char)c;
                                }
                            }
                            s->version[vi] = '\0';
                            if(vi == 0) strncpy(s->version, "0.0.0", sizeof(s->version) - 1);
                        }
                    }
                }
            }
            reg->count++;
        }
        storage_dir_close(dir);
    }
    storage_file_free(dir);
    furi_record_close(RECORD_STORAGE);

    /* Ensure at least one built-in skill name for empty SD */
    if(reg->count == 0) {
        GlSkillInfo* s = &reg->items[reg->count++];
        memset(s, 0, sizeof(*s));
        strncpy(s->id, "lab_pulse_counter", sizeof(s->id) - 1);
        strncpy(s->version, "1.0.0", sizeof(s->version) - 1);
        strncpy(s->description, "builtin fallback", sizeof(s->description) - 1);
        s->risk = GlRiskPassiveRx;
        s->enabled = true;
    }

    char detail[24];
    snprintf(detail, sizeof(detail), "n=%u", (unsigned)reg->count);
    gl_audit_line("agent", "skill_reload", "allow", detail);
    return true;
}

#else

bool gl_skill_registry_reload(GlSkillRegistry* reg) {
    if(!reg) return false;
    reg->count = 0;
    if(reg->count < GL_MAX_SKILLS) {
        GlSkillInfo* s = &reg->items[reg->count++];
        memset(s, 0, sizeof(*s));
        strncpy(s->id, "lab_pulse_counter", sizeof(s->id) - 1);
        strncpy(s->version, "1.0.0", sizeof(s->version) - 1);
        strncpy(s->description, "Count sub-GHz pulses (passive)", sizeof(s->description) - 1);
        s->risk = GlRiskPassiveRx;
        s->enabled = true;
    }
    gl_audit_line("agent", "skill_reload", "allow", "stub");
    return true;
}

#endif
