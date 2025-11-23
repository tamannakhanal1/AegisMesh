FROM python:3.11-slim
WORKDIR /app
COPY app.py /app/
RUN pip install flask requests
ENV FLASK_APP=app.py
CMD ["python", "app.py"]
