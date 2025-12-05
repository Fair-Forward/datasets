Miti360 contains the following core components and formats (quantities as provided):
- Orthophotos (GeoTIFF): high-resolution stitched orthomosaics (2 GeoTIFFs) and 844 orthophoto tiles exported for annotation. 
- Tree crown annotations (orthophoto): ~24,000 annotated crowns (bounding boxes) exported in JSON; 1,208 crowns have species labels and are also provided as a 1208-feature shapefile (SHP). 
- Ground measurements (numeric): 1,208 measurement records (600 individual trees sampled twice across two campaigns) in JSON — fields include tree height, crown diameter, basal diameter, and GPS coordinates. 
- Terrestrial single images: 1,208 JPEG images paired with semantic segmentation masks (mask files exported alongside images). 
- Terrestrial stereo images: 2,416 JPEG stereoscopic image pairs (left/right) with corresponding masks for 3D/photogrammetric workflows. 
- Weather time series: daily data spanning 8 years from 40 stations, accessible via an API endpoint for linking meteorological drivers to growth. 
All annotations and metadata use common interchange formats (JSON, SHP, GeoTIFF, JPEG) to enable GIS analyses and ML training without format conversion
