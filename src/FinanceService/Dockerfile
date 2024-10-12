# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the ports the FinanceService will run on (HTTP and WebSocket)
EXPOSE 5003
EXPOSE 5001

# Run the app on container start, with both HTTP and WebSocket ports
CMD ["python", "app.py", "5003", "5001"]
