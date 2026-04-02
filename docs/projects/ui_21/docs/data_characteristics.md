[Auto-enriched from linked project resources]

IMARIKA is a project by Strathmore University’s iLabAfrica that focuses on providing accurate, local weather information to farmers in rural Kenya. The dataset generated through this project is designed to help small-holder farmers receive location-specific weather guidance, moving away from generic information.

The dataset includes real-time weather data that is processed through a pipeline. It fetches data from an external weather API every three hours and processes it using Apache Spark. The data is cleaned, validated, and stored in PostgreSQL, with both raw and processed versions available. Key features of the dataset include:

- **Real-time Data Ingestion**: Weather data is updated every three hours.
- **Data Processing**: The pipeline includes data cleaning, mean-based imputation for missing values, and anomaly detection using Z-scores.
- **Daily Aggregation**: The dataset provides daily summaries and statistics of weather conditions.

While the dataset is robust, there may be limitations related to the accuracy of the external weather API and potential biases in the data collection process, which could affect the reliability of the recommendations made to farmers.

To ensure responsible and ethical use, the project emphasizes data quality through comprehensive cleaning and validation processes. Users are encouraged to follow ethical guidelines when utilizing the data for advisory services.

The dataset is maintained and updated by the iLabAfrica team at Strathmore University. Users interested in accessing the data will need to create an account with the weather API used in the project, which is a prerequisite for running the data processing pipeline.

The dataset is published under a license that allows users to access and reuse the data, but specific rights and restrictions should be confirmed by reviewing the licensing terms provided in the project documentation.

Source: https://github.com/iLab-DSU/imarika-weather-pipeline, https://github.com/iLab-DSU/Agricultural-Recommendations-Chat
