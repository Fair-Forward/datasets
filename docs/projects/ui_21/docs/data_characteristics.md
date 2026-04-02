[Auto-enriched from linked project resources]

Weather data pipeline for rural Kenya. Fetches readings from the Wireless Planet API (api.wirelessplanet.co.ke) every 3 hours. License: MIT. Data Type: Time-series weather readings. Processing: Apache Spark 3.3.0 structured streaming with data cleaning, mean-based imputation, and Z-score anomaly detection (threshold: 10.0). Storage: PostgreSQL 14 (raw table: weather_raw; processed table: weather_clean with device_id, date, temperature, wind, precipitation, anomaly flags). Throughput: ~40-50 records/second, <30 seconds end-to-end latency. Daily aggregation compresses ~1,000 raw readings into ~35 daily summaries. Requires Docker, 8GB+ RAM, and a weather API account.

Source: https://github.com/iLab-DSU/imarika-weather-pipeline
