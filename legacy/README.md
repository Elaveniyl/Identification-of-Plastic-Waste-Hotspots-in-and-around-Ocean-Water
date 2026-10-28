# Legacy Scripts Archive

This directory preserves the historical standalone scripts and experimental entry points from the original project prototype. They have been archived to maintain repository hygiene while preserving the complete evolutionary history of the codebase.

## Archived Components

### 1. Model Inference Scripts
- **prediction.py**:
  - *Original Purpose*: Loaded 	f_files/retrained_graph.pb and etrained_labels.txt using TensorFlow 1.x 	f.GraphDef and 	f.Session on each function call. Used hardcoded relative paths and raw byte feeding into DecodeJpeg/contents:0.
  - *Modern Replacement*: Superseded by [prediction_service.py](../prediction_service.py), which uses a singleton PredictionService architecture, caches the TensorFlow session in memory, safely handles multiple image formats (JPEG, PNG, WebP) via PIL conversion, and exposes structured JSON results.
- **plastic_prediction.py**:
  - *Original Purpose*: Standalone command-line test script loading 	8.png.jpg and printing top classification scores.
  - *Modern Replacement*: Replaced by automated test suite [	ests/test_suite.py](../tests/test_suite.py) and the interactive web interface at /object.

### 2. External Integration & Sensor Scripts
- **irebase.py**:
  - *Original Purpose*: Script for synchronizing buoy/sensor observations with a remote Firebase Realtime Database using pyrebase and static credentials from env.py.
  - *Modern Status*: Archived to eliminate plaintext credential exposure. Modern persistence uses Flask-SQLAlchemy with SQLite (instance/contact.db).
- **service.py & service_localtest.py**:
  - *Original Purpose*: Prototype communication scripts for sending buoy telemetry and image data to a remote or local processing server.
  - *Modern Status*: Archived as the application now operates as a self-contained, high-performance Flask web platform with GIS and FLA modules.
- **	esting.py**:
  - *Original Purpose*: Unstructured scratchpad for running ad-hoc verification snippets.
  - *Modern Replacement*: Superseded by unit tests in 	ests/test_suite.py.
