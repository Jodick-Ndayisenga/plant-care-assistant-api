import os
import google.generativeai as genai
from celery import shared_task
from django.conf import settings
from .models import Diagnostic, Message

@shared_task
def analyze_plant_image(diagnostic_id):
    """Analyze plant image using AI model and update diagnostic results."""
    try:
        diagnostic = Diagnostic.objects.get(id=diagnostic_id)
        diagnostic.status = 'processing'
        diagnostic.save()

        # TODO: Load and preprocess image
        # image_path = diagnostic.image.path
        # preprocessed_image = preprocess_image(image_path)

        # TODO: Load AI model and make prediction
        # model = load_model(os.path.join(settings.MODEL_PATH, 'plant_disease_model.h5'))
        # prediction = model.predict(preprocessed_image)

        # For now, return dummy result
        result = {
            'disease_detected': True,
            'disease_name': 'Example Disease',
            'confidence': 0.95,
            'recommendations': [
                'Apply organic fungicide',
                'Improve air circulation',
                'Reduce watering frequency'
            ]
        }

        diagnostic.result = result
        diagnostic.status = 'completed'
        diagnostic.save()

    except Exception as e:
        if diagnostic:
            diagnostic.status = 'failed'
            diagnostic.result = {'error': str(e)}
            diagnostic.save()
        raise

@shared_task
def generate_ai_response(message_id, conversation_id):
    """Generate AI response using Google Gemini API."""
    try:
        message = Message.objects.get(id=message_id)
        conversation = message.conversation

        # Configure Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        # Get conversation history
        history = Message.objects.filter(
            conversation=conversation
        ).order_by('created_at')[:5]  # Get last 5 messages for context

        # Format conversation history
        chat_history = [{
            'role': msg.role,
            'content': msg.content
        } for msg in history]

        # Generate response
        response = model.generate_content({
            'contents': chat_history,
            'generation_config': {
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40
            }
        })

        # Create AI response message
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response.text
        )

    except Exception as e:
        # Create error message
        Message.objects.create(
            conversation=conversation,
            role='system',
            content=f'Error generating response: {str(e)}'
        )
        raise

@shared_task
def generate_plant_recommendation(recommendation_id):
    """Generate plant care recommendations based on conditions."""
    try:
        from .models import Recommendation
        recommendation = Recommendation.objects.get(id=recommendation_id)

        # TODO: Implement recommendation logic based on:
        # - Plant type
        # - Soil type
        # - Climate
        # - Season

        # For now, return dummy recommendation
        recommendation.recommendation = (
            f"Based on the {recommendation.soil_type.name} soil, "
            f"{recommendation.climate.name} climate, and {recommendation.season} season, "
            f"we recommend the following care routine for your {recommendation.plant_type.name}:\n\n"
            "1. Water twice a week\n"
            "2. Provide partial shade\n"
            "3. Fertilize monthly"
        )
        recommendation.confidence_score = 0.85
        recommendation.save()

    except Exception as e:
        if recommendation:
            recommendation.recommendation = f'Error generating recommendation: {str(e)}'
            recommendation.confidence_score = 0
            recommendation.save()
        raise