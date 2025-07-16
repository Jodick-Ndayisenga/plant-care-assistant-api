# Gardien Eveille - Plant Disease Detection API

A Django REST API for plant disease detection and management system that uses computer vision AI and conversational AI to help users identify and manage plant diseases.

## Features

- 🔍 Computer vision AI for plant disease detection
- 🔐 JWT-based authentication system
- 💬 AI-powered conversation system using Google Gemini
- 🌱 Plant type and advice management
- 🌍 Soil type and climate data management
- 📊 Diagnostic history tracking
- 🎯 Smart recommendation engine

## Technical Stack

- Python 3.9+
- Django 5.2+
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- TensorFlow/Keras
- Google Gemini API

## Prerequisites

- Python 3.9 or higher
- PostgreSQL
- Redis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gardien-eveille
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and configure your environment variables:
```env
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DB_NAME=gardien_eveille
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

## Running the Development Server

1. Start Redis server

2. Start Celery worker:
```bash
celery -A gardien_eveille worker -l info
```

3. Run the development server:
```bash
python manage.py runserver
```

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## API Endpoints

- Authentication:
  - POST `/api/token/` - Obtain JWT token
  - POST `/api/token/refresh/` - Refresh JWT token

- Users:
  - GET `/api/users/me/` - Get current user profile
  - POST `/api/users/` - Register new user

- Plant Types:
  - GET `/api/plant-types/` - List all plant types
  - POST `/api/plant-types/` - Create new plant type

- Diagnostics:
  - POST `/api/diagnostics/` - Create new diagnostic
  - POST `/api/diagnostics/{id}/analyze/` - Analyze plant disease

- Conversations:
  - GET `/api/conversations/` - List user conversations
  - POST `/api/conversations/{id}/messages/` - Send message
  - POST `/api/conversations/{id}/messages/{id}/get_ai_response/` - Get AI response

- Recommendations:
  - GET `/api/recommendations/` - List recommendations
  - POST `/api/recommendations/generate/` - Generate new recommendation

## Testing

Run the test suite:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.# plant-care-assistant-api
# plant-care-assistant-api
