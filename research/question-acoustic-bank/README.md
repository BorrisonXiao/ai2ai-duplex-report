# Revised question audio — 31 October 2026

This current input bank contains 105 distinct primary questions and six additional published Qwen/Chatterbox versions of the original three AMI questions. Unsynthesized text alternatives and rejected TTS drafts are excluded.

- `current-input-index.json` maps every primary question ID to its revised question and source-excerpt WAVs, insertion time and hashes.
- `review.json` records all 111 versions, paired original/revised Parakeet transcripts, background controls, calibration intervals, source-PCM checks and seven remaining ASR caveats.
- `manifest.json` checks every file in this bundle except itself.

The revision preserves wording and timing and copies original source PCM exactly before and after each insertion. Acoustic calibration uses only earlier audio. Most versions use actual earlier room tone; 35 use speech-free stationary texture matched to a past quiet-frame spectrum and RMS after screening. All 12 earnings-call versions use that texture because estimated word timestamps cannot establish a speech-free gap. Past paired speech provides bounded spectral EQ where available; 17 sparse-reference versions use identity EQ. No voice weights are trained and no room impulse response or artificial reverberation is added.

All 111 background-only controls have empty Parakeet transcripts. The wake word is recognized in every version, appears first in 109/111 (110/111 in the originals), and the simple normalized full transcript is exact in 88/111 (91/111 originally). These ASR-guided checks do not establish human naturalness, voice similarity or perfect pronunciation. All seven paired-ASR regressions remain in the review, including the slide/slight ambiguity; existing proper-name limitations remain.

Original synthesis data and metrics remain in their original study bundles. Original ECAPA values displayed in the listening library describe original synthesis and were not recomputed for the acoustic revision. New S1 figures and response transcripts are separate, newly executed measurements. The full 105-question system comparison remains unvalidated.

[Listen to the revised library](../../experiments/question-audio.html) · [Current stress-test report](../../study-progress.html)
