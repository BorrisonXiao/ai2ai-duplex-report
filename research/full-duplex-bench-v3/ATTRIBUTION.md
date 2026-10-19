# Full-Duplex-Bench v3 attribution and audit notes

- Benchmark: Full-Duplex-Bench v3 (FDB-v3), by Guan-Ting Lin, Chen Chen, Zhehuai Chen and Hung-yi Lee; developed at National Taiwan University, with NVIDIA noted by the upstream project as a collaborative research contributor.
- Paper: [arXiv:2604.04847](https://arxiv.org/abs/2604.04847).
- Upstream source: [Full-Duplex-Bench at revision `3e799c45a045256f47d5f1c9cda90157e2d2ec9e`](https://github.com/DanielLin94144/Full-Duplex-Bench/tree/3e799c45a045256f47d5f1c9cda90157e2d2ec9e).
- Dataset: [official Google Drive archive](https://drive.google.com/file/d/1SO_4MTazWQ_jvCx0dtmpQ-t40bdd07yz/view?usp=sharing), downloaded 19 October 2026. The archive SHA-256 is `37545bd896f81718136598cf5be25d42ea9aa22efcd91f58370938d05d7d672f`.
- License: the upstream GitHub repository has a top-level [CC BY-NC 4.0 license](https://github.com/DanielLin94144/Full-Duplex-Bench/blob/3e799c45a045256f47d5f1c9cda90157e2d2ec9e/LICENSE). The audio was distributed separately through Google Drive; its ZIP contains no license file or reuse statement, so the repository license’s scope over the separate archive is unspecified. Three converted audio previews are included on the site; no claim is made that the repository license separately covers the archive.
- Audio changes: the three hosted WAVs are complete source recordings converted only for browser playback to mono 24 kHz PCM16. Stereo is downmixed, and source sample rates/bit depths are normalized. Speech content is not edited. Source and preview hashes appear in `preview.json`.
- Validation: 100 input WAVs and 100 metadata files pass ZIP CRC, JSON parsing, PCM WAV decoding and crosswalk checks against the pinned scenario catalogue. The audio archive covers 79 of 100 catalogue IDs; 21 catalogue IDs have no recording in this archive. The audio-side metadata preserves the matching catalogue task fields other than its per-clip dialogue, which contains the single recorded user turn.
- Local release storage: `data/benchmarks/full_duplex_bench_v3/` in the workspace; the complete archive is not included in the public site repository.

To reproduce the local integrity report, run `python scripts/validate_full_duplex_bench_v3.py` from the workspace. To rebuild the site page and three previews, run `python scripts/build_full_duplex_bench_v3.py` from the site checkout after the audit succeeds.
