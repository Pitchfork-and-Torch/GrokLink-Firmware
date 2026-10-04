#pragma once

#include <stdbool.h>
#include "groklink.h"

#ifdef __cplusplus
extern "C" {
#endif

GrokLinkCore* grok_agent_get_core(void);
int32_t grok_agent_app(void* p);
bool grok_agent_is_running(void);
void grok_agent_request_stop(void);

#ifdef __cplusplus
}
#endif
