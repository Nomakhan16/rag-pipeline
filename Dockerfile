FROM python:3.10-slim

WORKDIR /app

# Install all required packages
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==1.10.12 \
    python-dotenv==1.0.0 \
    python-multipart==0.0.6 

COPY . .

RUN mkdir -p chroma_db uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]