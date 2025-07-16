from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PlantType, SoilType, Climate, Diagnostic, Conversation, Message, Recommendation

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'full_name', 'phone_number', 'province', 'password', 'role')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 5},
            'role': {'read_only': True},  # Optional: prevent setting on registration
        }

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
        read_only_fields = ('conversation',)

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

class RecommendationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plant_type = PlantTypeSerializer(read_only=True)
    soil_type = SoilTypeSerializer(read_only=True)
    climate = ClimateSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = '__all__'
        read_only_fields = ('confidence_score',)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()



class DetectDiseaseSerializer(serializers.Serializer):
    image = serializers.ImageField()