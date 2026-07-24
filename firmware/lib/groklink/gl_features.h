/**
 * Feature extractors / ML stubs  -  reserved for Phase B/C (see docs/EXTENSIBILITY_ML.md)
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define GL_FEATURE_DIM 16

typedef struct {
    float v[GL_FEATURE_DIM];
    uint8_t dim;
} GlFeatureVec;

typedef struct {
    float score; /* 0..1 interestingness */
    uint8_t class_id;
    char label[24];
} GlMlResult;

bool gl_features_subghz_histogram(const uint32_t* timings, size_t n, GlFeatureVec* out);

/** Weak stub: returns false until a model is linked. */
bool gl_ml_infer(const GlFeatureVec* in, GlMlResult* out);

#ifdef __cplusplus
}
#endif
