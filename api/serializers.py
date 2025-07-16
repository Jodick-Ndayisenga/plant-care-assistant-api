from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PlantType, SoilType, Climate, Diagnostic, Conversation, Message, CropRecommendation, FertilizerRecommendation, Recommendation

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'full_name', 'phone_number', 'province', 'password', 'role')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 5},
            'role': {'read_only': True},  # Optional: prevent setting on registration
        }


    def to_internal_value(self, data):
        # Clean phone number before validation
        phone = data.get('phone_number')
        if phone:
            # Remove spaces, dashes, dots, and parentheses
            cleaned_phone = (
                phone.replace(" ", "")
                     .replace("-", "")
                     .replace("(", "")
                     .replace(")", "")
                     .replace(".", "")
            )
            data['phone_number'] = cleaned_phone
        return super().to_internal_value(data)
    

    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = get_user_model().objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class PlantTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantType
        fields = '__all__'

class SoilTypeSerializer(serializers.ModelSerializer):
    suitable_plants = PlantTypeSerializer(many=True, read_only=True)

    class Meta:
        model = SoilType
        fields = '__all__'

class ClimateSerializer(serializers.ModelSerializer):
    suitable_plants = PlantTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Climate
        fields = '__all__'

class DiagnosticSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plant_type = PlantTypeSerializer(read_only=True)
    plant_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PlantType.objects.all(),
        write_only=True
    )

    class Meta:
        model = Diagnostic
        fields = '__all__'
        read_only_fields = ('status', 'result')

    def validate_image(self, value):
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError('Image size should not exceed 10MB')
        return value

    def create(self, validated_data):
        plant_type = validated_data.pop('plant_type_id')
        return Diagnostic.objects.create(
            user=self.context['request'].user,
            plant_type=plant_type,
            **validated_data
        )

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('role', 'created_at')


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = '__all__'

    def create(self, validated_data):
        return Conversation.objects.create(
            user=self.context['request'].user,
            **validated_data
        )



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()



class DetectDiseaseSerializer(serializers.Serializer):
    image = serializers.ImageField()



class DiagnosticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnostic
        fields = '__all__'
        read_only_fields = ('user', 'status', 'result')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CropRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropRecommendation
        fields = '__all__'
        read_only_fields = (
            'user',
            'predicted_label',
            'predicted_crop',
            'confidence_score',
            'explanation'
        )

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class FertilizerRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FertilizerRecommendation
        fields = '__all__'
        read_only_fields = (
            'user',
            'predicted_label',
            'predicted_fertilizer',
            'confidence_score',
            'explanation'
        )

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
