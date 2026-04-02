[Auto-enriched from linked project resources]

VAYU OpenAir provides an end-to-end open-source platform for hyperlocal air pollution mapping, built through a collaboration between UNDP, GIZ, the Government of India, the University of Nottingham, Development Alternatives, D-Coop, and citizen scientists across India. The platform includes open data, open algorithms, and open software from hyperlocal mapping campaigns in Patna and Gurgaon.

The core platform consists of three components: a mobile app for field-level data collection and viewing air quality readings, a web portal dashboard for visualising pollution data, and a backend API serving data to both interfaces. All source code is available at github.com/undpindia/VAYU_OpenAir under an MIT license.

Practitioners can use VAYU OpenAir in several ways. If you are working on urban air quality in Indian cities or comparable contexts, you can deploy the existing platform to run your own hyperlocal mapping campaigns -- the mobile app supports citizen-science data collection, while the web portal provides ready-made visualisation tools for stakeholders and policymakers. If you already have air quality data and want to build predictive or analytical tools on top of it, several community-built open-source projects demonstrate what is possible:

- **vayu-gnn** -- A Graph Neural Network that predicts hyperlocal pollutant levels up to 8 hours ahead by combining VAYU sensor readings with weather data, elevation, river distance, and urban density features. Available under GPL-3.0 at github.com/EconAIorg/vayu-gnn.
- **VayuAssist** -- A RAG-based chatbot designed for government policymakers, providing air quality insights, AQI trend analysis, and mitigation strategies. Built with Streamlit and OpenAI GPT-3.5 Turbo. Available under MIT at github.com/Alphawarrior21/VayuAssist.
- **ClearSky** -- Jupyter Notebooks for predictive pollution analysis with 3D visualisation. Available at github.com/akbp24/ClearSky.
- **vayu_airnode** -- ARIMA time-series analysis for individual pollutants (CH4, CO, CO2, NO2, PM10, PM2.5) plus temperature and humidity, with a Streamlit interface. Available under Apache-2.0 at github.com/sherwaldeepesh/vayu_airnode.

These community tools illustrate concrete extension points: from short-term pollution forecasting to policy-support chatbots to time-series analysis of specific pollutants. Developers looking to extend the ecosystem can build on any of these as starting points.

Cost and resources: The platform and all community tools are open-source, so the primary costs are compute infrastructure for hosting the backend and any ML model training. Setup documentation is provided in each repository.

Sources:
- https://vayu.undp.org.in/
- https://github.com/undpindia/VAYU_OpenAir
- https://github.com/EconAIorg/vayu-gnn/tree/main
- https://github.com/Alphawarrior21/VayuAssist
- https://github.com/akbp24/ClearSky
- https://github.com/sherwaldeepesh/vayu_airnode