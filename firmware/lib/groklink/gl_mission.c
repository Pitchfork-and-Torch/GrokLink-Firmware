#include "gl_mission.h"
#include "gl_audit.h"
#include "gl_hw.h"
#include "gl_radio.h"

#include <string.h>
#include <stdio.h>

__attribute__((weak)) uint32_t gl_now_unix(void);
__attribute__((weak)) bool gl_storage_read_file(const char* path, char* buf, size_t cap, size_t* out_len);

bool gl_mission_bank_init(GlMissionBank* bank) {
    if(!bank) return false;
    memset(bank, 0, sizeof(*bank));
    bank->active_index = -1;
    return true;
}

GlMission* gl_mission_find(GlMissionBank* bank, const char* id) {
    if(!bank || !id) return NULL;
    for(size_t i = 0; i < bank->count; i++) {
        if(strncmp(bank->items[i].id, id, GL_MISSION_ID_MAX) == 0) return &bank->items[i];
    }
    return NULL;
}

/* Extract JSON string value for key. Handles pretty-printed whitespace.
 * Previous bug: double-advance on quotes captured ",\\n  " between fields. */
static bool gl_json_copy_str(const char* json, const char* key, char* out, size_t out_cap) {
    if(!json || !key || !out || out_cap == 0) return false;
    out[0] = '\0';
    char pat[48];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char* p = strstr(json, pat);
    if(!p) return false;
    p += strlen(pat);
    while(*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
    if(*p != ':') return false;
    p++;
    while(*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
    if(*p != '"') return false;
    p++;
    size_t i = 0;
    while(*p && *p != '"' && i + 1 < out_cap) {
        /* Drop C0 controls so RPC JSON never embeds bare newlines */
        unsigned char c = (unsigned char)*p++;
        if(c < 0x20) continue;
        if(c == '\\') {
            /* Keep simple escapes as literal next char (no full unescape) */
            if(*p) c = (unsigned char)*p++;
            if(c < 0x20) continue;
        }
        out[i++] = (char)c;
    }
    out[i] = '\0';
    return i > 0;
}

/* Minimal demo parser: prefer full cJSON in production overlay */
bool gl_mission_parse_json(const char* json, size_t len, GlMission* out) {
    if(!json || !out || len == 0) return false;
    memset(out, 0, sizeof(*out));
    if(!gl_json_copy_str(json, "id", out->id, GL_MISSION_ID_MAX) || out->id[0] == '\0') {
        strncpy(out->id, "unnamed", GL_MISSION_ID_MAX - 1);
    }
    if(!gl_json_copy_str(json, "name", out->name, sizeof(out->name)) || out->name[0] == '\0') {
        strncpy(out->name, out->id, sizeof(out->name) - 1);
    }
    out->max_risk = GlRiskPassiveRx;
    out->state = GlMissionIdle;
    /* Default single passive step if parse is shallow  -  loaders may fill steps */
    out->step_count = 1;
    out->steps[0].type = GlOpLog;
    strncpy(out->steps[0].message, "mission loaded", sizeof(out->steps[0].message) - 1);
    return true;
}

/* gl_mission_load_dir implemented in gl_mission_load.c */

static bool mission_safety_gate(
    GlSafetyState* safety,
    GlMission* m,
    const char* confirm_id) {
    if(m->max_risk <= GlRiskPassiveRx && !m->require_confirm) return true;
    GlSafetyRequest req = {
        .actor = GlActorAgent,
        .action = "mission_start",
        .risk = m->max_risk,
        .freq_hz = 0,
        .gpio_pin = -1,
        .protocol = NULL,
        .confirm_id = confirm_id,
        .rationale = m->id,
    };
    GlSafetyDecision d = gl_safety_check(safety, &req);
    return d.result == GlSafetyAllow;
}

bool gl_mission_start(
    GlMissionBank* bank,
    GlSafetyState* safety,
    const char* id,
    const char* confirm_id) {
    GlMission* m = gl_mission_find(bank, id);
    if(!m) return false;
    if(bank->active_index >= 0) {
        gl_audit_line("agent", "mission_start", "deny", "already running");
        return false;
    }
    if(!mission_safety_gate(safety, m, confirm_id)) return false;

    m->state = GlMissionRunning;
    m->step_index = 0;
    m->error[0] = '\0';
    bank->active_index = (int)(m - bank->items);
    gl_audit_line("agent", "mission_start", "allow", m->id);
    return true;
}

void gl_mission_stop(GlMissionBank* bank, const char* id) {
    if(!bank) return;
    GlMission* m = id ? gl_mission_find(bank, id) : NULL;
    if(!m && bank->active_index >= 0) m = &bank->items[bank->active_index];
    if(!m) return;
    m->state = GlMissionIdle;
    m->step_index = 0;
    bank->active_index = -1;
    gl_hw_release_all();
    gl_audit_line("agent", "mission_stop", "allow", m->id);
}

static void run_step(GlMission* m, GlSafetyState* safety, GlMissionStep* st) {
    switch(st->type) {
    case GlOpDelay:
        /* Agent tick handles delay via duration + step hold  -  simplified */
        break;
    case GlOpLog:
        gl_audit_line("mission", m->id, "log", st->message);
        break;
    case GlOpSubGhzRx: {
        /* Mission radio isolation: skip if breaker open or radio busy */
        if(!gl_radio_can_start()) {
            gl_audit_line("mission", m->id, "skip", "radio_breaker");
            break;
        }
        GlSafetyRequest req = {
            .actor = GlActorAgent,
            .action = "subghz_rx",
            .risk = GlRiskPassiveRx,
            .freq_hz = st->freq_hz,
            .gpio_pin = -1,
            .confirm_id = NULL,
            .rationale = m->id,
        };
        {
            GlSafetyDecision d = gl_safety_check(safety, &req);
            if(d.result == GlSafetyRateLimited) {
                gl_audit_line("mission", m->id, "skip", "rx_cooldown");
                break;
            }
            if(d.result != GlSafetyAllow) {
                m->state = GlMissionError;
                strncpy(m->error, "rx denied", sizeof(m->error) - 1);
                return;
            }
        }
        /* Cap duration  -  long blocking RX in service context is unsafe */
        uint32_t dur = st->duration_ms;
        if(dur == 0 || dur > 1000) dur = 400;
        int32_t pulses = 0;
        if(gl_hw_subghz_rx(st->freq_hz, dur, &pulses)) {
            m->last_metric_value = pulses;
            gl_safety_note_rx(safety);
        } else {
            gl_radio_note_fault("mission_rx_fail");
            gl_radio_force_safe();
        }
        break;
    }
    case GlOpSubGhzTxFile: {
        GlSafetyRequest req = {
            .actor = GlActorAgent,
            .action = "subghz_tx",
            .risk = GlRiskActiveTx,
            .freq_hz = st->freq_hz,
            .gpio_pin = -1,
            .confirm_id = NULL, /* autonomous TX only if mission pre-confirmed */
            .rationale = m->id,
        };
        GlSafetyDecision d = gl_safety_check(safety, &req);
        if(d.result != GlSafetyAllow) {
            m->state = GlMissionError;
            strncpy(m->error, "tx denied", sizeof(m->error) - 1);
            return;
        }
        gl_hw_subghz_tx_file(st->path);
        gl_safety_note_tx(safety, GL_TX_MAX_MS);
        break;
    }
    case GlOpGpioWrite: {
        GlSafetyRequest req = {
            .actor = GlActorAgent,
            .action = "gpio_write",
            .risk = GlRiskGpioOut,
            .freq_hz = 0,
            .gpio_pin = st->gpio_pin,
            .confirm_id = NULL,
            .rationale = m->id,
        };
        if(gl_safety_check(safety, &req).result != GlSafetyAllow) {
            m->state = GlMissionError;
            strncpy(m->error, "gpio denied", sizeof(m->error) - 1);
            return;
        }
        gl_hw_gpio_write((uint32_t)st->gpio_pin, st->gpio_value);
        break;
    }
    case GlOpDecision: {
        bool pass = false;
        if(st->cmp == 0) pass = m->last_metric_value >= st->threshold;
        else if(st->cmp == 1) pass = m->last_metric_value <= st->threshold;
        else pass = m->last_metric_value == st->threshold;
        gl_audit_line("mission", m->id, pass ? "decision_true" : "decision_false", st->metric);
        break;
    }
    case GlOpSkillRun:
        gl_hw_skill_run(st->skill_id);
        break;
    default:
        gl_audit_line("mission", m->id, "skip", "unknown op");
        break;
    }
}

void gl_mission_tick(GlMissionBank* bank, GlSafetyState* safety) {
    if(!bank) return;

    if(bank->active_index < 0) {
        /**
         * Autonomous auto-start DISABLED by default.
         * SubGHz from the agent service stack caused reboot loops on some builds.
         * Start missions explicitly: groklink mission start <id>
         */
#if defined(GL_ENABLE_AUTONOMOUS_MISSIONS)
        uint32_t now = gl_now_unix();
        for(size_t i = 0; i < bank->count; i++) {
            GlMission* m = &bank->items[i];
            if(!m->autonomous || m->every_sec == 0) continue;
            if(m->state != GlMissionIdle && m->state != GlMissionArmed) continue;
            if(m->last_run_unix && (now - m->last_run_unix) < m->every_sec) continue;
            if(m->max_risk > GlRiskPassiveRx) continue;
            bool radio = false;
            for(uint8_t s = 0; s < m->step_count; s++) {
                if(m->steps[s].type == GlOpSubGhzRx || m->steps[s].type == GlOpSubGhzTxFile ||
                   m->steps[s].type == GlOpIrRx || m->steps[s].type == GlOpIrTxFile) {
                    radio = true;
                    break;
                }
            }
            if(radio) continue;
            m->state = GlMissionRunning;
            m->step_index = 0;
            bank->active_index = (int)i;
            gl_audit_line("agent", "mission_auto", "allow", m->id);
            break;
        }
#else
        (void)safety;
#endif
        if(bank->active_index < 0) return;
    }

    GlMission* m = &bank->items[bank->active_index];
    if(m->state != GlMissionRunning) return;
    if(m->step_index >= m->step_count) {
        m->state = GlMissionDone;
        m->last_run_unix = gl_now_unix();
        bank->active_index = -1;
        gl_hw_release_all();
        gl_audit_line("agent", "mission_done", "allow", m->id);
        m->state = GlMissionIdle;
        return;
    }

    GlMissionStep* st = &m->steps[m->step_index];
    run_step(m, safety, st);
    if(m->state == GlMissionError) {
        bank->active_index = -1;
        gl_hw_release_all();
        gl_audit_line("agent", "mission_error", "deny", m->error);
        return;
    }
    m->step_index++;
}
