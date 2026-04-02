[Auto-enriched from linked project resources]

## What is This Dataset

The Crop Disease (Ghana) dataset is an Afrocentric image collection of annotated crop leaf photos, designed for training crop disease detection models. It was created by the Responsible AI Lab and is hosted on Kaggle (version 16, last updated March 2025).

## Crops and Disease Classes

The dataset covers four crops with 22 disease and health classes total:

- **Cashew** (5 classes): anthracnose, gummosis, healthy, leaf miner, red rust
- **Cassava** (5 classes): bacterial blight, brown spot, green mite, healthy, mosaic
- **Maize** (7 classes): fall armyworm, grasshopper, healthy, leaf beetle, leaf blight, leaf spot, streak virus
- **Tomato** (5 classes): healthy, leaf blight, leaf curl, septoria leaf spot, verticillium wilt

## Dataset Size

- **Raw images**: 24,881 total (6,549 cashew, 7,508 cassava, 5,389 maize, 5,435 tomato)
- **Augmented images**: 102,976 total (25,811 cashew, 26,330 cassava, 23,657 maize, 27,178 tomato), split into train and test sets
- Download size: approximately 20 GB (ZIP format)
- Licensed under CC BY 4.0

## Data Collection

Images were captured daily during daytime from local farms in Ghana, from October 2022 to December 2022. The photos show leaves with subtle disease symptoms at various stages of crop development.

## How to Access

1. Create a free Kaggle account at kaggle.com
2. Go to https://www.kaggle.com/datasets/responsibleailab/crop-disease-ghana
3. Click "Download" to get the full ZIP archive
4. Alternatively, use the Kaggle API:
   ```bash
   kaggle datasets download -d responsibleailab/crop-disease-ghana
   ```

## How to Use

The dataset is organized as labeled image folders, making it ready for standard image classification workflows. You can load it directly with libraries such as TensorFlow (`tf.keras.utils.image_dataset_from_directory`) or PyTorch (`torchvision.datasets.ImageFolder`).

The augmented train/test split is provided for direct use in model training. The raw images are also available if you prefer to apply your own augmentation or splitting strategy.

## Limitations

- The images are from specific farming regions in Ghana; models trained on this data may not generalize to crops grown under different conditions elsewhere.
- The dataset focuses on leaf-level symptoms; it does not include whole-plant or field-level imagery.

Sources:
- https://www.kaggle.com/datasets/responsibleailab/crop-disease-ghana
