"""
Firebase Authentication Module for Streamlit
Handles user signup, login, and session management
"""

import streamlit as st
import requests
import json
from typing import Optional, Dict, Tuple
from firebase_config import FIREBASE_CONFIG, AUTH_URL, FIRESTORE_URL


class FirebaseAuth:
    """Firebase Authentication Handler"""
    
    def __init__(self):
        self.api_key = FIREBASE_CONFIG['apiKey']
        self.auth_url = AUTH_URL
        self.firestore_url = FIRESTORE_URL
    
    def sign_up(self, email: str, password: str, user_data: Dict) -> Tuple[bool, str]:
        """
        Create new user account
        Returns: (success: bool, message: str)
        """
        try:
            # Create auth account
            url = f"{self.auth_url}:signUp?key={self.api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                user_id = data['localId']
                id_token = data['idToken']
                
                # Save user profile to Firestore
                success = self._save_user_profile(user_id, id_token, email, user_data)
                
                if success:
                    return True, "Account created successfully!"
                else:
                    return False, "Account created but profile save failed"
            else:
                error = response.json().get('error', {}).get('message', 'Unknown error')
                return False, f"Signup failed: {error}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def sign_in(self, email: str, password: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Sign in existing user
        Returns: (success: bool, user_data: dict, message: str)
        """
        try:
            url = f"{self.auth_url}:signInWithPassword?key={self.api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                user_id = data['localId']
                id_token = data['idToken']
                email = data['email']
                
                # Get user profile
                profile = self._get_user_profile(user_id, id_token)
                
                user_data = {
                    'user_id': user_id,
                    'email': email,
                    'id_token': id_token,
                    'profile': profile
                }
                
                return True, user_data, "Login successful!"
            else:
                error = response.json().get('error', {}).get('message', 'Unknown error')
                return False, None, f"Login failed: {error}"
                
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def _save_user_profile(self, user_id: str, id_token: str, email: str, user_data: Dict) -> bool:
        """Save user profile to Firestore"""
        try:
            from datetime import datetime
            
            url = f"{self.firestore_url}/users/{user_id}"
            
            # Convert user_data to Firestore format
            fields = {
                "email": {"stringValue": email},
                "created_at": {"timestampValue": datetime.now().isoformat() + "Z"},
            }
            
            # Add demographics
            for key, value in user_data.items():
                if isinstance(value, str):
                    fields[key] = {"stringValue": value}
                elif isinstance(value, int):
                    fields[key] = {"integerValue": str(value)}
                elif isinstance(value, bool):
                    fields[key] = {"booleanValue": value}
            
            payload = {"fields": fields}
            
            headers = {"Authorization": f"Bearer {id_token}"}
            response = requests.patch(url, json=payload, headers=headers, params={"updateMask.fieldPaths": list(fields.keys())})
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            st.error(f"Profile save error: {e}")
            return False
    
    def _get_user_profile(self, user_id: str, id_token: str) -> Dict:
        """Get user profile from Firestore"""
        try:
            url = f"{self.firestore_url}/users/{user_id}"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get('fields', {})
                
                # Convert from Firestore format
                profile = {}
                for key, value in fields.items():
                    if 'stringValue' in value:
                        profile[key] = value['stringValue']
                    elif 'integerValue' in value:
                        profile[key] = int(value['integerValue'])
                    elif 'booleanValue' in value:
                        profile[key] = value['booleanValue']
                
                return profile
            else:
                return {}
                
        except Exception as e:
            st.error(f"Profile fetch error: {e}")
            return {}
    
    def save_meal_plan(self, user_id: str, id_token: str, meal_plan: Dict) -> bool:
        """Save meal plan to user's account"""
        try:
            # Generate unique meal plan ID
            from datetime import datetime
            plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            url = f"{self.firestore_url}/users/{user_id}/meal_plans/{plan_id}"
            
            # Simplified storage - just save as JSON string for now
            fields = {
                "data": {"stringValue": json.dumps(meal_plan)},
                "created_at": {"timestampValue": datetime.now().isoformat() + "Z"}
            }
            
            payload = {"fields": fields}
            headers = {"Authorization": f"Bearer {id_token}"}
            
            response = requests.patch(url, json=payload, headers=headers)
            return response.status_code in [200, 201]
            
        except Exception as e:
            st.error(f"Save meal plan error: {e}")
            return False
    
    def get_meal_plans(self, user_id: str, id_token: str) -> list:
        """Get all meal plans for user"""
        try:
            url = f"{self.firestore_url}/users/{user_id}/meal_plans"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                
                meal_plans = []
                for doc in documents:
                    fields = doc.get('fields', {})
                    if 'data' in fields:
                        plan_data = json.loads(fields['data']['stringValue'])
                        meal_plans.append(plan_data)
                
                return meal_plans
            else:
                return []
                
        except Exception as e:
            st.error(f"Get meal plans error: {e}")
            return []


