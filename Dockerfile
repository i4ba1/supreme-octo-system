FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=eatsight.settings.production

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create media and static directories
RUN mkdir -p /app/media/qrcodes
RUN mkdir -p /app/static

# Run commands
CMD ["uvicorn", "eatsight.asgi:application", "--host", "0.0.0.0", "--port", "8000"]