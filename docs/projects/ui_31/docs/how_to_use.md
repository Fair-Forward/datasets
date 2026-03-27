The pipeline is designed to handle multi-source satellite imagery and corresponding biomass data with pixel-level precision. Key aspects include:

End-to-End Workflow: From raw data ingestion to model training, evaluation, and deployment
Advanced Feature Engineering: Comprehensive spectral indices, texture features, spatial gradients, and PCA components
Stable Neural Architecture: Utilizes a custom StableResNet with residual connections and layer normalization for robust biomass regression
Multi-Site Data Processing: Capable of processing and integrating data from multiple geographically distinct study sites
Flexible Deployment: Includes HuggingFace deployment capabilities with Gradio interface
Memory Efficient Processing: Chunk-based processing for handling large satellite images