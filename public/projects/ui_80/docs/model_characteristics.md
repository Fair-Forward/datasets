[Auto-enriched from linked project resources]

The project focuses on improving solar energy planning in Sub-Saharan Africa, particularly in Uganda, by using an AI model to predict solar irradiance. In simple terms, the model takes satellite data that often overestimates solar potential and corrects it to provide more accurate and reliable information about solar energy availability.

The input for the model includes satellite-derived solar irradiation data from sources like NASA and CAMS, along with ground measurements collected from various sites in Uganda. The output is a corrected estimate of daily Global Horizontal Irradiance (GHI), which is crucial for making informed decisions about solar energy projects.

One known limitation is that the model is specifically tuned for Uganda's unique climate and topography, which means it may not be as effective in other regions without further adjustments. Additionally, there may be biases in the training data that could affect predictions, so users should be aware of the context in which the data is applied.

To ensure responsible AI use, the project has taken steps to validate the model against ground truth data from multiple sites across Uganda, achieving a high accuracy score (R² of 0.86). This validation helps to minimize risks associated with using inaccurate satellite data.

The platform is designed to be user-friendly, featuring interactive visualizations and an API for easy integration into other applications. Users can access historical datasets on demand, making it a practical tool for energy professionals.

Source: https://github.com/Marconi-Lab/Solar_irradiation, https://irradiation-portal-55883164704.europe-west1.run.app/, https://github.com/Marconi-Lab/Irradiation_Portal
