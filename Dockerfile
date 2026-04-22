# Use Python 3.14 slim
FROM python:3.14-slim

# Install minimal build deps (for asyncpg / psycopg etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt


# Copy app code + alembic config
COPY . .

# Entrypoint runs migrations, then main command
ENTRYPOINT ["./docker-entrypoint.sh"]


# Expose FastAPI port
EXPOSE 8000

# Run the generated FastAPI app
CMD ["uvicorn", "openapi_server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]