/**
 * GrokLink  -  compile-time and path configuration
 * Keep RAM/Flash budgets explicit for STM32WB55 feasibility.
 */
#pragma once

#define GROKLINK_VERSION_MAJOR 2
#define GROKLINK_VERSION_MINOR 1
#define GROKLINK_VERSION_PATCH 3
#define GROKLINK_VERSION_STRING "2.1.3"

/** JSON RPC API generation (independent of firmware patch) */
#define GROKLINK_RPC_API 2

#define GL_SD_ROOT "/ext/groklink"
#define GL_PATH_CONFIG GL_SD_ROOT "/config/agent.json"
#define GL_PATH_MISSIONS GL_SD_ROOT "/missions"
#define GL_PATH_SKILLS GL_SD_ROOT "/skills"
#define GL_PATH_LOGS GL_SD_ROOT "/logs"
#define GL_PATH_BLACKLIST GL_SD_ROOT "/blacklist"
#define GL_PATH_AUDIT GL_PATH_LOGS "/audit.jsonl"
#define GL_PATH_AGENT_LOG GL_PATH_LOGS "/agent.jsonl"

/** Education acknowledgement required for elevated PC sessions */
#define GL_EDU_ACK_PHRASE "I_WILL_USE_ONLY_AUTHORIZED_TARGETS"

/** Resource budgets */
#define GL_MAX_MISSIONS 16
#define GL_MAX_SKILLS 24
#define GL_MAX_MISSION_STEPS 32
#define GL_MAX_CONFIRM_SLOTS 4
#define GL_CONFIRM_DEFAULT_TTL_SEC 60
#define GL_TX_MAX_MS 2000
#define GL_TX_COOLDOWN_MS 5000
/** Min gap between SubGHz RX RPCs in agent service (boot-loop mitigation) */
#define GL_RX_COOLDOWN_MS 1500
#define GL_AGENT_STACK 8192
#define GL_MISSION_BUF 1024
#define GL_AUDIT_LINE_MAX 384
#define GL_SKILL_ID_MAX 32
#define GL_MISSION_ID_MAX 32

/**
 * SubGHz policy window (CC1101-class). Outside -> RPC deny before HAL.
 * Matches typical Flipper SubGHz usable range with margin.
 */
#define GL_SUBGHZ_FREQ_MIN_HZ 281000000u
#define GL_SUBGHZ_FREQ_MAX_HZ 928000000u
#define GL_RX_DURATION_DEFAULT_MS 1000u
#define GL_RX_DURATION_MAX_MS 5000u
#define GL_SPECTRUM_MAX_BANDS 12

/** Feature flags */
#define GL_FEATURE_STREAM 1
#define GL_FEATURE_AUTONOMY 1
#define GL_FEATURE_SKILL_FAP 1
#define GL_FEATURE_ML_STUB 1
#define GL_FEATURE_SPECTRUM 1
#define GL_FEATURE_IR_RPC 1
#define GL_FEATURE_GPIO_RPC 1
