FROM python:3.11-slim

WORKDIR /app

ARG REQUIREMENTS_FILE=requirements/base.txt

COPY requirements requirements
RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE}

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
