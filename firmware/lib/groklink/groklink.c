#include "groklink.h"

#include <string.h>

bool groklink_core_init(GrokLinkCore* core) {
    if(!core) return false;
    memset(core, 0, sizeof(*core));
    strncpy(core->safety_mode, "strict", sizeof(core->safety_mode) - 1);

    if(!gl_audit_init()) return false;
    if(!gl_safety_init(&core->safety)) return false;
    gl_radio_init();
    if(!gl_hw_init()) return false;
    gl_mission_bank_init(&core->missions);
    gl_skill_registry_init(&core->skills);

    core->sd_ok = gl_mission_load_dir(&core->missions);
    if(!core->sd_ok) {
        strncpy(core->safety_mode, "degraded", sizeof(core->safety_mode) - 1);
    }
    core->running = true;
    gl_audit_line("agent", "core_init", "allow", GROKLINK_VERSION_STRING);
    return true;
}

void groklink_core_deinit(GrokLinkCore* core) {
    if(!core) return;
    gl_hw_release_all();
    gl_radio_deinit();
    gl_safety_deinit(&core->safety);
    gl_audit_deinit();
    core->running = false;
}

void groklink_core_tick(GrokLinkCore* core) {
    if(!core || !core->running) return;
    gl_mission_tick(&core->missions, &core->safety);
}
