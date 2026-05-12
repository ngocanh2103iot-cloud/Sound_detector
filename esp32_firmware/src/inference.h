#pragma once

// Nystroem + Linear OCSVM inference for anomaly detection
// Pipeline: raw features → scale → nystroem transform → dot(w, z) + intercept

// Run the full inference pipeline on a 39-dim feature vector.
// Returns the OCSVM decision score.
float ocsvm_score(const float *features);
