#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include "gl_config.h"
#include "gl_safety.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char id[GL_SKILL_ID_MAX];
    char version[16];
    char description[64];
    GlRiskClass risk;
    bool has_fap;
    bool enabled;
} GlSkillInfo;

typedef struct {
    GlSkillInfo items[GL_MAX_SKILLS];
    size_t count;
} GlSkillRegistry;

bool gl_skill_registry_init(GlSkillRegistry* reg);
bool gl_skill_registry_reload(GlSkillRegistry* reg);
const GlSkillInfo* gl_skill_find(const GlSkillRegistry* reg, const char* id);
bool gl_skill_run(const GlSkillRegistry* reg, const char* id, GlSafetyState* safety);

#ifdef __cplusplus
}
#endif
