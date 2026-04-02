[Auto-enriched from linked project resources]

This resource is useful for anyone working on urban mobility analysis, road infrastructure planning, or land-use evaluation in cities of the Global South. The UrbanInfraDL repository provides a deep learning pipeline for segmenting road infrastructure -- roads, sidewalks, and bicycle lanes -- from satellite imagery, with a focus on Bogota, Colombia.

You can use the provided patch extraction tool and training scripts for three segmentation architectures (DeepLabV3+, SegFormer, U-Net) to train models that classify urban road space from your own satellite imagery. This makes it possible to evaluate how road space is allocated across different transport modes and to support evidence-based advocacy for more equitable infrastructure distribution.

Researchers and developers can extend this work by applying the pipeline to other cities with similar urban structures, or by incorporating additional annotation classes (e.g., bus lanes, green spaces) to broaden the analysis. The modular design -- separate patch extraction and model training steps -- makes it straightforward to experiment with different architectures or hyperparameters.

Known limitations: No pre-trained model weights or sample datasets are included in the repository; you will need your own high-resolution TIFF satellite imagery and corresponding label files. The repository does not document its Python dependencies, so some setup effort is required. The codebase is a research prototype (8 commits) rather than a production-ready tool.

Source: https://github.com/yangshao2/UrbanInfraDL