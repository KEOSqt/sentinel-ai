FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Tests, pytest.ini and pyproject.toml are deliberately not copied: they are
# not needed at runtime and only inflate the image.
COPY app ./app

ENV SENTINEL_DATABASE_URL=sqlite:////data/sentinel.db \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Uses the /health alias so the check stays a single trivial response.
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]