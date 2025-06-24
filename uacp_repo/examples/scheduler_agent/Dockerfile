FROM python:3.11-slim
WORKDIR /app
COPY . .
COPY ../../uacp_sdk /uacp_sdk
RUN pip install /uacp_sdk && pip install -r requirements.txt
CMD ["python", "app.py"]