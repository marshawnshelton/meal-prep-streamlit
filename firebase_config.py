# Firebase Configuration for Isosalus Meal Prep
# This file contains your Firebase project settings

FIREBASE_CONFIG = {
    "apiKey": "AIzaSyAAGV7uN45Hfd_5AYFSrEXh8vKHcxUv7Xs",
    "authDomain": "isosalus-meal-prep.firebaseapp.com",
    "projectId": "isosalus-meal-prep",
    "storageBucket": "isosalus-meal-prep.firebasestorage.app",
    "messagingSenderId": "982729337956",
    "appId": "1:982729337956:web:88f98224451c9b4953c371",
    "databaseURL": "https://isosalus-meal-prep-default-rtdb.firebaseio.com/"
}

# Firebase REST API endpoints
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents"
