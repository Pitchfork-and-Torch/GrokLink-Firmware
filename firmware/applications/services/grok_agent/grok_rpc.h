#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * GrokRPC handler  -  process one request buffer, write response.
 * Framing: length-prefixed protobuf (or JSON mode for bridge compact path).
 */
typedef enum {
    GrokRpcFmtProtobuf = 0,
    GrokRpcFmtJson = 1,
} GrokRpcFormat;

typedef struct {
    GrokRpcFormat format;
    char session_id[40];
    bool session_active;
    bool edu_ack;
    bool stream_audit;
    bool stream_mission;
} GrokRpcSession;

bool grok_rpc_session_init(GrokRpcSession* s);

/**
 * Handle a single request.
 * @param req      request bytes
 * @param req_len  length
 * @param resp     output buffer
 * @param resp_cap capacity
 * @param resp_len out length
 */
bool grok_rpc_handle(
    GrokRpcSession* s,
    const uint8_t* req,
    size_t req_len,
    uint8_t* resp,
    size_t resp_cap,
    size_t* resp_len);

#ifdef __cplusplus
}
#endif
