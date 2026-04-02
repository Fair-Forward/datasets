[Auto-enriched from linked project resources]

## What KinyCOMET Does

KinyCOMET automatically evaluates the quality of Kinyarwanda-English translations. It scores translations on a 0-to-1 scale (higher is better), achieving a 0.75 Pearson correlation with human judgments -- roughly 2.5 times more accurate than traditional BLEU scores for this language pair.

## Using the KinyCOMET Model

Install the COMET library:

```bash
pip install unbabel-comet
```

Score translations in Python:

```python
from comet import load_from_checkpoint

model = load_from_checkpoint("chrismazii/kinycomet_unbabel")

samples = [
    {
        "src": "Umugabo ararya.",
        "mt": "The man is eating.",
        "ref": "The man is eating."
    },
    {
        "src": "Umwana arasinzira.",
        "mt": "A dog sleeps.",
        "ref": "The child is sleeping."
    }
]

pred = model.predict(samples, gpus=0)
print(pred)
# Output: {'scores': [0.9899, 0.8813], 'system_score': 0.9356}
```

Or use the command line:

```bash
comet-score -s source.txt -r reference.txt -t hypothesis.txt \
  --model chrismazii/kinycomet_unbabel --gpus 0 --to_json results.json
```

Scores above 0.8 indicate high-quality translations.

## Using the Dataset

The dataset contains 4,303 human-annotated translation pairs with quality scores, annotated by 15 linguistics students (minimum 3 annotations per sample). It covers both translation directions (Kinyarwanda-to-English and English-to-Kinyarwanda) across education, tourism, and general domains.

Each entry has five fields: `src` (source text), `mt` (machine translation), `ref` (human reference), `score` (quality score 0-1), and `direction` (kin2eng or eng2kin).

Load with pandas:

```python
from huggingface_hub import hf_hub_download
import pandas as pd

train_file = hf_hub_download(repo_id="chrismazii/kinycomet_dataset", filename="train.csv")
train_df = pd.read_csv(train_file)
```

The dataset is split into train (3,497 samples), validation (404), and test (422). Licensed under Apache 2.0.

## Model Variants

Two checkpoints are available:
- **KinyCOMET-Unbabel** (built on `Unbabel/wmt22-comet-da`) -- the primary variant
- **KinyCOMET-XLM** (built on `XLM-RoBERTa-large`) -- an alternative

Sources:
- https://huggingface.co/datasets/chrismazii/kinycomet_dataset
- https://huggingface.co/chrismazii/kinycomet_unbabel
