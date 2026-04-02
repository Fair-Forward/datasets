[Auto-enriched from linked project resources]

## How to Use This Resource

KinyCOMET is a tool for automatically evaluating the quality of Kinyarwanda-English translations. It scores translations on a 0-to-1 scale, achieving a 0.75 Pearson correlation with human judgments -- roughly 2.5 times more accurate than traditional BLEU scores for this language pair. Scores above 0.8 indicate high-quality translations.

This resource is valuable for anyone developing or deploying machine translation systems involving Kinyarwanda, whether for development programmes, government communications, educational materials, or other contexts where translation quality matters. Rather than relying on expensive and time-consuming human evaluation for every translation, KinyCOMET provides a reliable automated quality check that can be integrated into translation workflows. The model is available on [Hugging Face as chrismazii/kinycomet_unbabel](https://huggingface.co/chrismazii/kinycomet_unbabel), with an alternative variant (KinyCOMET-XLM, built on XLM-RoBERTa-large) also available. Both can be used through the open-source COMET library.

The accompanying dataset, hosted on [Hugging Face as chrismazii/kinycomet_dataset](https://huggingface.co/datasets/chrismazii/kinycomet_dataset), contains 4,303 human-annotated translation pairs with quality scores. These were annotated by 15 linguistics students, with a minimum of 3 annotations per sample, covering both translation directions (Kinyarwanda-to-English and English-to-Kinyarwanda) across education, tourism, and general domains. The dataset is split into train (3,497 samples), validation (404), and test (422), and is licensed under Apache 2.0.

Researchers can use this dataset to train improved evaluation models for Kinyarwanda or adapt the methodology to other low-resource African languages where automated translation quality assessment is similarly lacking. The human annotations provide a ground-truth benchmark that did not previously exist for this language pair.

Sources:
- https://huggingface.co/datasets/chrismazii/kinycomet_dataset
- https://huggingface.co/chrismazii/kinycomet_unbabel