# Installation Guide: VerbumLab

Follow these steps to set up and run the VerbumLab project.

## Prerequisites
-   **Git**: [Download Git](https://git-scm.com/)
-   **Docker & Docker Compose**: [Get Docker](https://docs.docker.com/get-docker/)
-   **Ollama** (if running LLMs locally): [Get Ollama](https://ollama.ai/)

---

## 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/your-repo/verbumlab.git
cd verbumlab
```

## 2. Environment Configuration
Copy the example environment file and adjust any settings if needed.
```bash
cp .env.example .env
```
> [!NOTE]
> If you are using **WSL**, update `OLLAMA_BASE_URL` in `.env` to the IP of your Windows host (e.g., `http://192.168.8.1:11434`).

## 3. Ollama Setup (Windows Host)
If Ollama is running on your Windows host, you must allow external connections from WSL:
1.  Set the environment variable `OLLAMA_HOST` to `0.0.0.0` on Windows.
2.  Restart the Ollama application.

## 4. Run with Docker Compose
Build and start all services (database, object storage, and backend).
```bash
docker compose up --build
```
> [!IMPORTANT]
> The `minio-init` service will automatically create the `verbumlab` bucket upon startup. You can monitor the logs with `docker compose logs -f minio-init` to verify success.

---

## 5. Database Migrations (Alembic)
After the database container is up, you **must** apply the latest database schema migrations.

### If running via Docker:
```bash
docker exec -it backend-vlab-01 alembic upgrade head
```

### If running locally:
```bash
cd backend
# Ensure your virtualenv is active
alembic upgrade head
```

---

## 6. Ollama Model Setup
The system requires specific models to be pulled into Ollama before use. Run these commands on your host machine (where Ollama is installed):

```bash
# For Embeddings
ollama pull mxbai-embed-large

# For Generation (Chat/RAG)
ollama pull qwen3:8b
```

---

## 7. Testing the API
Once the services are running and migrated, test the endpoints:

-   **Welcome**: `GET http://localhost:8000/`
-   **Database Check**: `GET http://localhost:8000/api/v1/utils/test-db`
-   **Ollama Check**: `GET http://localhost:8000/api/v1/utils/test-ollama`
-   **Chat (RAG)**: `POST http://localhost:8000/api/v1/chat/ask` with JSON `{"query": "..."}`

---

## 8. Development (Local Backend)
If you prefer running the backend locally for faster iteration:

1.  **Start Infrastructure Only**:
    ```bash
    docker compose up db minio minio-init -d
    ```

2.  **Setup Virtual Environment**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Run Migrations & Start**:
    ```bash
    alembic upgrade head
    uvicorn main:app --reload
    ```
