/**
 * Hardware facade  -  host stubs + full Furi HAL when GROKLINK_USE_FURI.
 */
#include "gl_hw.h"
#include "gl_audit.h"
#include "gl_config.h"
#include "gl_radio.h"
#include "gl_stream.h"

#include <stdio.h>
#include <string.h>

#if defined(GROKLINK_USE_FURI)

#include <furi.h>
#include <furi_hal.h>
#include <furi_hal_subghz.h>
#include <furi_hal_resources.h>
#include <storage/storage.h>
#include <flipper_format/flipper_format.h>
#include <lib/subghz/devices/cc1101_configs.h>
#include <infrared/worker/infrared_worker.h>
#include <infrared/encoder_decoder/infrared.h>

/* -- SubGHz async pulse counter ------------------------------------------- */

typedef struct {
    volatile int32_t pulses;
    volatile bool done;
} GlSubGhzRxCtx;

static void gl_subghz_capture_cb(bool level, uint32_t duration, void* context) {
    UNUSED(level);
    UNUSED(duration);
    GlSubGhzRxCtx* ctx = context;
    if(ctx) ctx->pulses++;
}

#if defined(GROKLINK_RX_SD_META)
static bool gl_path_ensure_parent(Storage* storage, const char* path) {
    /* Best-effort: ensure /ext/groklink/logs/captures exists when saving */
    storage_common_mkdir(storage, GL_SD_ROOT);
    storage_common_mkdir(storage, GL_PATH_LOGS);
    storage_common_mkdir(storage, GL_PATH_LOGS "/captures");
    UNUSED(path);
    return true;
}
#endif

bool gl_hw_init(void) {
    gl_audit_line("hw", "init", "allow", "furi");
    return true;
}

void gl_hw_release_all(void) {
    /* Best-effort idle; avoid hard-fault if async was never started */
    gl_radio_force_safe();
    gl_audit_line("hw", "release_all", "allow", "furi");
}

bool gl_hw_subghz_rx(uint32_t freq_hz, uint32_t duration_ms, int32_t* out_pulse_count) {
    if(out_pulse_count) *out_pulse_count = 0;
    if(!gl_radio_can_start()) {
        gl_audit_line("hw", "subghz_rx", "deny", "breaker_open");
        return false;
    }
    if(!furi_hal_subghz_is_frequency_valid(freq_hz)) {
        gl_audit_line("hw", "subghz_rx", "deny", "invalid freq");
        return false;
    }
    if(!gl_radio_lock(500)) {
        gl_audit_line("hw", "subghz_rx", "deny", "radio_busy");
        return false;
    }

    /* Hard wall-clock cap inside HAL path */
    if(duration_ms == 0 || duration_ms > 1000) duration_ms = 1000;

    GlSubGhzRxCtx ctx = {.pulses = 0, .done = false};

    furi_hal_subghz_reset();
    furi_hal_subghz_idle();
    furi_hal_subghz_load_custom_preset(subghz_device_cc1101_preset_ook_650khz_async_regs);
    uint32_t real = furi_hal_subghz_set_frequency_and_path(freq_hz);
    UNUSED(real);

    furi_hal_subghz_start_async_rx(gl_subghz_capture_cb, &ctx);
    furi_hal_subghz_rx();

    uint32_t start = furi_get_tick();
    while((furi_get_tick() - start) < duration_ms) {
        furi_delay_ms(10);
    }

    furi_hal_subghz_stop_async_rx();
    furi_hal_subghz_idle();
    furi_hal_subghz_sleep();
    gl_radio_unlock();
    gl_radio_note_ok();

    if(out_pulse_count) *out_pulse_count = ctx.pulses;

    char detail[80];
    snprintf(
        detail,
        sizeof(detail),
        "f=%lu d=%lu p=%ld",
        (unsigned long)freq_hz,
        (unsigned long)duration_ms,
        (long)ctx.pulses);
    gl_audit_line("hw", "subghz_rx", "allow", detail);
    {
        char body[96];
        snprintf(
            body,
            sizeof(body),
            "\"freq_hz\":%lu,\"pulses\":%ld",
            (unsigned long)freq_hz,
            (long)ctx.pulses);
        gl_stream_event("subghz_rx_done", body);
    }
    return true;
}

