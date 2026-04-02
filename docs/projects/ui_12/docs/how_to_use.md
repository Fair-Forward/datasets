[Auto-enriched from linked project resources]

The CADI-AI project is useful for anyone working on cashew crop health monitoring, agricultural extension, or precision agriculture in West Africa. It provides both a labeled image dataset and a ready-to-use pre-trained model for detecting three types of cashew tree health issues -- abiotic stress, disease damage, and insect damage -- from drone-captured imagery.

If you want to try the model immediately, a live demo is available on HuggingFace Spaces where you can upload your own cashew tree images and see detection results without any setup. For deployment in the field, a desktop application is also available on GitHub. These tools allow agricultural extension officers and agronomists to identify health issues across cashew plantations quickly, enabling targeted interventions rather than blanket treatments.

The dataset itself contains 4,736 high-resolution drone images (1600x1300 pixels) with over 22,000 annotated instances across the three health-issue classes, licensed under CC-BY-SA 4.0. Researchers and developers can use this data to train improved detection models or to extend the approach to other tree crops. The annotations are in YOLO format, and the pre-trained YOLOv5x model achieves a mean average precision (mAP@50) of 0.65, with strongest performance on insect damage detection (0.82 mAP@50) due to its distinct visual features. Disease and abiotic stress classes are harder to distinguish because their symptoms can overlap in field conditions -- an area where further research could improve accuracy.

A detailed datasheet documenting the data collection methodology is available via the HuggingFace dataset card. The dataset (approximately 3.78 GB) and model (approximately 173 MB) can be downloaded from HuggingFace after acknowledging the license terms.

Cost and resources: The dataset and model are freely available. Deploying the model requires only standard compute resources. The CADI-AI project was created by the KaraAgro AI Foundation, funded by GIZ and BMZ through the FAIR Forward and MOVE programs.

Sources:
- https://huggingface.co/datasets/KaraAgroAI/CADI-AI
- https://huggingface.co/KaraAgroAI/CADI-AI
