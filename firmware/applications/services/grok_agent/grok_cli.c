/**
 * CLI: groklink status|mission|skill|confirm|rpc
 * Registered at startup via cli_registry_add_command (in-firmware, not .fal).
 *
 * Machine RPC: groklink rpc <json>
 * Response: GROKRPC:{...}
 */
#include "grok_agent.h"
#include "grok_rpc.h"

#include <furi.h>
#include <toolbox/cli/cli_command.h>
#include <toolbox/cli/cli_registry.h>
#include <toolbox/args.h>
#include <toolbox/pipe.h>
#include <cli/cli.h>

#include <stdio.h>
#include <string.h>

#define TAG "GrokCli"

static GrokRpcSession s_rpc_session;
static bool s_rpc_inited = false;

static void ensure_rpc(void) {
    if(!s_rpc_inited) {
        grok_rpc_session_init(&s_rpc_session);
        s_rpc_inited = true;
    }
}

static void print_usage(void) {
    printf("Usage: groklink <cmd>\r\n");
    printf("  status\r\n");
    printf("  mission list|start <id>\r\n");
    printf("  skill list|reload\r\n");
    printf("  confirm physical\r\n");
    printf("  rpc <json>\r\n");
    printf("Safety: authorized research only. TX needs confirm.\r\n");
}

static void cmd_status(void) {
    GrokLinkCore* core = grok_agent_get_core();
    printf(
        "GrokLink %s | agent=%s | mode=%s | skills=%u | missions=%u | audit=%08lx\r\n",
        GROKLINK_VERSION_STRING,
        grok_agent_is_running() ? "up" : "down",
        core ? core->safety_mode : "n/a",
        core ? (unsigned)core->skills.count : 0,
        core ? (unsigned)core->missions.count : 0,
        (unsigned long)gl_audit_last_hash());
}

static void cmd_rpc(FuriString* args) {
    ensure_rpc();
    const char* json = furi_string_get_cstr(args);
    while(*json == ' ') json++;

    uint8_t resp[700];
    size_t resp_len = 0;
    if(!grok_rpc_handle(
           &s_rpc_session,
           (const uint8_t*)json,
           strlen(json),
           resp,
           sizeof(resp),
           &resp_len)) {
        printf("GROKRPC:{\"ok\":false,\"error\":\"handler failed\"}\r\n");
        return;
    }
    printf("GROKRPC:%s\r\n", (const char*)resp);
}

static void groklink_cli_execute(PipeSide* pipe, FuriString* args, void* context) {
    UNUSED(pipe);
    UNUSED(context);

    FuriString* cmd = furi_string_alloc();
    if(!args_read_string_and_trim(args, cmd)) {
        print_usage();
        furi_string_free(cmd);
        return;
    }

    if(furi_string_cmp_str(cmd, "status") == 0) {
        cmd_status();
    } else if(furi_string_cmp_str(cmd, "rpc") == 0) {
        cmd_rpc(args);
    } else if(furi_string_cmp_str(cmd, "mission") == 0) {
        FuriString* sub = furi_string_alloc();
        if(!args_read_string_and_trim(args, sub)) {
            printf("mission list|start <id>\r\n");
        } else if(furi_string_cmp_str(sub, "list") == 0) {
            GrokLinkCore* core = grok_agent_get_core();
            if(!core) {
                printf("agent offline\r\n");
            } else if(core->missions.count == 0) {
                printf("(no missions)\r\n");
            } else {
                for(size_t i = 0; i < core->missions.count; i++) {
                    printf(
                        " - %s auto=%d\r\n",
                        core->missions.items[i].id,
                        core->missions.items[i].autonomous ? 1 : 0);
                }
            }
        } else if(furi_string_cmp_str(sub, "start") == 0) {
            FuriString* mid = furi_string_alloc();
            if(args_read_string_and_trim(args, mid)) {
                GrokLinkCore* core = grok_agent_get_core();
                bool ok = core &&
                          gl_mission_start(
                              &core->missions, &core->safety, furi_string_get_cstr(mid), NULL);
                printf("%s\r\n", ok ? "started" : "failed");
            }
            furi_string_free(mid);
        }
        furi_string_free(sub);
    } else if(furi_string_cmp_str(cmd, "skill") == 0) {
        FuriString* sub = furi_string_alloc();
        if(!args_read_string_and_trim(args, sub)) {
            printf("skill list|reload\r\n");
        } else if(furi_string_cmp_str(sub, "list") == 0) {
            GrokLinkCore* core = grok_agent_get_core();
            if(!core) {
                printf("agent offline\r\n");
            } else {
                for(size_t i = 0; i < core->skills.count; i++) {
                    printf(
                        " - %s v%s risk=%d\r\n",
                        core->skills.items[i].id,
                        core->skills.items[i].version,
                        (int)core->skills.items[i].risk);
                }
            }
        } else if(furi_string_cmp_str(sub, "reload") == 0) {
            GrokLinkCore* core = grok_agent_get_core();
            if(core) gl_skill_registry_reload(&core->skills);
            printf("reloaded\r\n");
        }
        furi_string_free(sub);
    } else if(furi_string_cmp_str(cmd, "confirm") == 0) {
        FuriString* sub = furi_string_alloc();
        if(args_read_string_and_trim(args, sub) && furi_string_cmp_str(sub, "physical") == 0) {
            gl_safety_physical_confirm_set(true);
            printf("physical confirm armed (one-shot SYSTEM)\r\n");
        } else {
            printf("confirm physical\r\n");
        }
        furi_string_free(sub);
    } else {
        print_usage();
    }

    furi_string_free(cmd);
}

void groklink_cli_register(void) {
#ifdef SRV_CLI
    CliRegistry* registry = furi_record_open(RECORD_CLI);
    cli_registry_add_command(
        registry,
        "groklink",
        CliCommandFlagParallelSafe | CliCommandFlagUseShellThread,
        groklink_cli_execute,
        NULL);
    furi_record_close(RECORD_CLI);
    FURI_LOG_I(TAG, "CLI command registered");
#else
    FURI_LOG_W(TAG, "CLI not available (SRV_CLI undefined)");
#endif
}

/* Optional STARTUP entry if app is also listed as STARTUP */
void groklink_cli_on_system_start(void) {
    groklink_cli_register();
}
