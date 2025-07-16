import os
from celery import shared_task
from django.conf import settings
from .models import Diagnostic, Message, Recommendation, FertilizerRecommendation, CropRecommendation
import pickle
import joblib
import json
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from PIL import Image
import numpy as np
from .gemini import get_gemini_response
import asyncio
# Label mappings (add more if needed)
with open(settings.CROP_LABELS_PATH, 'r') as f:
    CROP_LABELS = json.load(f)

CROP_NAME_TO_IDX = {v.lower(): int(k) for k, v in CROP_LABELS.items()}


with open(settings.FERTILIZER_LABELS_PATH, 'r') as f:
    FERTILIZER_LABELS = json.load(f)

SOIL_TYPE_MAPPING = {
    "sandy": 0, "loamy": 1, "black": 2, "red": 3, "clayey": 4
    # Update to match training data
}


#CROP MODEL IN .joblib format
# Load crop prediction model (joblib)
try:
    CROP_MODEL = joblib.load(settings.CROP_MODEL_PATH)
except Exception as e:
    CROP_MODEL = None
    print(f"Error loading crop model: {e}")

# Load fertilizer prediction model (pickle)
try:
    with open(settings.FERTILIZER_MODEL_PATH, 'rb') as f:
        FERTILIZER_MODEL = pickle.load(f)
except Exception as e:
    FERTILIZER_MODEL = None
    print(f"Error loading fertilizer model: {e}")

# Load disease model (keras)
try:
    DISEASE_MODEL = load_model(settings.DISEASE_MODEL_PATH)
except Exception as e:
    DISEASE_MODEL = None
    print(f"Error loading disease model: {e}")

def preprocess_image(uploaded_image, target_size=(300, 300)):
    img = Image.open(uploaded_image).convert('RGB')  # Convert to RGB (drops alpha channel)
    img = img.resize(target_size)  # Resize to model input size
    img_array = np.array(img)  # shape: (300, 300, 3)
    # Optional normalization: img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    return img_array

import asyncio  # 👈 To run async code in sync task

