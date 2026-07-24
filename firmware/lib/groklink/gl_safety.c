/**
 * GrokLink safety implementation  -  compact, fail-closed for TX.
 *
 * NOTE: In full firmware, replace file I/O stubs with storage API
 * (storage_file_open / Flipper storage service). This unit is written
 * to be readable and portable for review; integrate with Furi storage.
 */
#include "gl_safety.h"
#include "gl_audit.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Weak time hooks  -  override in firmware with furi_get_tick / RTC */
__attribute__((weak)) uint32_t gl_now_unix(void) {
    return 0;
}
__attribute__((weak)) uint32_t gl_now_ms(void) {
    return 0;
}

static bool gl_physical_ok = false;

bool gl_safety_physical_confirm_pending(void) {
    return !gl_physical_ok;
}

void gl_safety_physical_confirm_set(bool ok) {
    gl_physical_ok = ok;
}

static void set_decision(GlSafetyDecision* d, GlSafetyResult r, const char* why) {
    d->result = r;
    if(why) {
        strncpy(d->reason, why, sizeof(d->reason) - 1);
        d->reason[sizeof(d->reason) - 1] = '\0';
    } else {
        d->reason[0] = '\0';
    }
}

static bool freq_banned(const GlSafetyState* st, uint32_t freq_hz) {
    if(freq_hz == 0) return false;
    for(size_t i = 0; i < st->banned_freq_count; i++) {
        /* Match within 100 kHz of listed center */
        uint32_t b = st->banned_freq_hz[i];
        if(freq_hz >= b - 100000 && freq_hz <= b + 100000) return true;
    }
    return false;
}

static bool gpio_banned(const GlSafetyState* st, int32_t pin) {
    if(pin < 0) return false;
    for(size_t i = 0; i < st->banned_gpio_count; i++) {
        if(st->banned_gpio[i] == pin) return true;
    }
    return false;
}

static bool confirm_valid(GlSafetyState* st, const char* action, const char* confirm_id) {
    if(!confirm_id || !confirm_id[0]) return false;
    uint32_t now = gl_now_unix();
    for(size_t i = 0; i < GL_MAX_CONFIRM_SLOTS; i++) {
        GlConfirmSlot* s = &st->confirms[i];
        if(s->used) continue;
        if(strncmp(s->id, confirm_id, sizeof(s->id)) != 0) continue;
        if(strncmp(s->action, action, sizeof(s->action)) != 0) continue;
        if(now > s->expires_unix) return false;
        s->used = true; /* single use */
        return true;
    }
    return false;
}

bool gl_safety_init(GlSafetyState* st) {
    if(!st) return false;
    memset(st, 0, sizeof(*st));
    st->fail_closed_tx = true;
    st->require_edu_ack = true;
    st->tx_max_ms = GL_TX_MAX_MS;
    st->tx_cooldown_ms = GL_TX_COOLDOWN_MS;
    st->rx_cooldown_ms = GL_RX_COOLDOWN_MS;
    st->last_rx_unix_ms = 0;
    st->loaded = true;
    /* Default lab blacklist examples  -  reloaded from SD when available */
    st->banned_freq_hz[0] = 0; /* none until SD load */
    st->banned_freq_count = 0;
    gl_safety_reload_blacklist(st);
    gl_audit_line("agent", "safety_init", "allow", "safety state ready");
    return true;
}

#if !defined(GROKLINK_USE_FURI)
bool gl_safety_reload_blacklist(GlSafetyState* st) {
    if(!st) return false;
    st->banned_freq_count = 0;
    st->banned_gpio_count = 0;
    return true;
}
#endif
/* Furi: gl_safety_reload_blacklist in gl_blacklist.c */

void gl_safety_deinit(GlSafetyState* st) {
    if(st) memset(st, 0, sizeof(*st));
}

