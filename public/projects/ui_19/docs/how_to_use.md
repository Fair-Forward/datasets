[Auto-enriched from linked project resources]

## Getting the Data

The dataset is hosted on HuggingFace and is openly accessible without a gated access request. The total size is approximately 45.6 GB.

Browse and download: https://huggingface.co/datasets/KaraAgroAI/Drone-based-Agricultural-Dataset-for-Crop-Yield-Estimation

DOI: 10.57967/hf/0959

## What You Get

A total of 14,870 drone-captured images of cashew, cocoa, and coffee crops with YOLO-format bounding box annotations:

**Ghana (KaraAgro AI) -- 8,784 images at 16000 x 13000 pixels:**
- Cashew: 4,715 images
- Cocoa: 4,069 images

**Uganda (Makerere AI Lab, Uganda Marconi Lab, NCRRI) -- 6,086 images at 4000 x 3000 pixels:**
- Cashew: 3,086 images
- Coffee: 3,000 images

**Folder structure:**
```
Data/
  Ghana/
    cashew.zip
    cocoa.zip
  Uganda/
    cashew.zip
    coffee.zip
```

## Annotation Details

Each image has a corresponding `.txt` file in YOLO format containing class labels (integer index) and normalized bounding box coordinates (x_center, y_center, width, height).

**Ghana -- Cashew classes and instance counts:**
cashew_tree (1,107), flower (16,757), immature (11,766), mature (4,244), ripe (11,721), spoilt (518)

**Ghana -- Cocoa classes and instance counts:**
cocoa-pod-mature-unripe (10,786), cocoa-tree (2,831), cocoa-pod-immature (2,401), cocoa-pod-riped (4,193), cocoa-pod-spoilt (2,018)

**Uganda -- Cashew classes:**
cashew_tree, flower, immature, mature, ripe, spoilt

**Uganda -- Coffee classes:**
unripe, ripening, ripe, spoilt, coffee

## How to Use It

The annotations follow the YOLO object detection format, so the data can be loaded directly into YOLO-based training pipelines. Each ZIP file contains paired image and annotation files ready for model training.

The class labels capture crop maturity stages (immature, mature, ripe, spoilt), which supports:
- Crop yield estimation through fruit counting and maturity classification
- Crop health monitoring via detection of spoilt fruits
- Object detection model development for agricultural drone imagery

Note that the Ghana images (16000 x 13000 px) are significantly higher resolution than the Uganda images (4000 x 3000 px), which may require different preprocessing approaches if combining both sources.

The dataset repository also includes PDF documentation (a datasheet and full dataset description) with details on collection methodology and variable definitions.

## License

Creative Commons Attribution 4.0 International (CC BY 4.0).

Source: https://huggingface.co/datasets/KaraAgroAI/Drone-based-Agricultural-Dataset-for-Crop-Yield-Estimation