@shared_task
def analyze_plant_image(diagnostic_id):
    diagnostic = None
    try:
        diagnostic = Diagnostic.objects.get(id=diagnostic_id)
        diagnostic.status = 'processing'
        diagnostic.save()

        if DISEASE_MODEL is None:
            raise Exception("Le modèle de détection des maladies n'est pas chargé.")

        # Step 1: Preprocess image
        image_array = preprocess_image(diagnostic.image.path)

        # Step 2: Predict disease
        preds = DISEASE_MODEL.predict(image_array)
        predicted_label = int(np.argmax(preds, axis=1)[0])
        confidence = float(preds[0][predicted_label])

        # Step 3: Map prediction to disease name
        DISEASE_LABELS = {
            0: "Early Blight",
            1: "Late Blight",
            2: "Healthy"
        }
        disease_name = DISEASE_LABELS.get(predicted_label, "Inconnu")

        # Step 4: Create Gemini prompt (in French)
        prompt = (
            f"Une plante a été analysée via une image. Le modèle a détecté la maladie '{disease_name}' "
            f"avec une confiance de {round(confidence * 100, 2)}%. "
        )

        if disease_name != "Healthy":
            prompt += (
                "Donne une explication brève sur cette maladie, ses symptômes, et recommande des traitements appropriés. "
                "Formule la réponse en français clair et simple."
            )
        else:
            prompt += (
                "La plante semble saine. Fournis un conseil pour maintenir sa santé. "
                "Formule la réponse en français."
            )

        # Step 5: Call Gemini async function inside sync task
        gemini_response = asyncio.run(get_gemini_response(
            user_message=prompt,
            chat_history=None,
            model_name="gemini-2.5-flash"
        ))

        # Step 6: Build result
        result = {
            'disease_detected': disease_name != "Healthy",
            'disease_name': disease_name,
            'confidence': confidence,
            'recommendations': [],
            'explanation': gemini_response
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
def generate_fertilizer_recommendation(fertilizer_id):
    fertilizer = None

    try:
        # Step 1: Retrieve the record
        fertilizer = FertilizerRecommendation.objects.get(id=fertilizer_id)
        fertilizer.status = 'processing'
        fertilizer.save()

        # Step 2: Ensure model is loaded
        if FERTILIZER_MODEL is None:
            raise Exception("Le modèle de fertilisant n'est pas chargé.")

        # Step 3: Encode categorical fields
        soil_index = SOIL_TYPE_MAPPING.get(fertilizer.soil_type.name.lower(), 0)
        crop_index = CROP_NAME_TO_IDX.get(fertilizer.crop.name.lower(), 0)

        # Step 4: Prepare features in the expected order
        features = np.array([[
            fertilizer.temperature,
            fertilizer.humidity,
            fertilizer.moisture,
            soil_index,
            crop_index,
            fertilizer.nitrogen,
            fertilizer.potassium,
            fertilizer.phosphorus
        ]])

        # Step 5: Predict
        preds = FERTILIZER_MODEL.predict(features)

        if preds.ndim == 2:
            predicted_label = int(np.argmax(preds, axis=1)[0])
            confidence = float(preds[0][predicted_label])
        else:
            predicted_label = int(preds[0])
            confidence = 1.0

        predicted_fertilizer = FERTILIZER_LABELS.get(str(predicted_label), "Inconnu")

        # Step 6: Generate French explanation using Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")

        french_prompt = (
            f"L'utilisateur cultive {fertilizer.crop.name} sur un sol de type {fertilizer.soil_type.name}. "
            f"Les conditions sont les suivantes : température = {fertilizer.temperature}°C, humidité = {fertilizer.humidity}%, "
            f"humidité du sol = {fertilizer.moisture}%, azote (N) = {fertilizer.nitrogen}, phosphore (P) = {fertilizer.phosphorus}, "
            f"potassium (K) = {fertilizer.potassium}. Le modèle a recommandé le fertilisant '{predicted_fertilizer}'. "
            f"Explique pourquoi ce choix est adapté aux conditions données, en français simple."
        )

        gemini_response = model.generate_content(french_prompt)

        # Step 7: Save results
        fertilizer.predicted_label = predicted_label
        fertilizer.predicted_fertilizer = predicted_fertilizer
        fertilizer.confidence_score = confidence
        fertilizer.explanation = gemini_response.text
        fertilizer.status = 'completed'
        fertilizer.save()

    except Exception as e:
        if fertilizer:
            fertilizer.status = 'failed'
            fertilizer.explanation = f"Erreur lors de la génération : {str(e)}"
            fertilizer.confidence_score = 0
            fertilizer.save()
        raise

@shared_task
def generate_crop_recommendation(crop_id):
    crop_rec = None
    try:
        crop_rec = CropRecommendation.objects.get(id=crop_id)
        crop_rec.status = 'processing'
        crop_rec.save()

        if CROP_MODEL is None:
            raise Exception("Crop model not loaded")

        features = np.array([[
            crop_rec.nitrogen,
            crop_rec.phosphorus,
            crop_rec.potassium,
            crop_rec.temperature,
            crop_rec.humidity,
            crop_rec.ph,
            crop_rec.rainfall
        ]])

        preds = CROP_MODEL.predict(features)

        if preds.ndim == 2:
            predicted_label = int(np.argmax(preds, axis=1)[0])
            confidence = float(preds[0][predicted_label])
        else:
            predicted_label = int(preds[0])
            confidence = 1.0

        predicted_crop = CROP_LABELS.get(str(predicted_label), "Inconnu")

        # 🇫🇷 Prompt Gemini in French
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")
        french_prompt = (
            f"L'utilisateur a fourni les données suivantes concernant les conditions du sol et du climat : "
            f"Azote (N) = {crop_rec.nitrogen}, Phosphore (P) = {crop_rec.phosphorus}, Potassium (K) = {crop_rec.potassium}, "
            f"Température = {crop_rec.temperature}°C, Humidité = {crop_rec.humidity}%, pH = {crop_rec.ph}, Pluviométrie = {crop_rec.rainfall} mm. "
            f"Sur cette base, le modèle a prédit que la culture la plus adaptée est : '{predicted_crop}'. "
            f"Expliquez pourquoi cette culture est un bon choix pour ces conditions, en français simple."
        )

        gemini_response = model.generate_content(french_prompt)

        crop_rec.predicted_label = predicted_label
        crop_rec.predicted_crop = predicted_crop
        crop_rec.confidence_score = confidence
        crop_rec.explanation = gemini_response.text
        crop_rec.status = 'completed'
        crop_rec.save()

    except Exception as e:
        if crop_rec:
            crop_rec.status = 'failed'
            crop_rec.explanation = f"Erreur lors de la génération : {str(e)}"
            crop_rec.confidence_score = 0
            crop_rec.save()
        raise

@shared_task
def generate_ai_response(message_id, conversation_id):
    try:
        message = Message.objects.get(id=message_id)
        conversation = message.conversation

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        history = Message.objects.filter(conversation=conversation).order_by('created_at')[:5]

        chat_history = [{'role': msg.role, 'content': msg.content} for msg in history]

        response = model.generate_content({
            'contents': chat_history,
            'generation_config': {
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40
            }
        })

        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response.text
        )

    except Exception as e:
        Message.objects.create(
            conversation=conversation,
            role='system',
            content=f'Error generating response: {str(e)}'
        )
        raise
