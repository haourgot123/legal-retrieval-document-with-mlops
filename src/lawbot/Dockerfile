# Use official Python base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .
COPY .env .env

# Expose port
EXPOSE 30000

# Command to run the app
CMD ["uvicorn", "chat_api:app", "--host", "0.0.0.0", "--port", "30000", "--reload"]