def init_session_state():
    """Initialize session state for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'  # 'login' or 'signup'


def show_auth_page():
    """Display login/signup page"""
    init_session_state()
    
    st.title("🍽️ Isosalus Meal Prep")
    st.markdown("### Welcome! Sign in to start planning your meals")
    
    # Toggle between login and signup
    auth_mode = st.session_state.auth_mode
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True, 
                    type="primary" if auth_mode == 'login' else "secondary"):
            st.session_state.auth_mode = 'login'
            st.rerun()
    with col2:
        if st.button("Sign Up", use_container_width=True,
                    type="primary" if auth_mode == 'signup' else "secondary"):
            st.session_state.auth_mode = 'signup'
            st.rerun()
    
    st.markdown("---")
    
    auth = FirebaseAuth()
    
    if auth_mode == 'login':
        show_login_form(auth)
    else:
        show_signup_form(auth)


def show_login_form(auth: FirebaseAuth):
    """Display login form"""
    st.subheader("Login to Your Account")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                with st.spinner("Logging in..."):
                    success, user_data, message = auth.sign_in(email, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = user_data
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)


def show_signup_form(auth: FirebaseAuth):
    """Display signup form with demographics"""
    st.subheader("Create Your Account")
    
    with st.form("signup_form"):
        st.markdown("**Account Information**")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password (min 6 characters)", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        
        st.markdown("---")
        st.markdown("**About You** (helps us improve the app)")
        
        age_group = st.selectbox("Age Group", [
            "Select...",
            "18-24",
            "25-34", 
            "35-44",
            "45-54",
            "55-64",
            "65+"
        ])
        
        household_size = st.number_input("Household Size", min_value=1, max_value=10, value=2)
        
        income_bracket = st.selectbox("Annual Household Income", [
            "Select...",
            "Under $25,000",
            "$25,000-$49,999",
            "$50,000-$74,999",
            "$75,000-$99,999",
            "$100,000-$149,999",
            "$150,000+"
        ])
        
        primary_goal = st.selectbox("Primary Goal", [
            "Select...",
            "Save money on groceries",
            "Eat healthier",
            "Lose weight",
            "Manage chronic condition (diabetes, hypertension, etc.)",
            "Learn to cook",
            "Save time",
            "Reduce food waste"
        ])
        
        dietary_restrictions = st.multiselect("Dietary Restrictions (optional)", [
            "None",
            "Vegetarian",
            "Vegan",
            "Gluten-free",
            "Dairy-free",
            "Nut allergies",
            "Shellfish allergies",
            "Low-sodium",
            "Diabetic-friendly",
            "Other"
        ])
        
        zipcode = st.text_input("ZIP Code (helps us find stores near you)")
        
        submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            # Validation
            if not email or not password:
                st.error("Email and password are required")
            elif password != password_confirm:
                st.error("Passwords don't match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif age_group == "Select..." or income_bracket == "Select..." or primary_goal == "Select...":
                st.error("Please complete all required fields")
            else:
                # Create user data
                user_data = {
                    "age_group": age_group,
                    "household_size": household_size,
                    "income_bracket": income_bracket,
                    "primary_goal": primary_goal,
                    "dietary_restrictions": ",".join(dietary_restrictions) if dietary_restrictions else "None",
                    "zipcode": zipcode
                }
                
                with st.spinner("Creating your account..."):
                    success, message = auth.sign_up(email, password, user_data)
                    
                    if success:
                        st.success(message)
                        st.info("Please login with your new account")
                        st.session_state.auth_mode = 'login'
                        st.rerun()
                    else:
                        st.error(message)


def logout():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.meal_plan = None
    st.rerun()
