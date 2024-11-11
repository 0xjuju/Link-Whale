# Version
FROM python:3.11

# Set env variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working dir
WORKDIR /app


# Dependencies
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy proejct
COPY . /app/

# Django Port
EXPOSE 8000

# Run Django server
CMD ["gunicorn", "--bind", ":8000", "_settings.wsgi:application"]





