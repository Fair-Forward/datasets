[Auto-enriched from linked project resources]

## Getting Started with VAYU OpenAir

VAYU OpenAir is a public repository of open software, open algorithms, and open data on air pollution collected through hyperlocal mapping in two Indian cities: Patna and Gurgaon. The project is a collaboration between UNDP, GIZ, Government of India, University of Nottingham, Development Alternatives, D-Coop, and citizen scientists across India.

### What Is Available

The VAYU OpenAir stack consists of three components, all open-source under an MIT license:

- **Mobile App** (React/TypeScript) -- for field-level data collection and viewing air quality readings.
- **Web Portal** (React) -- a dashboard for visualising air pollution data.
- **Backend API** (Django/Python) -- serves data to both the app and portal, backed by PostgreSQL, Redis, and Celery for task processing.

All source code is available at [github.com/undpindia/VAYU_OpenAir](https://github.com/undpindia/VAYU_OpenAir).

### Setting Up the Platform Locally

Prerequisites: Ubuntu 22.04 with build tools (gcc, g++, make), libsqlite3-dev, zlib1g-dev, Tippecanoe, Node.js v20.x, Redis server, Python 3.10, and PostgreSQL 15.

1. Clone the repository.
2. Set up the backend: create a Python virtual environment, install dependencies, run database migrations, and configure Celery services with systemd.
3. Build the mobile app and web portal separately following the instructions in each sub-directory.
4. Expose the applications through Nginx server blocks (backend via gunicorn, frontends as static files).

### Community-Built Tools on VAYU Data

Several open-source tools have been built on top of VAYU data:

- **vayu-gnn** (GPL-3.0) -- A Graph Neural Network that predicts hyperlocal air pollutant levels up to 8 hours ahead. It combines VAYU sensor readings with weather data (Open Meteo API), elevation, river distance, and urban density features. Each sensor is modelled as a node in a distance-weighted graph. Repository: [github.com/EconAIorg/vayu-gnn](https://github.com/EconAIorg/vayu-gnn)

- **VayuAssist** (MIT) -- A RAG-based chatbot for government policymakers that provides air quality insights, AQI trend analysis, and mitigation strategies. Built with Streamlit, Pathway (real-time data processing), and OpenAI GPT-3.5 Turbo. Requires Python 3.9+, a Dropbox account for data ingestion, and an OpenAI API key. Install via `pip install -r requirements.txt`, then run the backend (`python pathwayEngine.py`) and frontend (`streamlit run vayuassistUi.py`). Repository: [github.com/Alphawarrior21/VayuAssist](https://github.com/Alphawarrior21/VayuAssist)

- **ClearSky** -- A Jupyter Notebook project for predictive analysis of pollution with 3D visual graphics. Repository: [github.com/akbp24/ClearSky](https://github.com/akbp24/ClearSky)

- **vayu_airnode** (Apache-2.0) -- ARIMA time-series analysis notebooks for individual pollutants (CH4, CO, CO2, NO2, PM10, PM2.5) plus temperature and humidity, with a Streamlit app interface. Repository: [github.com/sherwaldeepesh/vayu_airnode](https://github.com/sherwaldeepesh/vayu_airnode)

Sources:
- https://vayu.undp.org.in/
- https://github.com/undpindia/VAYU_OpenAir
- https://github.com/EconAIorg/vayu-gnn/tree/main
- https://github.com/Alphawarrior21/VayuAssist
- https://github.com/akbp24/ClearSky
- https://github.com/sherwaldeepesh/vayu_airnode
