from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PlantType, SoilType, Climate, Diagnostic, Conversation, Message, Recommendation

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'province', 'is_staff')
    search_fields = ('username', 'email', 'full_name', 'province')
    list_filter = ('is_staff', 'is_superuser', 'province')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('full_name', 'phone_number', 'province')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'phone_number', 'province'),
        }),
    )

@admin.register(PlantType)
class PlantTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'emoji', 'created_at')
    search_fields = ('name', 'scientific_name')
    list_filter = ('created_at',)

@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('suitable_plants',)

@admin.register(Climate)
class ClimateAdmin(admin.ModelAdmin):
    list_display = ('name', 'temperature_range', 'rainfall_range', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('suitable_plants',)

@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    list_display = ('user', 'plant_type', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'plant_type__name')
    readonly_fields = ('result',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at', 'updated_at')
    search_fields = ('user__username', 'title')
    list_filter = ('created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('conversation__title', 'content')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'plant_type', 'soil_type', 'climate', 'season', 'confidence_score')
    list_filter = ('season', 'created_at')
    search_fields = ('user__username', 'plant_type__name')

# Register the custom user admin
admin.site.register(User, CustomUserAdmin)
