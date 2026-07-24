#pragma once

#include "gl_config.h"
#include "gl_safety.h"
#include "gl_audit.h"
#include "gl_mission.h"
#include "gl_skill.h"
#include "gl_hw.h"
#include "gl_features.h"
#include "gl_radio.h"
#include "gl_stream.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    GlSafetyState safety;
    GlMissionBank missions;
    GlSkillRegistry skills;
    bool running;
    bool sd_ok;
    char safety_mode[16]; /* "strict" | "lab" | "degraded" */
} GrokLinkCore;

bool groklink_core_init(GrokLinkCore* core);
void groklink_core_deinit(GrokLinkCore* core);
void groklink_core_tick(GrokLinkCore* core);

#ifdef __cplusplus
}
#endif
