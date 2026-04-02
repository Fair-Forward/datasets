[Auto-enriched from linked project resources]

## How to Use This Resource

This resource addresses a critical problem for solar energy planning in Uganda: standard satellite data sources such as CAMS and NASA POWER systematically overestimate solar irradiance by roughly 20%, which reduces lifetime energy savings for consumers by 5-20% and creates financial risk through incorrect system sizing. The Irradiation Portal provides corrected Global Horizontal Irradiance (GHI) data by applying a machine learning model trained on ground-truth measurements from 56 validation sites across Uganda and 7 African countries, achieving an R-squared accuracy of 0.86.

Anyone involved in solar project development, rural electrification planning, or energy policy in Uganda can access the corrected data through the [Irradiation Portal web application](https://irradiation-portal-55883164704.europe-west1.run.app/). The portal offers interactive data exploration with dynamic charts and maps, monthly irradiance measurements in kWh/m2/day, and historical data access -- all through a standard web browser. Technical documentation and user support are built into the portal.

For organisations that want to integrate the corrected solar data into their own planning tools or applications, a RESTful API is available through the portal. This enables automated data retrieval for feasibility studies, system design calculations, or monitoring dashboards.

Researchers and developers looking to extend the underlying methodology can access the SuSSE (Sub-Saharan Solar Estimation) model code, which is openly available on [GitHub](https://github.com/Marconi-Lab/Solar_irradiation). The repository includes the full codebase with Jupyter Notebooks and Python scripts, along with testing and development tools. This opens possibilities for adapting the correction model to other Sub-Saharan African countries where similar satellite overestimation issues exist.

Sources:
- https://github.com/Marconi-Lab/Solar_irradiation
- https://irradiation-portal-55883164704.europe-west1.run.app/
