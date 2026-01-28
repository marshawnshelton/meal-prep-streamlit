"""
Custom Plan Feature
Allows users to manually select meals, set budget, and configure household size
Collects preference data for future ML recommendations
"""

import streamlit as st
from datetime import datetime
import json


def custom_plan_page():
    """
    Custom meal plan creation with manual recipe selection
    """
    st.title("🎨 Create Custom Meal Plan")
    
    # Check authentication
    if 'user' not in st.session_state:
        st.warning("Please log in to create custom meal plans.")
        return
    
    # Initialize session state
    if 'custom_plan' not in st.session_state:
        st.session_state.custom_plan = {
            'days': 7,
            'people': 2,
            'budget': 200,
            'selected_meals': {},
            'preferences': []
        }
    
    # Get user profile for defaults
    user_profile = st.session_state.user.get('profile', {})
    
    # ============================================================================
    # CONFIGURATION SECTION
    # ============================================================================
    
    st.subheader("📊 Plan Configuration")
    
    with st.expander("⚙️ Setup Your Plan", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            people = st.number_input(
                "👥 People",
                min_value=1,
                max_value=10,
                value=user_profile.get('household_size', 2),
                help="How many people will be eating?"
            )
            st.session_state.custom_plan['people'] = people
        
        with col2:
            # Calculate smart default budget based on people
            default_budget = calculate_default_budget(people, days=7)
            
            budget = st.number_input(
                "💰 Budget ($)",
                min_value=50,
                max_value=2000,
                value=default_budget,
                step=25,
                help="Total grocery budget for this plan"
            )
            st.session_state.custom_plan['budget'] = budget
        
        with col3:
            days = st.number_input(
                "📅 Days",
                min_value=3,
                max_value=21,
                value=7,
                help="How many days to plan?"
            )
            st.session_state.custom_plan['days'] = days
        
        # Budget breakdown
        per_day = budget / days
        per_person_per_day = budget / (days * people)
        per_meal = budget / (days * people * 3)
        
        st.info(f"""
        **Budget Breakdown:**
        - Per day: ${per_day:.2f}
        - Per person per day: ${per_person_per_day:.2f}
        - Per meal: ${per_meal:.2f}
        """)
        
        # Budget guidance
        if per_person_per_day < 5:
            st.warning("💡 **Tight Budget Mode** - Focus on affordable proteins and pantry staples")
        elif per_person_per_day < 10:
            st.success("✅ **Balanced Budget** - Good variety available")
        else:
            st.success("🌟 **Flexible Budget** - Premium options available")
    
    # ============================================================================
    # MEAL SELECTION SECTION
    # ============================================================================
    
    st.subheader("🍽️ Select Your Meals")
    
    # Get available recipes
    recipes = load_recipes()
    
    # Organize by meal type - be flexible with meal_type field
    breakfast_recipes = []
    lunch_recipes = []
    dinner_recipes = []
    
    for r in recipes:
        meal_type = r.get('meal_type', '').lower()
        
        # Check multiple possible values for breakfast
        if meal_type in ['breakfast', 'morning', 'brunch']:
            breakfast_recipes.append(r)
        # Check for lunch
        elif meal_type in ['lunch', 'midday', 'lunch_dinner']:
            lunch_recipes.append(r)
        # Check for dinner
        elif meal_type in ['dinner', 'evening', 'lunch_dinner']:
            dinner_recipes.append(r)
        # Fallback: check recipe name for clues
        else:
            name_lower = r['name'].lower()
            if any(word in name_lower for word in ['oatmeal', 'pancake', 'hash', 'grits', 'breakfast']):
                breakfast_recipes.append(r)
            elif any(word in name_lower for word in ['bowl', 'salad', 'wrap', 'sandwich']):
                lunch_recipes.append(r)
            else:
                dinner_recipes.append(r)
    
    # Debug info
    st.caption(f"📊 Available: {len(breakfast_recipes)} breakfasts, {len(lunch_recipes)} lunches, {len(dinner_recipes)} dinners")
    
    # Track total meals needed
    total_meals_needed = days * 3
    total_meals_selected = sum(len(meals) for meals in st.session_state.custom_plan['selected_meals'].values())
    
    # Progress indicator
    progress = total_meals_selected / total_meals_needed
    st.progress(progress)
    st.caption(f"Selected {total_meals_selected} of {total_meals_needed} meals ({progress*100:.0f}%)")
    
    # Meal selection tabs
    tab1, tab2, tab3 = st.tabs(["🌅 Breakfast", "🌞 Lunch", "🌙 Dinner"])
    
    with tab1:
        st.write(f"**Select {days} Breakfasts**")
        selected_breakfasts = meal_selector(
            breakfast_recipes,
            "breakfast",
            days,
            people,
            per_meal
        )
    
    with tab2:
        st.write(f"**Select {days} Lunches**")
        selected_lunches = meal_selector(
            lunch_recipes,
            "lunch",
            days,
            people,
            per_meal
        )
    
    with tab3:
        st.write(f"**Select {days} Dinners**")
        selected_dinners = meal_selector(
            dinner_recipes,
            "dinner",
            days,
            people,
            per_meal
        )
    
    # ============================================================================
    # COST ESTIMATION SECTION
    # ============================================================================
    
    if total_meals_selected > 0:
        st.subheader("💵 Cost Estimate")
        
        # Estimate costs for selected meals
        estimated_cost = estimate_plan_cost(
            st.session_state.custom_plan['selected_meals'],
            people,
            days
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Estimated Cost",
                f"${estimated_cost:.2f}",
                delta=f"${estimated_cost - budget:.2f}" if estimated_cost != budget else None
            )
        
        with col2:
            if estimated_cost <= budget:
                st.metric("Budget Status", "✅ Under Budget")
            else:
                over_budget = estimated_cost - budget
                st.metric("Budget Status", "⚠️ Over Budget", delta=f"+${over_budget:.2f}")
        
        with col3:
            confidence = get_price_confidence(st.session_state.custom_plan['selected_meals'])
            st.metric("Price Confidence", f"{confidence}%")
    
    # ============================================================================
    # SAVE PLAN SECTION
    # ============================================================================
    
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        plan_name = st.text_input(
            "Plan Name",
            value=f"Custom Plan - {datetime.now().strftime('%b %d, %Y')}",
            help="Give your meal plan a name"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")
        
        if st.button("💾 Save Custom Plan", type="primary", use_container_width=True):
            if total_meals_selected < total_meals_needed:
                st.error(f"Please select all {total_meals_needed} meals before saving!")
            else:
                save_custom_plan(
                    plan_name,
                    st.session_state.custom_plan,
                    estimated_cost,
                    confidence
                )
                st.success("✅ Custom plan saved successfully!")
                st.balloons()
                
                # Navigate to plan view
                st.session_state.page = 'meal_plan'
                st.rerun()


def meal_selector(recipes, meal_type, days, people, budget_per_meal):
    """
    Interactive meal selector with visual cards
    """
    if meal_type not in st.session_state.custom_plan['selected_meals']:
        st.session_state.custom_plan['selected_meals'][meal_type] = []
    
    selected = st.session_state.custom_plan['selected_meals'][meal_type]
    
    # Show already selected meals
    if selected:
        st.write("**Selected:**")
        for i, meal in enumerate(selected):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{i+1}. {meal['name']}")
            with col2:
                est_cost = estimate_meal_cost(meal, people)
                if est_cost <= budget_per_meal:
                    st.write(f"💰 ${est_cost:.2f}")
                else:
                    st.write(f"⚠️ ${est_cost:.2f}")
            with col3:
                if st.button("❌", key=f"remove_{meal_type}_{i}"):
                    selected.pop(i)
                    st.rerun()
    
    # Add new meal
    if len(selected) < days:
        st.write("**Add Meal:**")
        
        # Filter out already selected
        available = [r for r in recipes if r not in selected]
        
        if available:
            # Show recipe cards
            cols = st.columns(3)
            for i, recipe in enumerate(available[:6]):  # Show 6 at a time
                with cols[i % 3]:
                    with st.container(border=True):
                        st.write(f"**{recipe['name']}**")
                        
                        # Show estimated cost
                        est_cost = estimate_meal_cost(recipe, people)
                        if est_cost <= budget_per_meal:
                            st.caption(f"💰 Est: ${est_cost:.2f} ✅")
                        else:
                            st.caption(f"💰 Est: ${est_cost:.2f} ⚠️")
                        
                        # Show key info
                        st.caption(f"⏱️ {recipe.get('prep_time', 'N/A')} min")
                        
                        if st.button("➕ Add", key=f"add_{meal_type}_{i}", use_container_width=True):
                            selected.append(recipe)
                            
                            # Track preference for ML
                            track_meal_preference(
                                st.session_state.user['user_id'],  # Fixed: was 'uid'
                                recipe['id'],
                                'manual_selection',
                                {'budget_per_meal': budget_per_meal, 'people': people}
                            )
                            
                            st.rerun()
    else:
        st.success(f"✅ All {days} {meal_type}s selected!")
    
    return selected


def calculate_default_budget(people, days=7):
    """
    Calculate smart default budget based on household size
    """
    # USDA moderate cost meal plan (2024 estimates)
    per_person_per_week = {
        1: 70,   # Single person
        2: 130,  # Couple
        3: 180,  # Small family
        4: 230,  # Family of 4
        5: 280,  # Large family
    }
    
    base_weekly = per_person_per_week.get(people, people * 60)
    daily_rate = base_weekly / 7
    total_budget = daily_rate * days
    
    # Round to nearest $25
    return round(total_budget / 25) * 25


def estimate_meal_cost(recipe, people):
    """
    Estimate cost of a single meal for given number of people
    """
    # Get cost tier from recipe
    tier = recipe.get('cost_tier', 'medium')
    
    # Base cost per serving
    tier_costs = {
        'very_cheap': 2.00,
        'cheap': 3.00,
        'budget_friendly': 4.00,
        'medium': 5.50,
        'expensive': 8.00,
        'premium': 12.00
    }
    
    base_cost = tier_costs.get(tier, 5.00)
    
    # Scale by people (with efficiency factor)
    if people <= 2:
        efficiency = 1.0
    elif people <= 4:
        efficiency = 0.9
    else:
        efficiency = 0.85
    
    return base_cost * people * efficiency


def estimate_plan_cost(selected_meals, people, days):
    """
    Estimate total cost for entire plan
    """
    total = 0
    for meal_type, meals in selected_meals.items():
        for meal in meals:
            total += estimate_meal_cost(meal, people)
    
    return total


def get_price_confidence(selected_meals):
    """
    Calculate confidence level for price estimates
    """
    # For now, return medium confidence (estimates)
    # When API prices are integrated, this will check actual price sources
    return 65  # Medium confidence


def track_meal_preference(user_id, recipe_id, selection_context, metadata):
    """
    Track user meal selections for future ML recommendations
    """
    try:
        import requests
        from firebase_config import FIRESTORE_URL
        
        # Get ID token from session
        id_token = st.session_state.user.get('id_token')
        if not id_token:
            return
        
        preference_data = {
            'recipe_id': {'stringValue': recipe_id},
            'selected_at': {'timestampValue': datetime.now().isoformat() + 'Z'},
            'context': {'stringValue': selection_context},
            'metadata': {'stringValue': json.dumps(metadata)}
        }
        
        # Save to Firebase
        url = f"{FIRESTORE_URL}/users/{user_id}/meal_preferences/{recipe_id}"
        headers = {"Authorization": f"Bearer {id_token}"}
        
        requests.patch(
            url,
            json={"fields": preference_data},
            headers=headers,
            timeout=2
        )
        
    except Exception as e:
        print(f"Error tracking preference: {e}")


def save_custom_plan(plan_name, plan_data, estimated_cost, confidence):
    """
    Save custom plan to Firebase in the format the app expects
    """
    try:
        import requests
        from firebase_config import FIRESTORE_URL
        from datetime import timedelta
        
        user_id = st.session_state.user['user_id']
        id_token = st.session_state.user.get('id_token')
        
        if not id_token:
            st.error("Authentication required to save plan")
            return
        
        # Get start date
        start_date = datetime.now()
        
        # Build meal plan in the format your app expects
        days_list = []
        
        for day_num in range(1, plan_data['days'] + 1):
            current_date = start_date + timedelta(days=day_num - 1)
            
            # Get meals for this day
            breakfast = None
            lunch = None
            dinner = None
            
            # Get from selected meals
            breakfasts = plan_data['selected_meals'].get('breakfast', [])
            lunches = plan_data['selected_meals'].get('lunch', [])
            dinners = plan_data['selected_meals'].get('dinner', [])
            
            if day_num <= len(breakfasts):
                breakfast_recipe = breakfasts[day_num - 1]
                breakfast = {
                    'recipe': breakfast_recipe['name'],
                    'cuisine': breakfast_recipe.get('cuisine', ''),
                    'time': f"{breakfast_recipe.get('prep_time', 0)} min"
                }
            
            if day_num <= len(lunches):
                lunch_recipe = lunches[day_num - 1]
                lunch = {
                    'recipe': lunch_recipe['name'],
                    'cuisine': lunch_recipe.get('cuisine', ''),
                    'time': f"{lunch_recipe.get('prep_time', 0)} min"
                }
            
            if day_num <= len(dinners):
                dinner_recipe = dinners[day_num - 1]
                dinner = {
                    'recipe': dinner_recipe['name'],
                    'cuisine': dinner_recipe.get('cuisine', ''),
                    'time': f"{dinner_recipe.get('prep_time', 0)} min"
                }
            
            day_info = {
                'day': day_num,
                'day_name': current_date.strftime('%A'),
                'date': current_date.strftime('%m/%d/%Y'),
                'meals': {
                    'breakfast': breakfast,
                    'lunch': lunch,
                    'dinner': dinner
                }
            }
            
            days_list.append(day_info)
        
        # Build complete meal plan
        meal_plan = {
            'plan_name': plan_name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': (start_date + timedelta(days=plan_data['days'] - 1)).strftime('%Y-%m-%d'),
            'planning_days': plan_data['days'],
            'people': plan_data['people'],
            'budget': plan_data['budget'],
            'estimated_cost': estimated_cost,
            'plan_type': 'custom',
            'days': days_list  # This is the list your app expects!
        }
        
        # Save to Firebase (simplified - just save the whole thing as JSON string)
        url = f"{FIRESTORE_URL}/users/{user_id}"
        headers = {"Authorization": f"Bearer {id_token}"}
        
        firebase_data = {
            'fields': {
                'meal_plan': {
                    'stringValue': json.dumps(meal_plan)
                }
            }
        }
        
        response = requests.patch(
            url,
            json=firebase_data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            # Update session state
            st.session_state.meal_plan = meal_plan
            st.session_state.meal_plan_loaded = True
            st.session_state.just_generated = False
            
            # Generate shopping list with selected stores
            try:
                from shopping_list import ShoppingListGenerator
                from meal_planner import MealPlanner
                
                # Get user's selected stores from session state
                selected_stores = st.session_state.get('selected_stores', ['costco', 'whole_foods', 'petes_fresh_market'])
                
                # Initialize planner and shopping list generator
                planner = MealPlanner()
                shopping_gen = ShoppingListGenerator()
                
                # Generate shopping list
                shopping_list = shopping_gen.generate_list(meal_plan, planner.recipes)
                
                # Apply smart routing with user's stores
                from store_router import apply_smart_routing
                shopping_list = apply_smart_routing(shopping_list, selected_stores)
                
                # Save to session
                st.session_state.shopping_list = shopping_list
                
            except Exception as shop_error:
                print(f"Error generating shopping list: {shop_error}")
                # Don't fail the whole save if shopping list fails
        else:
            st.error(f"Failed to save plan: {response.status_code}")
        
    except Exception as e:
        st.error(f"Error saving plan: {e}")
        import traceback
        st.error(traceback.format_exc())


def load_recipes():
    """
    Load available recipes from session state
    """
    if 'recipes' in st.session_state:
        # Flatten the recipes dictionary into a list
        all_recipes = []
        for category, recipe_list in st.session_state.recipes.items():
            for recipe in recipe_list:
                # Add cost tier if not present (based on simple heuristics)
                if 'cost_tier' not in recipe:
                    recipe['cost_tier'] = estimate_cost_tier(recipe)
                # Add ID if not present
                if 'id' not in recipe:
                    recipe['id'] = recipe['name'].lower().replace(' ', '_')
                all_recipes.append(recipe)
        return all_recipes
    return []


def estimate_cost_tier(recipe):
    """
    Estimate cost tier based on recipe characteristics
    """
    name_lower = recipe['name'].lower()
    
    # Check for expensive ingredients
    if any(word in name_lower for word in ['salmon', 'beef', 'duck', 'lobster']):
        return 'expensive'
    
    # Check for cheap ingredients  
    if any(word in name_lower for word in ['lentil', 'bean', 'rice', 'oat', 'egg']):
        return 'cheap'
    
    # Check for budget-friendly proteins
    if any(word in name_lower for word in ['chicken', 'turkey', 'pork']):
        return 'budget_friendly'
    
    # Default to medium
    return 'medium'


if __name__ == "__main__":
    custom_plan_page()
