[Auto-enriched from linked project resources]

## Using the Solar Irradiance Portal

The Irradiation Portal is a web application that provides corrected solar irradiance data for Uganda. It addresses systematic overestimation in standard satellite data sources (such as CAMS and NASA POWER) by applying a Random Forest machine learning model trained on ground-truth measurements from 56 validation sites across Uganda and 7 African countries. The model achieves an R-squared accuracy of 0.86.

Access the portal at: https://irradiation-portal-55883164704.europe-west1.run.app/

The portal offers three main access points:
- `/portal` -- interactive data exploration with dynamic charts and maps
- `/documentation` -- technical guidance on the data and methodology
- `/help` -- user support

A RESTful API is available for integrating the corrected solar data into your own applications.

## Using the SuSSE Python Package

The underlying model code is available as the SuSSE (Sub-Saharan Solar Estimation) Python package on GitHub.

**Installation:**

```bash
pip install .
```

Or for development (changes to source code are reflected immediately):

```bash
pip install -e .
```

The repository includes Jupyter Notebooks (87.9% of the codebase) and Python scripts (12.1%). Testing and code quality are managed through Tox:

- `tox -e py312` -- run tests with coverage
- `tox -e format-code` -- apply formatting
- `tox -e static-analysis` -- run type checking

## What the Portal Provides

- Corrected Global Horizontal Irradiance (GHI) data that accounts for roughly 20% satellite overestimation
- Monthly irradiance measurements (kWh/m2/day)
- Interactive visualizations for analyzing solar patterns
- Historical data access through the web interface

## Why This Matters

Standard satellite solar data can overestimate irradiance for Uganda, which reduces lifetime energy savings for consumers by 5-20% and creates financial risk through incorrect system sizing. The corrected data from this portal helps with more accurate solar potential assessment and system design.

Sources:
- https://github.com/Marconi-Lab/Solar_irradiation
- https://irradiation-portal-55883164704.europe-west1.run.app/
