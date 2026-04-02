[Auto-enriched from linked project resources]

## How to Use This Resource

The Tunga Agri-Chatbot Suite provides the building blocks for a Kinyarwanda-language agricultural advisory system delivered via Interactive Voice Response (IVR). It was built to address capacity gaps in Rwanda's agricultural extension services and is implemented by C4IR Rwanda and KiNLP, supported by GIZ and financed by BMZ.

This suite is relevant for anyone working on agricultural extension, farmer advisory services, or voice-based information delivery in Rwanda or similar contexts. The core idea is that smallholder farmers can call a phone number and receive spoken agricultural guidance in Kinyarwanda -- covering topics such as pest and disease diagnosis, agro-climatic practices, and MINAGRI support programmes -- without needing internet access or literacy.

The text-to-speech component (kinya-flex-tts) can generate natural-sounding Kinyarwanda speech with three voice options (two female, one male), outputting audio at broadcast quality (24 kHz). A live demo is available at [huggingface.co/spaces/Professor/c4ir-rw-kinyarwandatts](https://huggingface.co/spaces/Professor/c4ir-rw-kinyarwandatts), where you can hear sample outputs before deciding whether to integrate the model. The underlying TTS training dataset contains 10,482 audio clips recorded by two voice actors, all licensed under CC-BY-4.0.

The passage retrieval component (kiny-colbert-free) matches farmer questions in Kinyarwanda to relevant agricultural knowledge passages. This is the engine that allows the system to find the right answer from a knowledge base when a farmer asks a question. The accompanying retrieval dataset contains 984 agricultural passages, 19,537 related questions, and nearly 2 million training triplets, also under CC-BY-4.0.

The suite also includes KinyaBERT, a morphology-aware language model for Kinyarwanda used for passage ranking, available in base (107M parameter) and large (365M parameter) variants. All model code, training scripts, and technical documentation are available in the [DeepKIN-AgAI package on GitHub](https://github.com/c4ir-rw/ac-ai-models/tree/main/DeepKIN-AgAI). All components require attribution to C4IR Rwanda and KiNLP.

Developers and researchers can extend this work to other crops, regions, or languages, or integrate these components into existing agricultural advisory platforms. The individual models (TTS, retrieval, language understanding) can also be used independently for other Kinyarwanda language technology applications beyond agriculture. All datasets and models are hosted on Hugging Face under the [C4IR-RW organisation](https://huggingface.co/C4IR-RW).

Sources:
- https://huggingface.co/datasets/C4IR-RW/kinya-ag-tts
- https://huggingface.co/datasets/C4IR-RW/kinya-ag-retrieval
- https://huggingface.co/C4IR-RW/kinya-flex-tts
- https://huggingface.co/C4IR-RW/kiny-colbert-free
- https://huggingface.co/C4IR-RW/kinyabert
- https://github.com/c4ir-rw/ac-ai-models