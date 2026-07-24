#pragma once

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Emit a single GROKSTREAM JSON line for PC consumers (best-effort). */
void gl_stream_event(const char* kind, const char* json_object_body);

#ifdef __cplusplus
}
#endif
