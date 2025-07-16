from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from tensorflow.keras.models import load_model
from PIL import Image
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import numpy as np
import tensorflow as tf
import joblib
import os
from django.conf import settings
from .tasks import analyze_plant_image, generate_crop_recommendation, generate_fertilizer_recommendation


def preprocess_image(uploaded_image, target_size=(300, 300)):
    img = Image.open(uploaded_image).convert('RGB')  # Convert to RGB (drops alpha channel)
    img = img.resize(target_size)  # Resize to model input size
    img_array = np.array(img)  # shape: (300, 300, 3)
    # Optional normalization: img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    return img_array



from .models import (
    PlantType, SoilType, Climate, Diagnostic,
    Conversation, Message, Recommendation, CropRecommendation, FertilizerRecommendation
)
from .serializers import (
    UserSerializer, PlantTypeSerializer, SoilTypeSerializer,
    ClimateSerializer, DiagnosticSerializer, ConversationSerializer,
    MessageSerializer, CropRecommendationSerializer, FertilizerRecommendationSerializer, LoginSerializer, DetectDiseaseSerializer
)


# --- User ViewSet ---
class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    @extend_schema(
        description="Get current logged-in user's profile",
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class LoginViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'full_name': {'type': 'string'},
                            'role': {'type': 'string'},
                            'phoneNumber': {'type': 'string'},
                            'province': {'type': 'string'},
                        }
                    }
                }
            }
        }
    )
    def create(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_user_model().objects.filter(username=serializer.validated_data['username']).first()
        if user and user.check_password(serializer.validated_data['password']):
            token_serializer = TokenObtainPairSerializer(data=request.data)
            token_serializer.is_valid(raise_exception=True)

            # You can customize these fields as needed
            user_data = {
                'id': user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": getattr(user, "role", "N/A") ,
                "phoneNumber": user.phone_number,
                "province": user.province
            }

            return Response({
                "access": token_serializer.validated_data["access"],
                "refresh": token_serializer.validated_data["refresh"],
                "user": user_data
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


# --- PlantType ViewSet ---
class PlantTypeViewSet(viewsets.ModelViewSet):
    queryset = PlantType.objects.all()
    serializer_class = PlantTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'scientific_name']
    ordering_fields = ['name', 'created_at']


# --- SoilType ViewSet ---
class SoilTypeViewSet(viewsets.ModelViewSet):
    queryset = SoilType.objects.all()
    serializer_class = SoilTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


# --- Climate ViewSet ---
class ClimateViewSet(viewsets.ModelViewSet):
    queryset = Climate.objects.all()
    serializer_class = ClimateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


# --- Diagnostic ViewSet ---
class DiagnosticViewSet(viewsets.ModelViewSet):
    serializer_class = DiagnosticSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status']
    parser_classes = [MultiPartParser, FormParser]  # to handle image upload

    def get_queryset(self):
        return Diagnostic.objects.filter(user=self.request.user)

    @extend_schema(
        description='Upload a plant image for disease analysis; starts async processing.',
        request=DiagnosticSerializer,
        responses={201: DiagnosticSerializer}
    )
    def create(self, request, *args, **kwargs):
        # Expecting an image file in request.data['image'] and possibly other fields
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Save Diagnostic with status = processing
        diagnostic = serializer.save(user=request.user, status='processing')

        # Trigger Celery async task with diagnostic id
        analyze_plant_image.delay(diagnostic.id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        description='Get diagnostic details including current status and results.',
        responses={200: DiagnosticSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        description='Optionally trigger re-analysis on an existing diagnostic (if needed).',
        responses={202: {'description': 'Re-analysis started'}}
    )
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        diagnostic = self.get_object()

        if diagnostic.status == 'processing':
            return Response({'detail': 'Analysis is already in progress.'}, status=status.HTTP_409_CONFLICT)

        diagnostic.status = 'processing'
        diagnostic.result = None  # clear previous result if any
        diagnostic.save()

        analyze_plant_image.delay(diagnostic.id)

        return Response({'status': 'Re-analysis started'}, status=status.HTTP_202_ACCEPTED)
# --- Conversation ViewSet ---
class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at']

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --- Message ViewSet (nested under conversation) ---
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(conversation_id=self.kwargs.get('conversation_pk'))

    def perform_create(self, serializer):
        serializer.save(conversation_id=self.kwargs.get('conversation_pk'))

    @extend_schema(
        description='Get AI response (mocked)',
        responses={200: MessageSerializer}
    )
    @action(detail=True, methods=['post'])
    def get_ai_response(self, request, pk=None, conversation_pk=None):
        # Mocked assistant response
        ai_response = Message.objects.create(
            conversation_id=conversation_pk,
            role='assistant',
            content='This is a mock AI response.'
        )
        return Response(self.get_serializer(ai_response).data, status=status.HTTP_201_CREATED)


# --- Crop Recommendation ViewSet ---

class CropRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = CropRecommendationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']

    def get_queryset(self):
        return CropRecommendation.objects.filter(user=self.request.user)

    @extend_schema(
        description='Generate a crop recommendation based on input data.',
        responses={200: CropRecommendationSerializer}
    )
    @action(detail=False, methods=['post'])
    def generate(self, request):
        # Real logic goes here — this is just a placeholder
        # e.g., image analysis or soil data processing
        # For now, simulate creation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recommendation = serializer.save()
        return Response(self.get_serializer(recommendation).data, status=status.HTTP_201_CREATED)

# --- Fertilizer Recommendation ViewSet ---

class FertilizerRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = FertilizerRecommendationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']

    def get_queryset(self):
        return FertilizerRecommendation.objects.filter(user=self.request.user)

    @extend_schema(
        description='Generate a fertilizer recommendation based on input data.',
        responses={200: FertilizerRecommendationSerializer}
    )
    @action(detail=False, methods=['post'])
    def generate(self, request):
        # Again, replace with real model/logic
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recommendation = serializer.save()
        return Response(self.get_serializer(recommendation).data, status=status.HTTP_201_CREATED)

class MLModelViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
    description='Predict plant disease from image',
    request=DetectDiseaseSerializer,
    responses={200: {'description': 'Prediction results'}}
    )
    @action(detail=False, methods=['post'])
    def predict_disease(self, request):
        try:
            # Load the model
            model_path = os.path.join(settings.ML_MODELS_PATH, 'best_model.keras')
            model = load_model(model_path)

            # Get image from request
            image = request.FILES.get('image')
            if not image:
                return Response({'error': 'Image file is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Preprocess image and make prediction
            preprocessed_image = preprocess_image(image)
            prediction = model.predict(preprocessed_image)

            # Interpret prediction
            predicted_class = int(np.argmax(prediction))  # or use your label mapping if available
            confidence = float(np.max(prediction))
            #{'Potato___Early_blight': 0, 'Potato___Late_blight': 1, 'Potato___healthy': 2}
            print(f'Predicted class: {predicted_class}, Confidence: {confidence}')

            return Response({
                'status': 'success',
                'predicted_class': predicted_class,
                'confidence': round(confidence, 4)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    @extend_schema(
        description='Get crop recommendation',
        request={
            'type': 'object',
            'properties': {
                'soil_type': {'type': 'string'},
                'climate': {'type': 'string'},
                'season': {'type': 'string'}
            }
        },
        responses={200: {'description': 'Recommended crops'}}
    )
    @action(detail=False, methods=['post'])
    def recommend_crop(self, request):
        try:
            
            model_path = os.path.join(settings.ML_MODELS_PATH, 'crop_recom.joblib')
            model = joblib.load(model_path)
            # Process input and make prediction
            return Response({'status': 'success', 'recommendation': 'example'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Get fertilizer recommendation',
        request={
            'type': 'object',
            'properties': {
                'soil_type': {'type': 'string'},
                'crop_type': {'type': 'string'}
            }
        },
        responses={200: {'description': 'Recommended fertilizer'}}
    )
    @action(detail=False, methods=['post'])
    def recommend_fertilizer(self, request):
        try:
            model_path = os.path.join(settings.ML_MODELS_PATH, 'fertilizer_recom.pkl')
            model = joblib.load(model_path)
            # Process input and make prediction
            return Response({'status': 'success', 'recommendation': 'example'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
