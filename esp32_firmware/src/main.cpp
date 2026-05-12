#include <Arduino.h>
#include "config.h"
#include "audio.h"
#include "features.h"
#include "inference.h"
#include "model.h"

// ── Alert state ──
static int consecutive_abnormal = 0;
static const int ALERT_CONSECUTIVE = 3;  // frames to trigger sustained alert
static const int LED_PIN = 2;            // built-in LED on most ESP32 boards

void setup() {
    Serial.begin(115200);
    while (!Serial) { delay(10); }

    Serial.println("========================================");
    Serial.println("  Sound Anomaly Detector - ESP32");
    Serial.println("  Nystroem + Linear OCSVM");
    Serial.println("========================================");
    Serial.printf("  Features:   %d\n", N_FEATURES);
    Serial.printf("  Components: %d\n", N_COMPONENTS);
    Serial.printf("  Gamma:      %.10f\n", GAMMA);
    Serial.printf("  Intercept:  %.4f\n", INTERCEPT);
    Serial.printf("  Threshold1: %.4f\n", THRESHOLD_1);
    Serial.printf("  Threshold2: %.4f\n", THRESHOLD_2);
    Serial.println("========================================");

    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    audio_init();
    features_init();

    Serial.println("System ready. Starting inference loop...\n");
}

void loop() {
    unsigned long t0 = millis();

    // 1. Record audio (dummy mode: copies from dummy_audio.h)
    record_audio();
    unsigned long t1 = millis();

    // 2. Extract 39-dim MFCC features
    float features[FEATURE_COUNT];
    extract_features(features);
    unsigned long t2 = millis();

    // 3. Run OCSVM inference
    float score = ocsvm_score(features);
    unsigned long t3 = millis();

    // 4. Classify
    const char *label;
    if (score >= THRESHOLD_2) {
        label = "NORMAL";
        consecutive_abnormal = 0;
        digitalWrite(LED_PIN, LOW);
    } else if (score <= THRESHOLD_1) {
        label = "ABNORMAL";
        consecutive_abnormal++;
    } else {
        label = "UNCERTAIN";
        // Don't reset counter for uncertain zone
    }

    // 5. Sustained alert check
    bool alert = (consecutive_abnormal >= ALERT_CONSECUTIVE);
    if (alert) {
        digitalWrite(LED_PIN, HIGH);
    }

    // 6. Print results
    Serial.printf("[%s] score=%.4f | feat=%lums infer=%lums",
                  label, score, (t2 - t1), (t3 - t2));
    if (alert) {
        Serial.printf(" *** ALERT (%d consecutive) ***", consecutive_abnormal);
    }
    Serial.println();

    // Print first few features for debugging
    Serial.printf("  features[0..4]: %.2f, %.2f, %.2f, %.2f, %.2f\n",
                  features[0], features[1], features[2], features[3], features[4]);
}
