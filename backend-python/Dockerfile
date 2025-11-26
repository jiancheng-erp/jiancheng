# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set working directory INSIDE the container
WORKDIR /app/backend-python

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Copy only backend files into the container
COPY backend-python/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose Gunicorn port
EXPOSE 8000

# Run Gunicorn (with logging piped into app.log)
CMD gunicorn --bind 0.0.0.0:8000 --timeout 60 wsgi:app --access-logfile - --error-logfile -
# CMD python3 main.py
# \
#      2>&1 | tee -a app.log