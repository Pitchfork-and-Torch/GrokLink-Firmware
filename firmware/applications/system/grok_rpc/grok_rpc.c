/**
 * GrokRPC  -  JSON-framed control plane (v2).
 *
 * Request examples:
 *   {"id":1,"method":"status"}
 *   {"id":2,"method":"session_start","edu_ack":"I_WILL_USE_ONLY_AUTHORIZED_TARGETS"}
 *   {"id":3,"method":"spectrum_scan","duration_ms":1000}
 *   {"id":4,"method":"subghz_rx","freq_hz":433920000,"duration_ms":1000}
 *   {"id":5,"method":"ir_rx","duration_ms":1000}
 *   {"id":6,"method":"gpio_read","pin":1}
 */
#include "grok_rpc.h"

#include "grok_agent.h"
#include "groklink.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

bool grok_rpc_session_init(GrokRpcSession* s) {
    if(!s) return false;
    memset(s, 0, sizeof(*s));
    s->format = GrokRpcFmtJson;
    return true;
}

static bool json_get_str(const char* json, const char* key, char* out, size_t out_len) {
    char pat[48];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char* p = strstr(json, pat);
    if(!p) return false;
    p = strchr(p + strlen(pat), ':');
    if(!p) return false;
    p = strchr(p, '"');
    if(!p) return false;
    p++;
    const char* q = strchr(p, '"');
    if(!q) return false;
    size_t n = (size_t)(q - p);
    if(n >= out_len) n = out_len - 1;
    memcpy(out, p, n);
    out[n] = '\0';
    return true;
}

static uint32_t json_get_u32(const char* json, const char* key, uint32_t def) {
    char pat[48];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char* p = strstr(json, pat);
    if(!p) return def;
    p = strchr(p, ':');
    if(!p) return def;
    return (uint32_t)strtoul(p + 1, NULL, 10);
}

static bool json_has_method(const char* json, const char* method) {
    char pat[64];
    snprintf(pat, sizeof(pat), "\"method\":\"%s\"", method);
    if(strstr(json, pat)) return true;
    snprintf(pat, sizeof(pat), "\"method\": \"%s\"", method);
    return strstr(json, pat) != NULL;
}

static size_t write_str(uint8_t* resp, size_t cap, const char* s) {
    size_t n = strlen(s);
    if(n >= cap) n = cap - 1;
    memcpy(resp, s, n);
    resp[n] = '\0';
    return n;
}

/** Strip C0 controls from a short id/version for safe JSON embedding */
static void sanitize_token(const char* in, char* out, size_t out_cap) {
    if(!out || out_cap == 0) return;
    size_t j = 0;
    if(in) {
        for(size_t i = 0; in[i] && j + 1 < out_cap; i++) {
            unsigned char c = (unsigned char)in[i];
            if(c < 0x20 || c == '"' || c == '\\') continue;
            out[j++] = (char)c;
        }
    }
    out[j] = '\0';
    if(j == 0 && out_cap > 1) {
        out[0] = '?';
        out[1] = '\0';
    }
}

static bool freq_in_subghz_window(uint32_t freq_hz) {
    return freq_hz >= GL_SUBGHZ_FREQ_MIN_HZ && freq_hz <= GL_SUBGHZ_FREQ_MAX_HZ;
}

static uint32_t clamp_rx_duration(uint32_t dur) {
    if(dur == 0) return GL_RX_DURATION_DEFAULT_MS;
    if(dur > GL_RX_DURATION_MAX_MS) return GL_RX_DURATION_MAX_MS;
    return dur;
}

