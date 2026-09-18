/**
 * CLI: groklink status | mission list | skill list | confirm
 *
 * Flipper integration:
 *   #include <cli/cli.h>
 *   void groklink_cli_init(void) {
 *     Cli* cli = furi_record_open(RECORD_CLI);
 *     cli_add_command(cli, "groklink", CliCommandFlagParallelSafe, groklink_cli_cmd, NULL);
 *     furi_record_close(RECORD_CLI);
 *   }
 */
#include "grok_agent.h"
#include "groklink.h"

#include <stdio.h>
#include <string.h>

/* Host-friendly printer; on device use cli_write / printf via Cli */
static void gl_print(const char* s) {
    fputs(s, stdout);
}

void groklink_cli_cmd(void* cli, char* args, void* context) {
    (void)cli;
    (void)context;
    if(!args) args = "";

    while(*args == ' ') args++;

    GrokLinkCore* core = grok_agent_get_core();

    if(strncmp(args, "status", 6) == 0) {
        char line[256];
        snprintf(
            line,
            sizeof(line),
            "GrokLink %s | agent=%s | mode=%s | skills=%u | missions=%u | audit=%08lx\r\n",
            GROKLINK_VERSION_STRING,
            grok_agent_is_running() ? "up" : "down",
            core ? core->safety_mode : "n/a",
            core ? (unsigned)core->skills.count : 0,
            core ? (unsigned)core->missions.count : 0,
            (unsigned long)gl_audit_last_hash());
        gl_print(line);
        gl_print("SAFETY: authorized research only. TX requires confirm.\r\n");
        return;
    }

    if(strncmp(args, "mission list", 12) == 0) {
        if(!core) {
            gl_print("agent offline\r\n");
            return;
        }
        for(size_t i = 0; i < core->missions.count; i++) {
            char line[96];
            snprintf(
                line,
                sizeof(line),
                " - %s (%s) auto=%d\r\n",
                core->missions.items[i].id,
                core->missions.items[i].name,
                core->missions.items[i].autonomous ? 1 : 0);
            gl_print(line);
        }
        if(core->missions.count == 0) gl_print("(no missions on SD)\r\n");
        return;
    }

    if(strncmp(args, "skill list", 10) == 0) {
        if(!core) {
            gl_print("agent offline\r\n");
            return;
        }
        for(size_t i = 0; i < core->skills.count; i++) {
            char line[96];
            snprintf(
                line,
                sizeof(line),
                " - %s v%s risk=%d\r\n",
                core->skills.items[i].id,
                core->skills.items[i].version,
                (int)core->skills.items[i].risk);
            gl_print(line);
        }
        return;
    }

    if(strncmp(args, "confirm physical", 16) == 0) {
        gl_safety_physical_confirm_set(true);
        gl_print("physical confirm armed (one-shot SYSTEM)\r\n");
        return;
    }

    gl_print("Usage: groklink status|mission list|skill list|confirm physical\r\n");
}
