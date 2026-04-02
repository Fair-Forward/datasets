[Auto-enriched from linked project resources]

## Getting Started

The UrbanInfraDL repository provides a deep learning pipeline for analyzing urban road infrastructure from satellite imagery, with a focus on Bogota, Colombia. The repository includes a patch extraction tool and three model training scripts.

## What is in the Repository

- **patch_extractor.py** -- a command-line utility that generates image patches from large TIFF files. It supports two modes:
  - `raw` mode: processes raw satellite images and saves patches to an `images/` folder
  - `label` mode: processes reference label images (road, sidewalk, and bicycle lane annotations) and saves patches to a `labels/` folder

- **Training scripts** for three segmentation architectures:
  - `deeplabv3plus_trainer.py`
  - `segformer_trainer.py`
  - `unet_trainer.py`

- A `data/` directory (contents not documented in the README)

## How to Use the Patch Extractor

Run the tool from the command line, specifying mode, input/output directories, patch size, and stride:

```
python patch_extractor.py --mode raw --input_dir /path/to/raw_images --output_dir /path/to/output --patch_size 256 256 --stride 128 128
```

You can adjust `--patch_size` and `--stride` to control the dimensions and overlap of extracted patches for your training data.

## Limitations

- The README does not list dependencies or installation instructions; you will need to inspect the code for required Python packages.
- No pre-trained model weights are provided in the repository.
- No dataset download links are included; you need your own TIFF satellite imagery and corresponding label files.
- The repository is small (8 commits) and may be a research prototype rather than a production tool.

Source: https://github.com/yangshao2/UrbanInfraDL
