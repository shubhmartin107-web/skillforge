FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir skillforge[all]

EXPOSE 7860

CMD ["skillforge", "dashboard"]