bool grok_rpc_handle(
    GrokRpcSession* s,
    const uint8_t* req,
    size_t req_len,
    uint8_t* resp,
    size_t resp_cap,
    size_t* resp_len) {
    if(!s || !req || !resp || !resp_cap || !resp_len) return false;
    *resp_len = 0;

    char buf[512];
    size_t n = req_len < sizeof(buf) - 1 ? req_len : sizeof(buf) - 1;
    memcpy(buf, req, n);
    buf[n] = '\0';

    uint32_t id = json_get_u32(buf, "id", 0);
    GrokLinkCore* core = grok_agent_get_core();
    char out[768];

    if(json_has_method(buf, "ping") || json_has_method(buf, "methods")) {
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"api\":%d,\"version\":\"%s\","
            "\"methods\":[\"ping\",\"methods\",\"status\",\"session_start\",\"confirm\","
            "\"mission_list\",\"mission_start\",\"mission_reload\",\"skill_list\","
            "\"skill_reload\",\"subghz_rx\",\"subghz_tx\",\"spectrum_scan\","
            "\"ir_rx\",\"gpio_read\",\"gpio_write\",\"radio_reset\",\"radio_status\","
            "\"radio_trip\"]}",
            (unsigned long)id,
            GROKLINK_RPC_API,
            GROKLINK_VERSION_STRING);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "session_start")) {
        char edu[64] = {0};
        json_get_str(buf, "edu_ack", edu, sizeof(edu));
        if(strcmp(edu, GL_EDU_ACK_PHRASE) != 0) {
            snprintf(
                out,
                sizeof(out),
                "{\"id\":%lu,\"ok\":false,\"error\":\"edu_ack required: %s\"}",
                (unsigned long)id,
                GL_EDU_ACK_PHRASE);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        s->edu_ack = true;
        s->session_active = true;
        snprintf(s->session_id, sizeof(s->session_id), "s%08lx", (unsigned long)(id * 2654435761u));
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"session_id\":\"%s\",\"agent_version\":\"%s\","
            "\"api\":%d,\"safety_mode\":\"%s\","
            "\"features\":[\"missions\",\"skills\",\"stream\",\"safety\",\"spectrum\","
            "\"ir_rx\",\"gpio\"],"
            "\"sd_ok\":%s,\"agent_running\":%s,"
            "\"freq_min_hz\":%lu,\"freq_max_hz\":%lu,\"rx_max_ms\":%lu}",
            (unsigned long)id,
            s->session_id,
            GROKLINK_VERSION_STRING,
            GROKLINK_RPC_API,
            core ? core->safety_mode : "degraded",
            (core && core->sd_ok) ? "true" : "false",
            grok_agent_is_running() ? "true" : "false",
            (unsigned long)GL_SUBGHZ_FREQ_MIN_HZ,
            (unsigned long)GL_SUBGHZ_FREQ_MAX_HZ,
            (unsigned long)GL_RX_DURATION_MAX_MS);
        *resp_len = write_str(resp, resp_cap, out);
        gl_audit_line("rpc", "session_start", "allow", s->session_id);
        return true;
    }

    if(json_has_method(buf, "status")) {
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"firmware_version\":\"groklink-%s\","
            "\"agent_version\":\"%s\",\"api\":%d,\"battery_pct\":0,\"sd_present\":%s,"
            "\"agent_running\":%s,\"safety_mode\":\"%s\",\"skill_count\":%u,"
            "\"mission_count\":%u,\"last_audit_hash\":\"%08lx\","
            "\"freq_min_hz\":%lu,\"freq_max_hz\":%lu,\"rx_max_ms\":%lu,"
            "\"tx_mode\":\"ack_file\",\"radio_breaker\":%s,\"radio_faults\":%lu}",
            (unsigned long)id,
            GROKLINK_VERSION_STRING,
            GROKLINK_VERSION_STRING,
            GROKLINK_RPC_API,
            (core && core->sd_ok) ? "true" : "false",
            grok_agent_is_running() ? "true" : "false",
            core ? core->safety_mode : "degraded",
            core ? (unsigned)core->skills.count : 0,
            core ? (unsigned)core->missions.count : 0,
            (unsigned long)gl_audit_last_hash(),
            (unsigned long)GL_SUBGHZ_FREQ_MIN_HZ,
            (unsigned long)GL_SUBGHZ_FREQ_MAX_HZ,
            (unsigned long)GL_RX_DURATION_MAX_MS,
            gl_radio_breaker_open() ? "true" : "false",
            (unsigned long)gl_radio_fault_count());
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "radio_reset")) {
        gl_radio_breaker_reset();
        gl_hw_release_all();
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"message\":\"radio breaker reset\",\"breaker_open\":false,\"faults\":0}",
            (unsigned long)id);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "radio_trip")) {
        /* Lab research: force circuit breaker open (blocks SubGHz until reset/cooldown). */
        char reason[40] = {0};
        json_get_str(buf, "reason", reason, sizeof(reason));
        if(reason[0] == '\0') {
            strncpy(reason, "lab_trip", sizeof(reason) - 1);
        }
        gl_radio_breaker_force_open(reason);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"message\":\"radio breaker OPEN\",\"breaker_open\":true,"
            "\"faults\":%lu,\"last_fault\":\"%s\"}",
            (unsigned long)id,
            (unsigned long)gl_radio_fault_count(),
            gl_radio_last_fault());
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "radio_status")) {
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"breaker_open\":%s,\"faults\":%lu,\"last_fault\":\"%s\","
            "\"can_start\":%s,\"threshold\":%u,\"cooldown_ms\":%u}",
            (unsigned long)id,
            gl_radio_breaker_open() ? "true" : "false",
            (unsigned long)gl_radio_fault_count(),
            gl_radio_last_fault(),
            gl_radio_can_start() ? "true" : "false",
            (unsigned)3,
            (unsigned)30000);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "confirm")) {
        if(!core) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"agent offline\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        char action[32] = {0};
        json_get_str(buf, "action", action, sizeof(action));
        if(action[0] == '\0') strncpy(action, "subghz_tx", sizeof(action) - 1);
        uint32_t ttl = json_get_u32(buf, "ttl", 60);
        char cid[24];
        if(!gl_safety_issue_confirm(&core->safety, action, ttl, cid, sizeof(cid))) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"confirm slots full\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"result\":\"confirm_issued\",\"confirm_id\":\"%s\",\"expires_in_sec\":%lu}",
            (unsigned long)id,
            cid,
            (unsigned long)ttl);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "mission_list")) {
        char list[400] = "[";
        if(core) {
            for(size_t i = 0; i < core->missions.count; i++) {
                char sid[GL_MISSION_ID_MAX];
                char sname[48];
                char item[120];
                sanitize_token(core->missions.items[i].id, sid, sizeof(sid));
                sanitize_token(core->missions.items[i].name, sname, sizeof(sname));
                snprintf(
                    item,
                    sizeof(item),
                    "%s{\"id\":\"%s\",\"name\":\"%s\",\"autonomous\":%s}",
                    i ? "," : "",
                    sid,
                    sname,
                    core->missions.items[i].autonomous ? "true" : "false");
                if(strlen(list) + strlen(item) + 2 < sizeof(list)) strcat(list, item);
            }
        }
        strcat(list, "]");
        snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":true,\"missions\":%s}", (unsigned long)id, list);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "mission_reload")) {
        if(core) gl_mission_load_dir(&core->missions);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"mission_count\":%u}",
            (unsigned long)id,
            core ? (unsigned)core->missions.count : 0);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "mission_start")) {
        if(!core) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"agent offline\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        char mid[GL_MISSION_ID_MAX] = {0};
        char cid[24] = {0};
        json_get_str(buf, "mission_id", mid, sizeof(mid));
        json_get_str(buf, "confirm_id", cid, sizeof(cid));
        bool ok = gl_mission_start(&core->missions, &core->safety, mid, cid[0] ? cid : NULL);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":%s,\"message\":\"%s\"}",
            (unsigned long)id,
            ok ? "true" : "false",
            ok ? "started" : "denied_or_missing");
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "subghz_rx")) {
        if(!core) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"agent offline\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        uint32_t freq = json_get_u32(buf, "freq_hz", 433920000);
        uint32_t dur = clamp_rx_duration(json_get_u32(buf, "duration_ms", GL_RX_DURATION_DEFAULT_MS));
        if(!freq_in_subghz_window(freq)) {
            snprintf(
                out,
                sizeof(out),
                "{\"id\":%lu,\"ok\":false,\"safety\":\"deny\",\"message\":\"freq out of range\"}",
                (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        GlSafetyRequest sreq = {
            .actor = GlActorRpc,
            .action = "subghz_rx",
            .risk = GlRiskPassiveRx,
            .freq_hz = freq,
            .gpio_pin = -1,
            .confirm_id = NULL,
            .rationale = "rpc",
        };
        GlSafetyDecision d = gl_safety_check(&core->safety, &sreq);
        if(d.result != GlSafetyAllow) {
            const char* sname = "deny";
            if(d.result == GlSafetyRateLimited) sname = "rate_limited";
            snprintf(
                out,
                sizeof(out),
                "{\"id\":%lu,\"ok\":false,\"safety\":\"%s\",\"message\":\"%s\"}",
                (unsigned long)id,
                sname,
                d.reason);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        /* Hard cap: never block service longer than 1s per RPC (boot-loop mitigation) */
        if(dur > 1000) dur = 1000;
        int32_t pulses = 0;
        bool hw_ok = gl_hw_subghz_rx(freq, dur, &pulses);
        if(hw_ok) gl_safety_note_rx(&core->safety);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":%s,\"safety\":\"allow\",\"freq_hz\":%lu,\"duration_ms\":%lu,"
            "\"json_meta\":\"{\\\"pulses\\\":%ld}\"}",
            (unsigned long)id,
            hw_ok ? "true" : "false",
            (unsigned long)freq,
            (unsigned long)dur,
            (long)pulses);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "spectrum_scan")) {
        /**
         * DISABLED (v2.0.1): multi-band sequential SubGHz RX inside the agent
         * service stack caused USB drops and reboot loops in lab stress tests.
         * Prefer discrete short subghz_rx from the PC bridge (one band per RPC).
         * Re-enable only with async worker + hard wall-clock budget.
         */
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":false,\"safety\":\"deny\","
            "\"message\":\"spectrum_scan disabled (service radio multi-band unstable); use short subghz_rx\"}",
            (unsigned long)id);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "subghz_tx")) {
        if(!core) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"agent offline\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        char cid[24] = {0};
        char path[64] = {0};
        json_get_str(buf, "confirm_id", cid, sizeof(cid));
        json_get_str(buf, "file_path", path, sizeof(path));
        uint32_t freq = json_get_u32(buf, "freq_hz", 0);
        if(freq != 0 && !freq_in_subghz_window(freq)) {
            snprintf(
                out,
                sizeof(out),
                "{\"id\":%lu,\"ok\":false,\"safety\":\"deny\",\"message\":\"freq out of range\"}",
                (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        GlSafetyRequest sreq = {
            .actor = GlActorRpc,
            .action = "subghz_tx",
            .risk = GlRiskActiveTx,
            .freq_hz = freq,
            .gpio_pin = -1,
            .confirm_id = cid,
            .rationale = "rpc_tx",
        };
        GlSafetyDecision d = gl_safety_check(&core->safety, &sreq);
        if(d.result != GlSafetyAllow) {
            const char* sname = "deny";
            if(d.result == GlSafetyConfirmNeeded) sname = "confirm_needed";
            if(d.result == GlSafetyRateLimited) sname = "rate_limited";
            if(d.result == GlSafetyBlacklisted) sname = "blacklist";
            snprintf(
                out,
                sizeof(out),
                "{\"id\":%lu,\"ok\":false,\"safety\":\"%s\",\"message\":\"%s\"}",
                (unsigned long)id,
                sname,
                d.reason);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        bool ok = gl_hw_subghz_tx_file(path);
        if(ok) gl_safety_note_tx(&core->safety, GL_TX_MAX_MS);
        /* Honest v2 messaging: default path is file-ack without full encoder radio blast */
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":%s,\"safety\":\"allow\",\"tx_mode\":\"ack_file\","
            "\"message\":\"%s\"}",
            (unsigned long)id,
            ok ? "true" : "false",
            ok ? "tx ack (file ok; radio encoder gated)" : "tx failed");
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "ir_rx")) {
        if(!core) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"agent offline\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        uint32_t dur = clamp_rx_duration(json_get_u32(buf, "duration_ms", 1000));
        GlSafetyRequest sreq = {
            .actor = GlActorRpc,
            .action = "ir_rx",
            .risk = GlRiskPassiveRx,
            .freq_hz = 0,
            .gpio_pin = -1,
            .confirm_id = NULL,
            .rationale = "rpc",
        };
        if(gl_safety_check(&core->safety, &sreq).result != GlSafetyAllow) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"safety\":\"deny\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        bool ok = gl_hw_ir_rx(dur);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":%s,\"safety\":\"allow\",\"duration_ms\":%lu}",
            (unsigned long)id,
            ok ? "true" : "false",
            (unsigned long)dur);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "gpio_read")) {
        if(!core) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"agent offline\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        uint32_t pin = json_get_u32(buf, "pin", 0);
        uint8_t val = 0;
        bool ok = gl_hw_gpio_read(pin, &val);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":%s,\"pin\":%lu,\"value\":%u}",
            (unsigned long)id,
            ok ? "true" : "false",
            (unsigned long)pin,
            (unsigned)val);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "gpio_write")) {
        if(!core) {
            snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":false,\"error\":\"agent offline\"}", (unsigned long)id);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        uint32_t pin = json_get_u32(buf, "pin", 0);
        uint32_t value = json_get_u32(buf, "value", 0);
        char cid[24] = {0};
        json_get_str(buf, "confirm_id", cid, sizeof(cid));
        GlSafetyRequest sreq = {
            .actor = GlActorRpc,
            .action = "gpio_write",
            .risk = GlRiskGpioOut,
            .freq_hz = 0,
            .gpio_pin = (int32_t)pin,
            .confirm_id = cid,
            .rationale = "rpc_gpio",
        };
        GlSafetyDecision d = gl_safety_check(&core->safety, &sreq);
        if(d.result != GlSafetyAllow) {
            snprintf(
                out,
                sizeof(out),
                "{\"id\":%lu,\"ok\":false,\"safety\":\"%s\",\"message\":\"%s\"}",
                (unsigned long)id,
                d.result == GlSafetyConfirmNeeded ? "confirm_needed" : "deny",
                d.reason);
            *resp_len = write_str(resp, resp_cap, out);
            return true;
        }
        bool ok = gl_hw_gpio_write(pin, value ? 1 : 0);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":%s,\"safety\":\"allow\",\"pin\":%lu,\"value\":%u}",
            (unsigned long)id,
            ok ? "true" : "false",
            (unsigned long)pin,
            value ? 1u : 0u);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "skill_list")) {
        char list[480] = "[";
        if(core) {
            for(size_t i = 0; i < core->skills.count; i++) {
                char sid[GL_SKILL_ID_MAX];
                char sver[16];
                char item[120];
                sanitize_token(core->skills.items[i].id, sid, sizeof(sid));
                sanitize_token(core->skills.items[i].version, sver, sizeof(sver));
                snprintf(
                    item,
                    sizeof(item),
                    "%s{\"id\":\"%s\",\"version\":\"%s\",\"risk\":%d}",
                    i ? "," : "",
                    sid,
                    sver,
                    (int)core->skills.items[i].risk);
                if(strlen(list) + strlen(item) + 2 < sizeof(list)) strcat(list, item);
            }
        }
        strcat(list, "]");
        snprintf(out, sizeof(out), "{\"id\":%lu,\"ok\":true,\"skills\":%s}", (unsigned long)id, list);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    if(json_has_method(buf, "skill_reload")) {
        if(core) gl_skill_registry_reload(&core->skills);
        snprintf(
            out,
            sizeof(out),
            "{\"id\":%lu,\"ok\":true,\"skill_count\":%u}",
            (unsigned long)id,
            core ? (unsigned)core->skills.count : 0);
        *resp_len = write_str(resp, resp_cap, out);
        return true;
    }

    snprintf(
        out,
        sizeof(out),
        "{\"id\":%lu,\"ok\":false,\"error\":\"unknown method\"}",
        (unsigned long)id);
    *resp_len = write_str(resp, resp_cap, out);
    return true;
}
