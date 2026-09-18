#include "gl_features.h"

#include <string.h>

bool gl_features_subghz_histogram(const uint32_t* timings, size_t n, GlFeatureVec* out) {
    if(!out) return false;
    memset(out, 0, sizeof(*out));
    out->dim = GL_FEATURE_DIM;
    if(!timings || n == 0) return true;

    /* Simple 16-bin log-ish duration histogram (fixed point style via float for clarity) */
    for(size_t i = 0; i < n; i++) {
        uint32_t t = timings[i];
        unsigned bin = 0;
        while(bin < 15 && t > (1u << (bin + 3))) bin++;
        out->v[bin] += 1.0f;
    }
    /* L1 normalize */
    float sum = 0.f;
    for(int i = 0; i < GL_FEATURE_DIM; i++) sum += out->v[i];
    if(sum > 0.f) {
        for(int i = 0; i < GL_FEATURE_DIM; i++) out->v[i] /= sum;
    }
    return true;
}

__attribute__((weak)) bool gl_ml_infer(const GlFeatureVec* in, GlMlResult* out) {
    (void)in;
    if(out) {
        out->score = 0.f;
        out->class_id = 0;
        out->label[0] = '\0';
    }
    return false; /* no model linked in v1.0 */
}