bool gl_hw_subghz_tx_file(const char* path) {
    /**
     * TX stages:
     *  1) path non-empty
     *  2) radio breaker closed
     *  3) file exists on storage
     *  4) radio lock
     *  5) if GROKLINK_SUBGHZ_TX_FULL: encoder worker (not default)
     *  6) else: ack_file (confirm gates already passed in RPC)
     */
    if(!path || !path[0]) return false;
    if(gl_radio_breaker_open()) {
        gl_audit_line("hw", "subghz_tx_file", "deny", "breaker_open");
        return false;
    }

    Storage* storage = furi_record_open(RECORD_STORAGE);
    FileInfo info;
    bool exists = storage_common_stat(storage, path, &info) == FSE_OK;
    furi_record_close(RECORD_STORAGE);

    if(!exists) {
        gl_audit_line("hw", "subghz_tx_file", "deny", "missing file");
        return false;
    }

    if(!gl_radio_lock(500)) {
        gl_audit_line("hw", "subghz_tx_file", "deny", "radio_busy");
        return false;
    }

#if defined(GROKLINK_SUBGHZ_TX_FULL)
    /* Full encoder/TX worker: enable only after protocol review. */
    gl_radio_unlock();
    gl_audit_line("hw", "subghz_tx_file", "deny", "tx_full not linked");
    gl_stream_event("subghz_tx_denied", "\"reason\":\"tx_full_not_linked\"");
    return false;
#else
    gl_audit_line("hw", "subghz_tx_file", "allow", path);
    FURI_LOG_W("GrokHW", "TX file acknowledged (encoder path not enabled): %s", path);
    gl_stream_event("subghz_tx_ack", "\"mode\":\"ack_file\"");
    gl_radio_unlock();
    gl_radio_note_ok();
    return true;
#endif
}

/* -- IR ------------------------------------------------------------------- */

static volatile bool gl_ir_got = false;

static void gl_ir_rx_cb(void* context, InfraredWorkerSignal* signal) {
    UNUSED(context);
    UNUSED(signal);
    gl_ir_got = true;
}

bool gl_hw_ir_rx(uint32_t duration_ms) {
    InfraredWorker* worker = infrared_worker_alloc();
    gl_ir_got = false;
    infrared_worker_rx_set_received_signal_callback(worker, gl_ir_rx_cb, NULL);
    infrared_worker_rx_start(worker);

    uint32_t start = furi_get_tick();
    while((furi_get_tick() - start) < duration_ms && !gl_ir_got) {
        furi_delay_ms(20);
    }

    infrared_worker_rx_stop(worker);
    infrared_worker_free(worker);
    gl_audit_line("hw", "ir_rx", "allow", gl_ir_got ? "signal" : "timeout");
    return true;
}

bool gl_hw_ir_tx_file(const char* path) {
    if(!path) return false;
    Storage* storage = furi_record_open(RECORD_STORAGE);
    FileInfo info;
    bool exists = storage_common_stat(storage, path, &info) == FSE_OK;
    furi_record_close(RECORD_STORAGE);
    if(!exists) {
        gl_audit_line("hw", "ir_tx_file", "deny", "missing");
        return false;
    }
    /* Full .ir TX via infrared_worker_set_*  -  enable after file parser hook */
    gl_audit_line("hw", "ir_tx_file", "allow", path);
    FURI_LOG_W("GrokHW", "IR TX file ack (parser path conservative): %s", path);
    return true;
}

/* -- NFC ------------------------------------------------------------------ */

