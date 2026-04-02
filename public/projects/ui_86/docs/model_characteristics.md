[Auto-enriched from linked project resources]

Pretrained Model: KinyCOMET-Unbabel, a translation quality estimation model for Kinyarwanda-English (bidirectional). Fine-tuned on Unbabel/wmt22-comet-da using the COMET framework. Input: source text, machine translation, and human reference translation. Output: quality score from 0 to 1. Achieves 0.75 Pearson correlation with human judgments (vs. 0.30 for BLEU), Spearman 0.59, MAE 0.07. A second variant (KinyCOMET-XLM) based on XLM-RoBERTa-large achieves 0.73 Pearson. Trained on 4,323 human-annotated translation pairs scored by 15 annotators following WMT Direct Assessment standards. Install via pip install unbabel-comet; load with comet.load_from_checkpoint("chrismazii/kinycomet_unbabel"). License: Apache 2.0.

Source: https://huggingface.co/datasets/chrismazii/kinycomet_dataset, https://huggingface.co/chrismazii/kinycomet_unbabel
