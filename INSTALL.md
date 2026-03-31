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

---

## 5. Testing the API
Once the containers are running, you can test the following endpoints:

-   **Welcome**: `GET http://localhost:8000/`
-   **Database**: `GET http://localhost:8000/api/v1/utils/test-db`
-   **Ollama**: `GET http://localhost:8000/api/v1/utils/test-ollama`
-   **LLM test**: `GET http://localhost:8000/api/v1/llm/test-llm?model=llama3`

## 6. Development (without Docker)
If you prefer running the backend locally for faster iteration:

1.  **Start Infrastructure Only**:
    If you don't want to run the backend in Docker but need the DB and MinIO:
    ```bash
    docker compose up db minio -d
    ```

2.  **Setup Virtual Environment**:
    Navigate to the `backend` folder and create a venv:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run with Hot-Reload**:
    Start Uvicorn from the `backend` directory:
    ```bash
    uvicorn main:app --reload
    ```
    > [!TIP]
    > Since the backend code expects the `.env` file to be in the root directory, ensure you have followed Step 2.
