/**
 * Lightweight stream events over CLI (USB).
 * Format: GROKSTREAM:{...}\r\n
 */
#include "gl_stream.h"

#include <stdio.h>
#include <string.h>

void gl_stream_event(const char* kind, const char* json_object_body) {
    if(!kind) return;
    /* Keep short for VCP; body is raw JSON object fields or empty */
    if(json_object_body && json_object_body[0]) {
        printf("GROKSTREAM:{\"kind\":\"%s\",%s}\r\n", kind, json_object_body);
    } else {
        printf("GROKSTREAM:{\"kind\":\"%s\"}\r\n", kind);
    }
}
