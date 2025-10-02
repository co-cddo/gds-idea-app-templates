FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install streamlit python-jose requests

# Copy application
COPY src/ .

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK CMD curl --fail http://localhost:80/_stcore/health || exit 1

# Run streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "80"]
