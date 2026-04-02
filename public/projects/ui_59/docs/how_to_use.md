[Auto-enriched from linked project resources]

## Accessing the Data

The Kinyarwanda voice data is available through two channels:

- **Mozilla Data Collective**: The "Common Voice Scripted Speech 25.0 - Kinyarwanda" dataset (57.18 GB of MP3 recordings) is available at the Mozilla Data Collective platform under a CC0-1.0 license, meaning it can be used without restrictions.

- **Hugging Face**: The `mbazaNLP/common-voice-kinyarwanda-english-dataset` provides a bilingual compilation (Kinyarwanda and English) with 721,395 text transcription entries across train/validation/test splits, licensed under CC-BY-4.0. Note that this dataset currently contains text transcriptions only; audio files are planned for a future release.

## Loading the Hugging Face Dataset

```python
from datasets import load_dataset

# Load the full dataset
dataset = load_dataset("mbazaNLP/common-voice-kinyarwanda-english-dataset")

# Or load a specific split
train_data = load_dataset("mbazaNLP/common-voice-kinyarwanda-english-dataset", split="train")
```

The dataset can also be loaded with pandas:

```python
import pandas as pd
df = pd.read_parquet("default/train/*.parquet")
```

## What the Dataset Contains

Each entry includes:
- `audio_filepath` -- path to the audio file (e.g. `train_data/0.wav`)
- `duration` -- audio duration in seconds
- `text` -- the transcription text

The Hugging Face dataset has three splits: train (619,000 rows), validation (61,600 rows), and test (41,200 rows).

## Intended Use

The dataset is designed for training multilingual Automatic Speech Recognition (ASR) systems that handle both Kinyarwanda and English. It can be used with the Hugging Face `datasets` library, pandas, or polars.

Sources:
- https://datacollective.mozillafoundation.org/datasets?q=common+voice&locale=rw
- https://huggingface.co/datasets/mbazaNLP/common-voice-kinyarwanda-english-dataset
