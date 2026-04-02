[Auto-enriched from linked project resources]

## Getting the Data

The PheDEF dataset is distributed across two repositories:

**Zenodo** (ground observations, climate, citizen science, phenocam data):
https://zenodo.org/records/15704554

**4TU.ResearchData** (satellite imagery and vegetation indices):
- Sentinel-2 subsets and indices (~30 GB): https://doi.org/10.4121/d97e338b-dc94-4e3d-a473-6dd3d4b48898.v1
- Landsat subsets and indices (~1.5 GB): https://doi.org/10.4121/9e6b4bca-f3d3-40f3-a8f5-4f71f7790c2f.v1
- MODIS EVI subsets (2,861 GeoTIFF files): https://doi.org/10.4121/7e6d7ca3-060d-4ca5-bd83-d779b598c11d.v1

All data is openly accessible and free to download. Each repository provides individual file downloads or full-archive options.

## What You Get

Six interconnected datasets covering 48 weeks of observations (July 2024 -- June 2025) from Bobiri Forest Reserve and Boabeng Fiema Monkey Sanctuary in Ghana:

**From Zenodo (CSV files):**
- **Ground phenology** (9.1 MB) -- Field observations of flowering, fruiting, and leaf phases in tagged trees and lianas across forest plots. Contains 28 variables including species name, flower/fruit/leaf phase stages, and crown visibility.
- **Traditional ecological knowledge** (22.6 MB) -- Community interviews from 10 communities documenting local phenological calendars, with respondent demographics (age, gender, occupation, years in community).
- **Phenocam index data** (933 KB) -- Camera-derived vegetation indices and color channel metrics (22 metrics per observation including GRVI, excess greenness, brightness, contrast).
- **Citizen science classifications** (100.3 MB) -- Zooniverse volunteer labels for leafing, flowering, and fruiting events from images.
- **Climate data** (13.7 MB) -- Weather station measurements: temperature, precipitation, humidity, wind speed/direction, and dew point from both forest sites.

**From 4TU.ResearchData (GeoTIFF files):**
- Sentinel-2 and Landsat image subsets cropped to the two study areas
- Derived vegetation indices: ARVI, EBI, EVI, EVI2, GLI, GNDVI, MSAVI, NDVI, NDWI, NDYI

## How to Use It

The datasets share common date and site identifiers, so you can link ground observations to climate records, satellite imagery, and citizen science labels for the same time periods.

Practical starting points:
- Cross-reference ground phenology observations with climate data to analyze how weather drives flowering or fruiting timing
- Compare citizen science classifications against ground-truth field observations to assess volunteer labeling accuracy
- Use satellite-derived vegetation indices alongside ground phenology to validate remote sensing approaches to phenological monitoring
- Integrate traditional ecological knowledge calendars with measured data to evaluate community-reported seasonal patterns

**Data notes:** Missing values appear as "NA - no data" across the ground datasets. Tree crown visibility is recorded per observation, which affects observation reliability. Dates in the ground phenology file use DD/MM/YYYY format. Satellite vegetation indices are stored as int16 values scaled by 10,000.

## License

Creative Commons Attribution 4.0 International (CC BY 4.0).

Sources: https://zenodo.org/records/15704554, https://doi.org/10.4121/d97e338b-dc94-4e3d-a473-6dd3d4b48898.v1, https://doi.org/10.4121/9e6b4bca-f3d3-40f3-a8f5-4f71f7790c2f.v1, https://doi.org/10.4121/7e6d7ca3-060d-4ca5-bd83-d779b598c11d.v1
