/**
 * Flipper Furi storage / time overrides.
 * Compile with -DGROKLINK_USE_FURI (service cdefines).
 */
#include "gl_config.h"

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#if defined(GROKLINK_USE_FURI)

#include <furi.h>
#include <furi_hal.h>
#include <storage/storage.h>

uint32_t gl_now_unix(void) {
    return furi_hal_rtc_get_timestamp();
}

uint32_t gl_now_ms(void) {
    return furi_get_tick();
}

static void gl_ensure_log_dirs(Storage* storage) {
    storage_common_mkdir(storage, "/ext/groklink");
    storage_common_mkdir(storage, "/ext/groklink/logs");
    storage_common_mkdir(storage, "/ext/groklink/missions");
    storage_common_mkdir(storage, "/ext/groklink/skills");
    storage_common_mkdir(storage, "/ext/groklink/config");
    storage_common_mkdir(storage, "/ext/groklink/blacklist");
}

bool gl_storage_append_line(const char* path, const char* line) {
    if(!path || !line) return false;
    Storage* storage = furi_record_open(RECORD_STORAGE);
    gl_ensure_log_dirs(storage);
    File* file = storage_file_alloc(storage);
    bool ok = false;
    if(storage_file_open(file, path, FSAM_WRITE, FSOM_OPEN_APPEND) ||
       storage_file_open(file, path, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        size_t n = strlen(line);
        ok = storage_file_write(file, line, n) == n;
        ok = (storage_file_write(file, "\n", 1) == 1) && ok;
        storage_file_close(file);
    }
    storage_file_free(file);
    furi_record_close(RECORD_STORAGE);
    return ok;
}

bool gl_storage_read_file(const char* path, char* buf, size_t cap, size_t* out_len) {
    if(!buf || cap == 0 || !path) return false;
    Storage* storage = furi_record_open(RECORD_STORAGE);
    File* file = storage_file_alloc(storage);
    bool ok = false;
    if(storage_file_open(file, path, FSAM_READ, FSOM_OPEN_EXISTING)) {
        size_t n = storage_file_read(file, buf, cap - 1);
        buf[n] = '\0';
        if(out_len) *out_len = n;
        storage_file_close(file);
        ok = true;
    }
    storage_file_free(file);
    furi_record_close(RECORD_STORAGE);
    return ok;
}

bool gl_storage_sd_present(void) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    FileInfo info;
    bool ok = storage_common_stat(storage, "/ext", &info) == FSE_OK;
    furi_record_close(RECORD_STORAGE);
    return ok;
}

#endif /* GROKLINK_USE_FURI */