bool gl_hw_nfc_read(uint32_t timeout_ms, char* uid_out, size_t uid_cap) {
    (void)timeout_ms;
    if(uid_out && uid_cap) uid_out[0] = '\0';
    /**
     * Full NFC poller requires protocol selection + bit buffer stack.
     * Conservative: log so callers use stock NFC or a dedicated skill FAP.
     */
    gl_audit_line("hw", "nfc_read", "allow", "stub_poller");
    return true;
}

/* -- GPIO ----------------------------------------------------------------- */

bool gl_hw_gpio_read(uint32_t pin, uint8_t* value) {
    const GpioPinRecord* rec = furi_hal_resources_pin_by_number((uint8_t)pin);
    if(!rec || !rec->pin) return false;
    if(value) *value = furi_hal_gpio_read(rec->pin) ? 1 : 0;
    return true;
}

bool gl_hw_gpio_write(uint32_t pin, uint8_t value) {
    const GpioPinRecord* rec = furi_hal_resources_pin_by_number((uint8_t)pin);
    if(!rec || !rec->pin || rec->debug) {
        gl_audit_line("hw", "gpio_write", "deny", "bad pin");
        return false;
    }
    furi_hal_gpio_init(rec->pin, GpioModeOutputPushPull, GpioPullNo, GpioSpeedLow);
    furi_hal_gpio_write(rec->pin, value ? true : false);
    char detail[32];
    snprintf(detail, sizeof(detail), "pin=%lu v=%u", (unsigned long)pin, (unsigned)value);
    gl_audit_line("hw", "gpio_write", "allow", detail);
    return true;
}

bool gl_hw_skill_run(const char* skill_id) {
    gl_audit_line("hw", "skill_run", "allow", skill_id ? skill_id : "");
    return skill_id != NULL;
}

#else /* !GROKLINK_USE_FURI  -  host / review stubs */

bool gl_hw_init(void) {
    gl_audit_line("hw", "init", "allow", "stub");
    return true;
}

void gl_hw_release_all(void) {
    gl_audit_line("hw", "release_all", "allow", "");
}

bool gl_hw_subghz_rx(uint32_t freq_hz, uint32_t duration_ms, int32_t* out_pulse_count) {
    char detail[64];
    snprintf(detail, sizeof(detail), "f=%lu d=%lu", (unsigned long)freq_hz, (unsigned long)duration_ms);
    gl_audit_line("hw", "subghz_rx", "allow", detail);
    if(out_pulse_count) *out_pulse_count = 0;
    return true;
}

bool gl_hw_subghz_tx_file(const char* path) {
    gl_audit_line("hw", "subghz_tx_file", "allow", path ? path : "");
    return path != NULL;
}

bool gl_hw_ir_rx(uint32_t duration_ms) {
    (void)duration_ms;
    gl_audit_line("hw", "ir_rx", "allow", "");
    return true;
}

bool gl_hw_ir_tx_file(const char* path) {
    gl_audit_line("hw", "ir_tx_file", "allow", path ? path : "");
    return path != NULL;
}

bool gl_hw_nfc_read(uint32_t timeout_ms, char* uid_out, size_t uid_cap) {
    UNUSED(timeout_ms);
    if(uid_out && uid_cap) uid_out[0] = '\0';
    gl_audit_line("hw", "nfc_read", "allow", "");
    return true;
}

bool gl_hw_gpio_read(uint32_t pin, uint8_t* value) {
    UNUSED(pin);
    if(value) *value = 0;
    return true;
}

bool gl_hw_gpio_write(uint32_t pin, uint8_t value) {
    char detail[32];
    snprintf(detail, sizeof(detail), "pin=%lu v=%u", (unsigned long)pin, (unsigned)value);
    gl_audit_line("hw", "gpio_write", "allow", detail);
    return true;
}

bool gl_hw_skill_run(const char* skill_id) {
    gl_audit_line("hw", "skill_run", "allow", skill_id ? skill_id : "");
    return skill_id != NULL;
}

#endif /* GROKLINK_USE_FURI */
