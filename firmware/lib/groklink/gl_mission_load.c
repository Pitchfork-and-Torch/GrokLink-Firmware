/**
 * Mission directory loader (Furi storage).
 */
#include "gl_mission.h"
#include "gl_audit.h"
#include "gl_config.h"

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#if defined(GROKLINK_USE_FURI)

#include <furi.h>
#include <storage/storage.h>

extern bool gl_storage_read_file(const char* path, char* buf, size_t cap, size_t* out_len);

static void gl_fill_demo_steps(GlMission* m) {
    /* Log-only default steps  -  do NOT inject SubGHz into service context */
    if(m->step_count == 0 || (m->step_count == 1 && m->steps[0].type == GlOpLog)) {
        m->step_count = 0;
        m->steps[m->step_count].type = GlOpLog;
        strncpy(
            m->steps[m->step_count].message,
            "mission loaded (radio steps via RPC only)",
            sizeof(m->steps[0].message) - 1);
        m->step_count++;
    }
    m->max_risk = GlRiskPassiveRx;
    m->state = GlMissionIdle;
    m->autonomous = false; /* force off until operator enables safely */
}

bool gl_mission_load_dir(GlMissionBank* bank) {
    if(!bank) return false;
    bank->count = 0;
    bank->active_index = -1;

    Storage* storage = furi_record_open(RECORD_STORAGE);
    storage_common_mkdir(storage, GL_SD_ROOT);
    storage_common_mkdir(storage, GL_PATH_MISSIONS);

    File* dir = storage_file_alloc(storage);
    bool any = false;
    if(storage_dir_open(dir, GL_PATH_MISSIONS)) {
        char name[64];
        FileInfo info;
        while(storage_dir_read(dir, &info, name, sizeof(name))) {
            if(info.flags & FSF_DIRECTORY) continue;
            size_t nlen = strlen(name);
            if(nlen < 6 || strcmp(name + nlen - 5, ".json") != 0) {
                /* also accept .mission.json */
            }
            if(strstr(name, ".json") == NULL) continue;
            if(bank->count >= GL_MAX_MISSIONS) break;

            char path[160];
            snprintf(path, sizeof(path), "%s/%s", GL_PATH_MISSIONS, name);
            char* buf = malloc(2048);
            if(!buf) continue;
            size_t len = 0;
            if(gl_storage_read_file(path, buf, 2048, &len)) {
                GlMission* m = &bank->items[bank->count];
                if(gl_mission_parse_json(buf, len, m)) {
                    /* Detect autonomous + interval heuristically */
                    if(strstr(buf, "\"autonomous\": true") || strstr(buf, "\"autonomous\":true")) {
                        m->autonomous = true;
                    }
                    if(strstr(buf, "\"every_sec\"")) {
                        const char* p = strstr(buf, "\"every_sec\"");
                        p = strchr(p, ':');
                        if(p) m->every_sec = (uint32_t)strtoul(p + 1, NULL, 10);
                    }
                    if(strstr(buf, "subghz_rx")) {
                        gl_fill_demo_steps(m);
                    }
                    bank->count++;
                    any = true;
                }
            }
            free(buf);
        }
        storage_dir_close(dir);
    }
    storage_file_free(dir);
    furi_record_close(RECORD_STORAGE);

    char detail[32];
    snprintf(detail, sizeof(detail), "n=%u", (unsigned)bank->count);
    gl_audit_line("agent", "mission_load_dir", "allow", detail);
    return any || true; /* SD present even if empty */
}

#else

bool gl_mission_load_dir(GlMissionBank* bank) {
    if(!bank) return false;
    gl_audit_line("agent", "mission_load_dir", "allow", "stub");
    return true;
}

#endif
