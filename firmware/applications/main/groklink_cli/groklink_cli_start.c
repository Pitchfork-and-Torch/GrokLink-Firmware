/**
 * Startup registration for Flipper CLI.
 * application.fam entry_point -> groklink_cli_on_system_start
 */
void groklink_cli_cmd(void* cli, char* args, void* context);

void groklink_cli_on_system_start(void) {
    /**
     * Device:
     *   Cli* cli = furi_record_open(RECORD_CLI);
     *   cli_add_command(cli, "groklink", CliCommandFlagParallelSafe, groklink_cli_cmd, NULL);
     *   furi_record_close(RECORD_CLI);
     */
    (void)groklink_cli_cmd;
}
