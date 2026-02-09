# Valve Datasheet Automation API
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY valve_datasheet_automation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY valve_datasheet_automation/ ./valve_datasheet_automation/
COPY unstructured/ ./unstructured/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "valve_datasheet_automation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
