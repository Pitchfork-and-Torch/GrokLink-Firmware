#include "gl_skill.h"
#include "gl_audit.h"
#include "gl_hw.h"

#include <string.h>

bool gl_skill_registry_init(GlSkillRegistry* reg) {
    if(!reg) return false;
    memset(reg, 0, sizeof(*reg));
    return gl_skill_registry_reload(reg);
}

/* gl_skill_registry_reload implemented in gl_skill_load.c */

const GlSkillInfo* gl_skill_find(const GlSkillRegistry* reg, const char* id) {
    if(!reg || !id) return NULL;
    for(size_t i = 0; i < reg->count; i++) {
        if(strncmp(reg->items[i].id, id, GL_SKILL_ID_MAX) == 0) return &reg->items[i];
    }
    return NULL;
}

bool gl_skill_run(const GlSkillRegistry* reg, const char* id, GlSafetyState* safety) {
    const GlSkillInfo* s = gl_skill_find(reg, id);
    if(!s || !s->enabled) return false;
    GlSafetyRequest req = {
        .actor = GlActorAgent,
        .action = "skill_run",
        .risk = s->risk,
        .freq_hz = 0,
        .gpio_pin = -1,
        .confirm_id = NULL,
        .rationale = id,
    };
    if(gl_safety_check(safety, &req).result != GlSafetyAllow) return false;
    return gl_hw_skill_run(id);
}
