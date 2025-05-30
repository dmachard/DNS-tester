# 🛠️ Contributing

Contributions are welcome and appreciated! Whether it's fixing a bug, improving documentation, adding a feature, or enhancing tests

Before opening a pull request, please read the following guidelines to ensure smooth collaboration.

## 🏗️ Architecture
- **API Layer**: FastAPI REST endpoints
- **Task Queue**: Redis + Celery for async processing
- **CLI**: Direct interface for testing and automation
- **Monitoring**: Built-in Prometheus metrics

## ✅ Contribution Guidelines

- Keep the project backward compatible and follow existing code conventions.
- Add unit tests for any new features, bug fixes, or important logic changes.
- Make sure the project still passes all existing tests:
- Document any relevant changes, especially for new CLI options or API endpoints.
- Use descriptive commit messages and clean up the history before submitting your PR.

## 🐳 Running the Dev Environment with Docker

To run the development version of the stack using the docker-compose.dev.yml file (includes building images locally):

```bash
sudo docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

This will:
- Build the API and CLI images from your local source code
- Start Redis and other dependencies
- Mount the source code for live development (if volumes are defined)

## 🔬 Running Unit Tests

To run the test suite locally:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
pytest tests/ -v