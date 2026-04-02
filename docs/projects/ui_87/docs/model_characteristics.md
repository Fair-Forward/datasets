[Auto-enriched from linked project resources]

Two pretrained models for a Kinyarwanda agricultural IVR system. (1) TTS Model (kinya-flex-tts): Multi-speaker text-to-speech based on MB-iSTFT-VITS2 architecture. Converts Kinyarwanda text to speech at 24 kHz with 3 speaker options (2 female, 1 male). Requires PyTorch; implementation via the DeepKIN-AgAI package. (2) Retrieval Model (kiny-colbert-free): Information retrieval model for RAG, fine-tuned from Davlan/bert-base-multilingual-cased-finetuned-kinyarwanda. 0.2B parameters, F32 safetensors format. Trained on agricultural question-passage pairs. Usable via ragatouille library. Both models by C4IR Rwanda and KiNLP. License: CC-BY 4.0.

Source: https://huggingface.co/C4IR-RW/kinya-flex-tts, https://huggingface.co/C4IR-RW/kiny-colbert-free
