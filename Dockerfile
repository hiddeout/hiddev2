FROM python:3.9

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy bot files
COPY . .

# Expose the port the bot listens on (if necessary)
EXPOSE 8080

# Command to run the bot
CMD ["python", "main.py"]
