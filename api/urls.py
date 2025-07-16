from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

# Main router for top-level resources
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'plant-types', views.PlantTypeViewSet)
router.register(r'soil-types', views.SoilTypeViewSet)
router.register(r'climates', views.ClimateViewSet)
router.register(r'diagnostics', views.DiagnosticViewSet, basename='diagnostic')
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
#router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')
router.register(r'crop-recommendations', views.CropRecommendationViewSet, basename='crop-recommendation')
router.register(r'fertilizer-recommendations', views.FertilizerRecommendationViewSet, basename='fertilizer-recommendation')

# Nested router for messages inside conversations
conversations_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
    path('login/', views.LoginViewSet.as_view({'post': 'create'}), name='login'),
]
