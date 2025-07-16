from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from .models import PlantType, SoilType, Climate, Diagnostic, Conversation, Message, Recommendation

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            phone_number='+1234567890',
            province='Test Province'
        )
        
        self.plant_type = PlantType.objects.create(
            name='Test Plant',
            scientific_name='Testus Plantus',
            description='A test plant',
            emoji='🌱'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.full_name, 'Test User')
        self.assertEqual(self.user.phone_number, '+1234567890')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_plant_type_str(self):
        self.assertEqual(str(self.plant_type), '🌱 Test Plant')

class APITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            phone_number='+1234567890',
            province='Test Province'
        )
        
        self.client.force_authenticate(user=self.user)

        self.plant_type = PlantType.objects.create(
            name='Test Plant',
            scientific_name='Testus Plantus',
            description='A test plant',
            emoji='🌱'
        )

    def test_user_me_endpoint(self):
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_plant_type_list(self):
        response = self.client.get('/api/plant-types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_diagnostic(self):
        image = SimpleUploadedFile(
            'test.jpg',
            b'file_content',
            content_type='image/jpeg'
        )
        
        data = {
            'plant_type_id': self.plant_type.id,
            'image': image
        }
        
        response = self.client.post('/api/diagnostics/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_conversation(self):
        data = {'title': 'Test Conversation'}
        response = self.client.post('/api/conversations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Conversation')

    def test_send_message(self):
        # Create a conversation first
        conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        
        data = {
            'role': 'user',
            'content': 'Test message'
        }
        
        response = self.client.post(
            f'/api/conversations/{conversation.id}/messages/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test message')

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'full_name': 'New User',
            'phone_number': '+1234567890',
            'province': 'Test Province'
        }

    def test_user_registration(self):
        response = self.client.post('/api/users/', self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_token_obtain(self):
        # Create user first
        User.objects.create_user(**self.user_data)
        
        response = self.client.post('/api/token/', {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
