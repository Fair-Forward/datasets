[Auto-enriched from linked project resources]

## Overview

The Tunga Agri-Chatbot Suite provides datasets and models for building a Kinyarwanda-language agricultural advisory system delivered via Interactive Voice Response (IVR). It was built to address capacity gaps in Rwanda's agricultural extension services. The suite is implemented by C4IR Rwanda and KiNLP, supported by GIZ and financed by BMZ.

## Datasets

### Kinyarwanda Agricultural TTS Dataset

A text-to-speech dataset with 10,482 audio clips (5,242 female, 5,238 male) recorded by two voice actors at 24 kHz mono WAV format. The content covers pest and disease diagnosis, agro-climatic practices, and MINAGRI support programs. Licensed under CC-BY-4.0.

```python
from datasets import load_dataset
dataset = load_dataset("C4IR-RW/kinya-ag-tts")
```

### Kinyarwanda Agricultural Retrieval Dataset

A passage retrieval dataset containing 984 Kinyarwanda agricultural passages, 19,537 related questions, and 1,953,700 query-positive-negative triplets for training retrieval models. Includes morphologically parsed versions of all text. Licensed under CC-BY-4.0.

Note: The dataset viewer may show errors due to inconsistent column structures across files. Direct file access via the Hugging Face repository is recommended.

## Models

### kinya-flex-tts (Text-to-Speech)

A multi-speaker TTS model based on MB-iSTFT-VITS2 with three voice options (Female 1, Female 2, Male), outputting 24 kHz WAV audio. Requires PyTorch and the DeepKIN-AgAI package.

```python
import torch, torchaudio
from deepkin.data.kinya_norm import text_to_sequence
from deepkin.models.flex_tts import FlexKinyaTTS
from deepkin.modules.tts_commons import intersperse

device = torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu')
kinya_tts = FlexKinyaTTS.from_pretrained(device, '/path/to/kinya_flex_tts_base_trained.pt')
kinya_tts.eval()

text = "Your Kinyarwanda text here"
text_id_sequence = intersperse(text_to_sequence(text, norm=True), 0)
speaker_id = 0  # 0=Female1, 1=Female2, 2=Male
audio_data = kinya_tts(text_id_sequence, speaker_id)
torchaudio.save("output.wav", audio_data, 24000)
```

A live demo is available at: https://huggingface.co/spaces/Professor/c4ir-rw-kinyarwandatts

### kiny-colbert-free (Passage Retrieval)

A 0.2B-parameter retrieval model based on a BERT model fine-tuned for Kinyarwanda, designed for RAG (Retrieval-Augmented Generation) systems. It matches farmer questions to relevant agricultural knowledge passages.

```bash
pip install ragatouille==0.0.8 transformers==4.49
```

```python
from ragatouille import RAGPretrainedModel

model = RAGPretrainedModel.from_pretrained("C4IR-RW/kiny-colbert-free")

knowledge_base = [
    "Ikigori ni igihingwa cy'ingenzi gikura neza mubutaka...",
    "Gukingira inka ni intambwe y'ingenzi mu kwirinda indwara..."
]

index_path = model.index(index_name="my_index", collection=knowledge_base)

question = "Mfite ikibazo kijyanye n'ubuhinzi bw'ibigori"
RAG = RAGPretrainedModel.from_index(index_path)
results = RAG.search(question)
```

### KinyaBERT (Language Understanding)

A morphology-aware language model for Kinyarwanda (107M parameters base, 365M large) used for passage ranking. Requires the DeepKIN-AgAI package and MorphoKIN for text parsing.

## Code and Documentation

All model code, training scripts, and technical documentation are in the DeepKIN-AgAI package: https://github.com/c4ir-rw/ac-ai-models/tree/main/DeepKIN-AgAI

All components are licensed under CC-BY-4.0 with attribution required to C4IR Rwanda and KiNLP.

Sources:
- https://huggingface.co/datasets/C4IR-RW/kinya-ag-tts
- https://huggingface.co/datasets/C4IR-RW/kinya-ag-retrieval
- https://huggingface.co/C4IR-RW/kinya-flex-tts
- https://huggingface.co/C4IR-RW/kiny-colbert-free
- https://huggingface.co/C4IR-RW/kinyabert
- https://github.com/c4ir-rw/ac-ai-models
