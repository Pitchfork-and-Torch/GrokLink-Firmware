# Future On-Device ML (Post-v1.0)

## Constraints

STM32WB55: limited RAM/Flash, no GPU, shared radio core. Full LLMs are impossible on-device.

## Feasible progression

### Phase A  -  PC-side only (v1.0) [OK]

- Feature extraction offline from logs
- Grok skill generation
- Classical ML classifiers on PC for protocol hints

### Phase B  -  Tiny feature extractors on-device

- Fixed-point pulse width histograms (SubGHz)
- NFC UID pattern flags
- Ship as `lib/groklink/features.c` (~2-4 KB)
- Output vectors to mission log for PC training

### Phase C  -  Tiny models

- [CMSIS-NN](https://github.com/ARM-software/CMSIS-NN) or [TensorFlow Lite Micro](https://www.tensorflow.org/lite/microcontrollers)
- Models <= 20-40 KB flash, <= 8 KB arena
- Tasks: binary "interesting burst?", simple modulation class
- Never auto-TX from model score alone  -  always policy layer

### Phase D  -  Edge + Grok hybrid

```
on-device features -> optional tiny model score
                 -> mission branch
                 -> on reconnect: Grok refines skills / retrain
```

## API hooks reserved in v1.0

```c
// gl_features.h  -  stubs return empty vectors until Phase B
bool gl_features_subghz_histogram(const uint32_t* timings, size_t n, gl_feature_vec_t* out);
bool gl_ml_infer(const gl_feature_vec_t* in, gl_ml_result_t* out); // weak stub
```

## Training loop (PC)

1. Pull labeled captures
2. Train sklearn / tiny TF model
3. Export quantized C array
4. Skill craft packages model + feature code as a skill
5. Human approve deploy to SD / firmware rebuild if linked statically
