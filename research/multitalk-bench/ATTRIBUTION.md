# MultiTalkBench attribution

MultiTalkBench is by Ke Wang, Houxing Ren, Zimu Lu, Yunqiao Yang, Zhuofan Zong, Mingjie Zhan, and Hongsheng Li. The source release is hosted at [Hugging Face](https://huggingface.co/datasets/MultiTalk/MultiTalkBench), pinned here to revision d7188c179603db8566c50b6e43af5c8a1e7678ba, and is identified as CC BY-SA 4.0 in its dataset card.

This site distributes two 15-second excerpts under the same CC BY-SA 4.0 terms. They are lossless PCM16 FLAC crops from the original 16 kHz stereo recordings, with no resampling or channel mixing:

- EN2002a.Headset-0.SPKMEE073: audio/en/EN2002a.Headset-0.SPKMEE073.flac, seconds 0–15.
- R8008_M8017_N_SPK8065: audio/zh/R8008_M8017_N_SPK8065.flac, seconds 18.63–33.63.

The excerpt and source hashes, timing bounds, and the dataset integrity record are in [preview.json](preview.json) and [validation.json](validation.json).

Please cite:

@inproceedings{wang2026multitalk,
  title={MultiTalk: Scaling Full-Duplex Speech Models to Long, Multi-Party, Bilingual Conversation},
  author={Wang, Ke and Ren, Houxing and Lu, Zimu and Yang, Yunqiao and Zong, Zhuofan and Zhan, Mingjie and Li, Hongsheng},
  booktitle={The Fortieth Annual Conference on Neural Information Processing Systems Evaluations and Datasets Track},
  year={2026},
  url={https://openreview.net/forum?id=G9Adf8ZYoP}
}
