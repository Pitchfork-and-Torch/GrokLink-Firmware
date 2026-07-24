/**
 * GrokLink safety interlocks  -  ALL actuator paths must call gl_safety_check().
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include "gl_config.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    GlRiskInfo = 0,
    GlRiskPassiveRx = 1,
    GlRiskActiveTx = 2,
    GlRiskGpioOut = 3,
    GlRiskContact = 4,
    GlRiskSystem = 5,
} GlRiskClass;

typedef enum {
    GlSafetyAllow = 0,
    GlSafetyDeny = 1,
    GlSafetyConfirmNeeded = 2,
    GlSafetyRateLimited = 3,
    GlSafetyBlacklisted = 4,
    GlSafetyDegraded = 5,
} GlSafetyResult;

typedef enum {
    GlActorRpc = 0,
    GlActorAgent = 1,
    GlActorCli = 2,
    GlActorUi = 3,
} GlActor;

typedef struct {
    GlActor actor;
    const char* action; /* e.g. "subghz_tx" */
    GlRiskClass risk;
    uint32_t freq_hz; /* 0 if N/A */
    int32_t gpio_pin; /* -1 if N/A */
    const char* protocol; /* optional */
    const char* confirm_id; /* optional */
    const char* rationale;
} GlSafetyRequest;

typedef struct {
    GlSafetyResult result;
    char reason[96];
} GlSafetyDecision;

typedef struct {
    char id[24];
    char action[32];
    uint32_t expires_unix;
    bool used;
} GlConfirmSlot;

typedef struct {
    bool loaded;
    bool fail_closed_tx;
    bool require_edu_ack;
    uint32_t tx_max_ms;
    uint32_t tx_cooldown_ms;
    uint32_t last_tx_unix_ms;
    uint32_t rx_cooldown_ms;
    uint32_t last_rx_unix_ms;
    GlConfirmSlot confirms[GL_MAX_CONFIRM_SLOTS];
    /* simplified blacklist: up to N forbidden MHz centers */
    uint32_t banned_freq_hz[32];
    size_t banned_freq_count;
    int32_t banned_gpio[16];
    size_t banned_gpio_count;
} GlSafetyState;

bool gl_safety_init(GlSafetyState* st);
bool gl_safety_reload_blacklist(GlSafetyState* st);
void gl_safety_deinit(GlSafetyState* st);

GlSafetyDecision gl_safety_check(GlSafetyState* st, const GlSafetyRequest* req);

/** Issue short-lived confirm token (RPC/CLI). */
bool gl_safety_issue_confirm(
    GlSafetyState* st,
    const char* action,
    uint32_t ttl_sec,
    char* out_id,
    size_t out_len);

/** SYSTEM actions that require physical on-device confirmation. */
bool gl_safety_physical_confirm_pending(void);
void gl_safety_physical_confirm_set(bool ok);

/** Call after successful TX for duty-cycle tracking. */
void gl_safety_note_tx(GlSafetyState* st, uint32_t duration_ms);

/** Call after successful passive RX for radio spacing. */
void gl_safety_note_rx(GlSafetyState* st);

#ifdef __cplusplus
}
#endif
