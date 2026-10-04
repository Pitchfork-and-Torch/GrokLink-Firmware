# Complete repository structure

```
GrokLink-Firmware/
  README.md
  LICENSE
  SECURITY.md
  CHANGELOG.md
  REPO_STRUCTURE.md
  .gitignore
  docs/
    ARCHITECTURE.md
    SAFETY.md
    BUILD_FLASH.md
    GROKRPC.md
    MISSIONS.md
    EXTENSIBILITY_ML.md
    FIRST_DEPLOYMENT_REPORT.md
    EXPLORE_NOTES.md
    INTEGRATION_STATUS.md
  schemas/
    groklink.proto
  firmware/
    lib/groklink/
      gl_config.h
      gl_safety.h / gl_safety.c
      gl_audit.h / gl_audit.c
      gl_mission.h / gl_mission.c
      gl_skill.h / gl_skill.c
      gl_hw.h / gl_hw.c
      gl_features.h / gl_features.c
      gl_storage_furi.c
      groklink.h / groklink.c
      SConscript
    applications/services/grok_agent/
      grok_agent.h / grok_agent.c
      grok_cli.c
      grok_rpc.c / grok_rpc.h
      application.fam
    applications/system/grok_rpc/
    applications/main/groklink_cli/
    applications_user/
  sd_card/groklink/
    config/
    blacklist/
    missions/
    skills/
    logs/
  bridge/
    groklink/
      cli.py
      safety.py
      rpc/
      skills/
    tests/
    pyproject.toml
  skills/
    TRACKING.md
    templates/
    examples/
  tools/
    apply_overlay.ps1
    apply_overlay.sh
    ascii_sanitize.py
  examples/
  assets/
    logo.jpg
    banner.jpg
    groklink-what-it-does.jpg
```