bool gl_safety_issue_confirm(
    GlSafetyState* st,
    const char* action,
    uint32_t ttl_sec,
    char* out_id,
    size_t out_len) {
    if(!st || !action || !out_id || out_len < 12) return false;
    if(ttl_sec == 0) ttl_sec = GL_CONFIRM_DEFAULT_TTL_SEC;
    if(ttl_sec > 300) ttl_sec = 300;

    int slot = -1;
    for(size_t i = 0; i < GL_MAX_CONFIRM_SLOTS; i++) {
        if(st->confirms[i].used || st->confirms[i].id[0] == '\0' ||
           gl_now_unix() > st->confirms[i].expires_unix) {
            slot = (int)i;
            break;
        }
    }
    if(slot < 0) return false;

    GlConfirmSlot* s = &st->confirms[slot];
    memset(s, 0, sizeof(*s));
    /* Not crypto-secure; sufficient for local USB session tokens */
    snprintf(s->id, sizeof(s->id), "c%08lx", (unsigned long)(gl_now_ms() ^ (uint32_t)slot * 2654435761u));
    strncpy(s->action, action, sizeof(s->action) - 1);
    s->expires_unix = gl_now_unix() + ttl_sec;
    s->used = false;
    strncpy(out_id, s->id, out_len - 1);
    out_id[out_len - 1] = '\0';
    gl_audit_line("rpc", "confirm_issue", "allow", action);
    return true;
}

void gl_safety_note_tx(GlSafetyState* st, uint32_t duration_ms) {
    if(!st) return;
    (void)duration_ms;
    st->last_tx_unix_ms = gl_now_ms();
}

void gl_safety_note_rx(GlSafetyState* st) {
    if(!st) return;
    st->last_rx_unix_ms = gl_now_ms();
}

GlSafetyDecision gl_safety_check(GlSafetyState* st, const GlSafetyRequest* req) {
    GlSafetyDecision d;
    set_decision(&d, GlSafetyDeny, "null");
    if(!st || !req || !req->action) {
        set_decision(&d, GlSafetyDeny, "invalid request");
        return d;
    }
    if(!st->loaded) {
        set_decision(&d, GlSafetyDegraded, "safety not loaded");
        gl_audit_line("agent", req->action, "deny", d.reason);
        return d;
    }

    /* INFO always allowed */
    if(req->risk == GlRiskInfo) {
        set_decision(&d, GlSafetyAllow, "info");
        return d;
    }

    if(freq_banned(st, req->freq_hz)) {
        set_decision(&d, GlSafetyBlacklisted, "frequency blacklisted");
        gl_audit_line("agent", req->action, "blacklist", d.reason);
        return d;
    }
    if(gpio_banned(st, req->gpio_pin)) {
        set_decision(&d, GlSafetyBlacklisted, "gpio blacklisted");
        gl_audit_line("agent", req->action, "blacklist", d.reason);
        return d;
    }

    if(req->risk == GlRiskPassiveRx) {
        /* Space radio work in service context (matrix tests caused reboot loops) */
        uint32_t now = gl_now_ms();
        if(st->last_rx_unix_ms && st->rx_cooldown_ms &&
           (now - st->last_rx_unix_ms) < st->rx_cooldown_ms) {
            set_decision(&d, GlSafetyRateLimited, "rx cooldown");
            gl_audit_line("agent", req->action, "rate_limit", d.reason);
            return d;
        }
        set_decision(&d, GlSafetyAllow, "passive_rx");
        gl_audit_line("agent", req->action, "allow", "passive_rx");
        return d;
    }

    if(req->risk == GlRiskSystem) {
        if(!gl_physical_ok) {
            set_decision(&d, GlSafetyConfirmNeeded, "physical confirm required");
            gl_audit_line("agent", req->action, "confirm_needed", d.reason);
            return d;
        }
        set_decision(&d, GlSafetyAllow, "system with physical confirm");
        gl_physical_ok = false; /* one-shot */
        gl_audit_line("agent", req->action, "allow", "system");
        return d;
    }

    /* ACTIVE_TX / GPIO / CONTACT */
    if(st->fail_closed_tx) {
        uint32_t now = gl_now_ms();
        if(st->last_tx_unix_ms && (now - st->last_tx_unix_ms) < st->tx_cooldown_ms) {
            set_decision(&d, GlSafetyRateLimited, "tx cooldown");
            gl_audit_line("agent", req->action, "rate_limit", d.reason);
            return d;
        }
        if(!confirm_valid(st, req->action, req->confirm_id)) {
            set_decision(&d, GlSafetyConfirmNeeded, "confirm token required");
            gl_audit_line("agent", req->action, "confirm_needed", req->action);
            return d;
        }
    }

    set_decision(&d, GlSafetyAllow, "elevated allow");
    gl_audit_line("agent", req->action, "allow", req->rationale ? req->rationale : "");
    return d;
}
