/**
 * GrokAgent  -  persistent Momentum/Flipper service.
 * Also registers the `groklink` CLI command at startup.
 */
#include "grok_agent.h"

#include <furi.h>
#include <furi_hal.h>

#define TAG "GrokAgent"
#define GROK_AGENT_TICK_MS 1000

static GrokLinkCore s_core;
static GrokLinkCore* s_core_ptr = NULL;
static volatile bool s_run = false;

/* Implemented in grok_cli.c */
void groklink_cli_register(void);

GrokLinkCore* grok_agent_get_core(void) {
    return s_core_ptr;
}

bool grok_agent_is_running(void) {
    return s_run && s_core_ptr && s_core_ptr->running;
}

void grok_agent_request_stop(void) {
    s_run = false;
}

int32_t grok_agent_app(void* p) {
    UNUSED(p);

    if(!groklink_core_init(&s_core)) {
        FURI_LOG_E(TAG, "core init failed");
        return -1;
    }

    s_core_ptr = &s_core;
    s_run = true;
    groklink_cli_register();
    FURI_LOG_I(TAG, "GrokLink agent %s started mode=%s", GROKLINK_VERSION_STRING, s_core.safety_mode);

    while(s_run) {
        groklink_core_tick(&s_core);
        furi_delay_ms(GROK_AGENT_TICK_MS);
    }

    groklink_core_deinit(&s_core);
    s_core_ptr = NULL;
    FURI_LOG_I(TAG, "stopped");
    return 0;
}
