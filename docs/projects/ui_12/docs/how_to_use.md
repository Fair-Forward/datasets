[Auto-enriched from linked project resources]

## What is CADI-AI

The Cashew Disease Identification with Artificial Intelligence (CADI-AI) project provides both a labeled image dataset and a pre-trained object detection model for identifying cashew tree health issues from drone-captured images. It was created by the KaraAgro AI Foundation, funded by GIZ and BMZ through the FAIR Forward and MOVE programs.

## Dataset

- **4,736 high-resolution images** (1600x1300 pixels) captured by drone
- Split into train (3,788), validation (710), and test (238) sets
- **22,610 annotated instances** across three classes:
  - Abiotic stress (13,960 instances) -- damage from environmental factors or nutrient deficiencies
  - Disease (7,032 instances) -- damage from microorganisms
  - Insect (1,618 instances) -- damage from pests
- Annotations are in YOLO format (text files with class labels and bounding box coordinates)
- Licensed under CC-BY-SA 4.0
- Download size: approximately 3.78 GB
- Access requires acknowledging the license on HuggingFace

### Folder structure
```
Data/
  train/
    images/
    labels/
  val/
    images/
    labels/
  test/
    images/
    labels/
```

## Pre-trained Model

- Architecture: YOLOv5x
- Model file: `yolov5_0.65map_exp7_best.pt` (approximately 173 MB)
- Licensed under AGPL-3.0

### Performance on test set

| Class    | Precision | Recall | mAP@50 | mAP@50-95 |
|----------|-----------|--------|--------|-----------|
| All      | 0.663     | 0.632  | 0.648  | 0.291     |
| Insect   | 0.794     | 0.811  | 0.815  | 0.390     |
| Abiotic  | 0.682     | 0.514  | 0.542  | 0.237     |
| Disease  | 0.594     | 0.571  | 0.588  | 0.248     |

The model performs best on the insect class due to distinct visual features. Disease and abiotic classes are harder to distinguish because their symptoms can overlap in field conditions.

## How to Run Inference

Install the required library:
```bash
pip install -U ultralytics
```

Load the model and run predictions:
```python
import torch

model = torch.hub.load('ultralytics/yolov5', 'custom',
                       path='CADI-AI/yolov5_0.65map_exp7_best.pt',
                       force_reload=True)
model.conf = 0.20  # confidence threshold

results = model(['/path/to/your/image.jpg'], size=640)
results.show()
results.save(save_dir='results/')
```

## Additional Resources

- Live demo: https://huggingface.co/spaces/KaraAgroAI/CADI-AI
- Desktop application source: https://github.com/karaagro/cadi-ai
- Datasheet with detailed methodology: available via Google Drive link in the HuggingFace dataset card

Sources:
- https://huggingface.co/datasets/KaraAgroAI/CADI-AI
- https://huggingface.co/KaraAgroAI/CADI-AI
