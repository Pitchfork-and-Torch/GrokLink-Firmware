#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include "gl_config.h"
#include "gl_safety.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    GlMissionIdle = 0,
    GlMissionArmed,
    GlMissionRunning,
    GlMissionError,
    GlMissionDone,
} GlMissionState;

typedef enum {
    GlOpDelay = 0,
    GlOpLog,
    GlOpSubGhzRx,
    GlOpSubGhzTxFile,
    GlOpIrRx,
    GlOpIrTxFile,
    GlOpNfcRead,
    GlOpGpioRead,
    GlOpGpioWrite,
    GlOpSkillRun,
    GlOpDecision,
    GlOpUnknown = 255,
} GlOpType;

typedef struct {
    GlOpType type;
    uint32_t duration_ms;
    uint32_t freq_hz;
    int32_t gpio_pin;
    uint8_t gpio_value;
    char path[64];
    char message[64];
    char skill_id[GL_SKILL_ID_MAX];
    /* decision */
    char metric[24];
    int32_t threshold;
    uint8_t cmp; /* 0:gte 1:lte 2:eq */
} GlMissionStep;

typedef struct {
    char id[GL_MISSION_ID_MAX];
    char name[48];
    bool autonomous;
    bool require_confirm;
    GlRiskClass max_risk;
    uint32_t every_sec;
    GlMissionState state;
    uint8_t step_count;
    uint8_t step_index;
    GlMissionStep steps[GL_MAX_MISSION_STEPS];
    uint32_t last_run_unix;
    int32_t last_metric_value; /* simple decision context */
    char error[48];
} GlMission;

typedef struct {
    GlMission items[GL_MAX_MISSIONS];
    size_t count;
    int active_index; /* -1 none */
} GlMissionBank;

bool gl_mission_bank_init(GlMissionBank* bank);
bool gl_mission_load_dir(GlMissionBank* bank); /* SD missions */
GlMission* gl_mission_find(GlMissionBank* bank, const char* id);

/**
 * Start mission by id. confirm_id required if max_risk elevated.
 * Returns false if safety denies.
 */
bool gl_mission_start(
    GlMissionBank* bank,
    GlSafetyState* safety,
    const char* id,
    const char* confirm_id);

void gl_mission_stop(GlMissionBank* bank, const char* id);

/** Call from agent 1 Hz (or faster) tick. */
void gl_mission_tick(GlMissionBank* bank, GlSafetyState* safety);

/** Parse one mission JSON file into out (minimal hand parser / hooks). */
bool gl_mission_parse_json(const char* json, size_t len, GlMission* out);

#ifdef __cplusplus
}
#endif
