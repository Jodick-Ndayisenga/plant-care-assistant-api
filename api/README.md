# Gardien Éveillé API Documentation

## Table of Contents
- [Authentication](#authentication)
- [User Management](#user-management)
- [Plant Types](#plant-types)
- [Soil Types](#soil-types)
- [Climates](#climates)
- [Diagnostics](#diagnostics)
- [Conversations](#conversations)
- [Recommendations](#recommendations)
- [Machine Learning Endpoints](#machine-learning-endpoints)

## Authentication

### Login
`POST /api/login/`
- Request Body:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- Response:
  ```json
  {
    "access": "JWT token",
    "refresh": "JWT refresh token",
    "user": {
      "id": 1,
      "username": "string",
      "email": "string",
      "full_name": "string",
      "role": "string",
      "phoneNumber": "string",
      "province": "string"
    }
  }
  ```

## User Management

### Create User
`POST /api/users/`
- Request Body:
  ```json
  {
    "username": "string",
    "email": "string",
    "full_name": "string",
    "phone_number": "string",
    "province": "string",
    "password": "string"
  }
  ```

### Get Current User
`GET /api/users/me/`

## Plant Types

### List Plant Types
`GET /api/plant-types/`

### Get Plant Type
`GET /api/plant-types/{id}/`

## Soil Types

### List Soil Types
`GET /api/soil-types/`

### Get Soil Type
`GET /api/soil-types/{id}/`

## Climates

### List Climates
`GET /api/climates/`

### Get Climate
`GET /api/climates/{id}/`

## Diagnostics

### Create Diagnostic
`POST /api/diagnostics/`
- Request Body (multipart/form-data):
  - `plant_type_id`: integer
  - `image`: file

### Analyze Diagnostic
`POST /api/diagnostics/{id}/analyze/`

## Conversations

### Create Conversation
`POST /api/conversations/`
- Request Body:
  ```json
  {
    "title": "string"
  }
  ```

### List Messages in Conversation
`GET /api/conversations/{id}/messages/`

### Send Message
`POST /api/conversations/{id}/messages/`
- Request Body:
  ```json
  {
    "role": "user|assistant|system",
    "content": "string"
  }
  ```

## Recommendations

### List Recommendations
`GET /api/recommendations/`

## Machine Learning Endpoints

### Predict Plant Disease
`POST /api/ml/predict_disease/`
- Request Body (multipart/form-data):
  - `image`: file

### Recommend Crop
`POST /api/ml/recommend_crop/`
- Request Body:
  ```json
  {
    "soil_type": "string",
    "climate": "string",
    "season": "string"
  }
  ```

### Recommend Fertilizer
`POST /api/ml/recommend_fertilizer/`
- Request Body:
  ```json
  {
    "soil_type": "string",
    "crop_type": "string"
  }
  ```

## Authentication
All endpoints except `/api/login/` and `/api/users/` (POST) require JWT authentication in the header:
`Authorization: Bearer <access_token>`

### Refresh Token
`POST /api/token/refresh/`
- Request Body:
  ```json
  {
    "refresh": "JWT refresh token"
  }
  ```
- Response:
  ```json
  {
    "access": "JWT token"
  }
  ```

### Logout
`POST /api/logout/`
- Request Body:
  ```json
  {
    "refresh": "JWT refresh token"
  }
  ```
- Response:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```

### Verify Token
`POST /api/token/verify/`
- Request Body:
  ```json
  {
    "token": "JWT token"
  }
  ```
- Response:
  ```json
  {
    "token": "JWT token",
    "exp": 1692345600,
    "user_id": 1,
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "string",
    "phoneNumber": "string",
    "province": "string"
  }
  ```
- Response:
  ```json
  {
    "token": "JWT token",
    "exp": 1692345600,
    "user_id": 1,
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "string",
    "phoneNumber": "string",
    "province": "string"
  }
  ```

    

  
