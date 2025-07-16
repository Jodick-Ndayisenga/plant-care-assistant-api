from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.'
        )]
    )
    province = models.CharField(max_length=100)
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['-date_joined']

class PlantType(models.Model):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100)
    description = models.TextField()
    emoji = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.emoji} {self.name}"

class SoilType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    characteristics = models.JSONField()
    suitable_plants = models.ManyToManyField(PlantType, related_name='suitable_soils')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Climate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    temperature_range = models.CharField(max_length=50)
    rainfall_range = models.CharField(max_length=50)
    humidity_range = models.CharField(max_length=50)
    suitable_plants = models.ManyToManyField(PlantType, related_name='suitable_climates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Diagnostic(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diagnostics')
    plant_type = models.ForeignKey(PlantType, on_delete=models.CASCADE, related_name='diagnostics')
    image = models.ImageField(upload_to='diagnostics/')
    result = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    plant_type = models.ForeignKey(PlantType, on_delete=models.CASCADE, related_name='recommendations')
    soil_type = models.ForeignKey(SoilType, on_delete=models.CASCADE, related_name='recommendations')
    climate = models.ForeignKey(Climate, on_delete=models.CASCADE, related_name='recommendations')
    season = models.CharField(max_length=20)
    recommendation = models.TextField()
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class CropRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crop_recommendations')

    nitrogen = models.FloatField()
    phosphorus = models.FloatField()
    potassium = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph = models.FloatField()
    rainfall = models.FloatField()

    # ML model output
    predicted_label = models.IntegerField(null=True, blank=True)  # index like "0"
    predicted_crop = models.CharField(max_length=50, null=True, blank=True)  # e.g. "maize"
    confidence_score = models.FloatField(null=True, blank=True)

    # Explanation or LLM response
    explanation = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class FertilizerRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fertilizer_recommendations')
    crop = models.ForeignKey(PlantType, on_delete=models.CASCADE, related_name='fertilizer_recommendations')
    soil_type = models.ForeignKey(SoilType, on_delete=models.CASCADE, related_name='fertilizer_recommendations')

    temperature = models.FloatField()
    humidity = models.FloatField()
    moisture = models.FloatField()
    nitrogen = models.FloatField()
    phosphorus = models.FloatField()
    potassium = models.FloatField()

    # ML model output
    predicted_label = models.IntegerField(null=True, blank=True)
    predicted_fertilizer = models.CharField(max_length=50, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)

    explanation = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
