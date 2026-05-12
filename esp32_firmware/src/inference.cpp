#include "inference.h"
#include "model.h"
#include <math.h>

// ── Nystroem + Linear OCSVM inference ──────────────────────────────────────
//
// Pipeline:
//   1. StandardScaler:  x_scaled[i] = (features[i] - mean[i]) / scale[i]
//   2. Nystroem RBF:    k[j] = exp(-gamma * ||x_scaled - component[j]||^2)
//   3. Normalization:   z[i] = sum_j( normalization[i][j] * k[j] )
//   4. Linear SVM:      score = dot(w, z) + intercept
//

float ocsvm_score(const float *features) {
    // ── Step 1: StandardScaler ──
    float x_scaled[N_FEATURES];
    for (int i = 0; i < N_FEATURES; i++) {
        x_scaled[i] = (features[i] - SCALER_MEAN[i]) / SCALER_SCALE[i];
    }

    // ── Step 2: RBF kernel to each Nystroem component ──
    float kernel[N_COMPONENTS];
    for (int j = 0; j < N_COMPONENTS; j++) {
        float dist_sq = 0.0f;
        const float *comp = &NYS_COMPONENTS[j * N_FEATURES];
        for (int i = 0; i < N_FEATURES; i++) {
            float diff = x_scaled[i] - comp[i];
            dist_sq += diff * diff;
        }
        kernel[j] = expf(-GAMMA * dist_sq);
    }

    // ── Step 3: Normalization (200x200 matrix × 200 vector) ──
    float z[N_COMPONENTS];
    for (int i = 0; i < N_COMPONENTS; i++) {
        float sum = 0.0f;
        const float *row = &NYS_NORMALIZATION[i * N_COMPONENTS];
        for (int j = 0; j < N_COMPONENTS; j++) {
            sum += row[j] * kernel[j];
        }
        z[i] = sum;
    }

    // ── Step 4: Linear SVM decision ──
    float score = INTERCEPT;
    for (int i = 0; i < N_COMPONENTS; i++) {
        score += SVM_W[i] * z[i];
    }

    return score;
}
