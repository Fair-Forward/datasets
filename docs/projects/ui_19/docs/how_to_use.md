[Auto-enriched from linked project resources]

This drone-based agricultural dataset is designed for anyone working on crop yield estimation, crop health monitoring, or object detection in smallholder farming contexts. It contains 14,870 high-resolution drone images of cashew, cocoa, and coffee crops from Ghana and Uganda, each paired with bounding box annotations that label individual fruits by maturity stage -- immature, mature, ripe, and spoilt.

You can use these images to train models that count and classify fruits from aerial imagery, enabling plot-level yield estimation without manual field counts. The maturity-stage labels also support crop health monitoring, since spoilt fruit detection can flag disease or post-harvest loss issues early. Because the dataset covers three different cash crops across two countries, it lends itself to cross-crop and cross-region transfer learning experiments -- for example, testing whether a model trained on Ghanaian cashew generalises to Ugandan cashew, or adapting a cocoa detector for coffee.

Researchers and developers should note that the Ghana images (16,000 x 13,000 px, collected by KaraAgro AI) are significantly higher resolution than the Uganda images (4,000 x 3,000 px, collected by Makerere AI Lab, Uganda Marconi Lab, and NCRRI). This difference may require separate preprocessing pipelines or resolution-aware training strategies if combining both sources.

The annotations use the YOLO object detection format, so the data can be loaded directly into standard YOLO-based training pipelines. The dataset repository also includes PDF documentation covering collection methodology and variable definitions.

The full dataset (~45.6 GB) is openly available on HuggingFace under a CC BY 4.0 license: https://huggingface.co/datasets/KaraAgroAI/Drone-based-Agricultural-Dataset-for-Crop-Yield-Estimation

Source: https://huggingface.co/datasets/KaraAgroAI/Drone-based-Agricultural-Dataset-for-Crop-Yield-Estimation
