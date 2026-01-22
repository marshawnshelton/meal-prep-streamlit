#!/usr/bin/env python3
"""
Meal Prep System - Web Interface
Built with Streamlit for easy, user-friendly meal planning
Now with Firebase Authentication!
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from meal_planner import MealPlanner
from shopping_list import ShoppingListGenerator
from excel_export import ExcelExporter

# Import authentication
from auth import init_session_state, show_auth_page, logout, FirebaseAuth


# Inline helper functions (avoiding import issues)
def display_shopping_with_checklist(shopping_list, auth):
    """Display shopping list with checkboxes"""
    st.header("🛒 Shopping Checklist")
    total_items = sum(len(store['items']) for store in shopping_list['stores'].values())
    st.info(f"**Total Items:** {total_items} across {len(shopping_list['stores'])} stores")
    st.markdown("---")
    
    for store_name, store_data in shopping_list['stores'].items():
        store_display = store_name.replace('_', ' ').title()
        with st.expander(f"**{store_display}** ({len(store_data['items'])} items)", expanded=True):
            if 'store_info' in store_data:
                st.caption(f"📍 {store_data['store_info'].get('type', '')}")
            st.markdown("")
            
            for idx, item in enumerate(store_data['items']):
                col1, col2 = st.columns([1, 5])
                with col1:
                    checked = st.checkbox("✓", key=f"{store_name}_{idx}", label_visibility="collapsed")
                with col2:
                    if checked:
                        st.markdown(f"~~{item['amount']} {item['unit']} **{item['item']}**~~")
                    else:
                        st.markdown(f"{item['amount']} {item['unit']} **{item['item']}**")
                    if 'used_in' in item and item['used_in']:
                        recipes = ", ".join(item['used_in'][:2])
                        st.caption(f"Used in: {recipes}")
    
    st.markdown("---")
    st.caption("💡 Tip: Check off items as you shop!")


def display_recipe_booklet_with_pdf(meal_plan, planner, auth):
    """Display recipe booklet"""
    st.header("📖 Recipe Booklet")
    unique_recipes = set()
    for day in meal_plan['days']:
        for meal_type, meal_info in day.get('meals', {}).items():
            if meal_info and meal_info.get('recipe'):
                unique_recipes.add(meal_info['recipe'])
    
    st.markdown(f"### {len(unique_recipes)} Recipes in Your Plan")
    st.markdown(f"**Meal Plan:** {meal_plan['start_date']} to {meal_plan['end_date']}")
    st.markdown("---")
    
    for i, recipe_name in enumerate(sorted(unique_recipes), 1):
        recipe = None
        for category, recipes in planner.recipes.items():
            for r in recipes:
                if r['name'] == recipe_name:
                    recipe = r
                    break
            if recipe:
                break
        
        if recipe:
            with st.expander(f"**{i}. {recipe['name']}** - {recipe.get('cuisine', 'N/A')}", expanded=(i == 1)):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Servings", recipe.get('servings', 'N/A'))
                with col2:
                    st.metric("Prep", f"{recipe.get('prep_time', 'N/A')} min")
                with col3:
                    st.metric("Cook", f"{recipe.get('cook_time', 'N/A')} min")
                
                st.markdown("---")
                st.markdown("### 🥘 Ingredients")
                ingredients = recipe.get('ingredients', [])
                if isinstance(ingredients, dict):
                    for section, ing_list in ingredients.items():
                        st.markdown(f"**{section.title()}:**")
                        for ing in ing_list:
                            if isinstance(ing, dict):
                                st.markdown(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                        st.markdown("")
                else:
                    for ing in ingredients:
                        if isinstance(ing, dict):
                            st.markdown(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                
                st.markdown("---")
                st.markdown("### 👩‍🍳 Instructions")
                for j, step in enumerate(recipe.get('instructions', []), 1):
                    st.markdown(f"**{j}.** {step}")
                
                if recipe.get('cultural_note'):
                    st.markdown("---")
                    st.info(f"💡 {recipe.get('cultural_note')}")
    
    st.markdown("---")
    st.caption("💡 Advanced features (PDF download, Firebase sync) coming soon!")


# Page configuration
st.set_page_config(
    page_title="Meal Prep System",
    page_icon="🍽️",
    layout="wide"
)

# Initialize authentication
init_session_state()

# Initialize other session state
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = None
if 'selected_meals' not in st.session_state:
    st.session_state.selected_meals = {}
if 'recipes' not in st.session_state:
    # Load recipes once
    planner = MealPlanner()
    st.session_state.recipes = planner.recipes
    st.session_state.planner = planner


def main():
    # Check if user is authenticated
    if not st.session_state.authenticated:
        show_auth_page()
        return
    
    # User is authenticated - show main app
    show_main_app()


def show_main_app():
    """Main application after authentication"""
    
    # Top bar with user info and logout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🍽️ Meal Prep System")
        st.markdown("### Plan your meals, generate shopping lists, get recipes")
    with col2:
        user_email = st.session_state.user['email']
        st.write("")  # Spacing
        st.caption(f"👤 {user_email.split('@')[0]}")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Show user profile info
        profile = st.session_state.user.get('profile', {})
        if profile:
            with st.expander("👤 Your Profile"):
                st.caption(f"**Goal:** {profile.get('primary_goal', 'N/A')}")
                st.caption(f"**Household:** {profile.get('household_size', 2)} people")
                st.caption(f"**ZIP:** {profile.get('zipcode', 'N/A')}")
        
        st.markdown("---")
        
        people = st.number_input("Number of people", min_value=1, max_value=10, 
                                value=config['system']['people'])
        
        budget = st.number_input("Bi-weekly budget ($)", min_value=100, max_value=1000, 
                                value=config['system']['budget_per_cycle'], step=50)
        
        days = st.slider("Planning days", min_value=1, max_value=30, 
                        value=config['system']['planning_cycle_days'])
        
        start_date = st.date_input("Start date", value=datetime.now())
        
        st.markdown("---")
        st.markdown("**Stores:**")
        for store in config['stores'].keys():
            st.markdown(f"✓ {store.replace('_', ' ').title()}")
        
        st.markdown("---")
        st.markdown(f"**📖 Total Recipes: {sum(len(r) for r in st.session_state.recipes.values())}**")
        for category, recipe_list in st.session_state.recipes.items():
            category_name = category.replace('_', ' ').title()
            st.caption(f"{category_name}: {len(recipe_list)}")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎲 Auto Generate", "✋ Custom Select", "📖 Browse Recipes", "📊 View Results"])
    
    # TAB 1: Auto Generate
    with tab1:
        st.header("Automatic Meal Planning")
        st.markdown("Let the system create a diverse meal plan for you")
        
        if st.button("🎲 Generate Random Plan", type="primary", use_container_width=True):
            with st.spinner("Generating your meal plan..."):
                planner = st.session_state.planner
                meal_plan = planner.generate_meal_plan(start_date)
                st.session_state.meal_plan = meal_plan
                
                # Save to Firebase
                auth = FirebaseAuth()
                user_id = st.session_state.user['user_id']
                id_token = st.session_state.user['id_token']
                
                if auth.save_meal_plan(user_id, id_token, meal_plan):
                    st.success(f"✓ Generated {days}-day meal plan and saved to your account!")
                else:
                    st.success(f"✓ Generated {days}-day meal plan!")
                    st.warning("Note: Plan saved locally but cloud sync failed")
                
                st.rerun()
    
    # TAB 2: Custom Select
    with tab2:
        st.header("Custom Meal Selection")
        st.markdown("Pick exactly what you want for each day")
        
        custom_days = st.number_input("How many days to plan?", min_value=1, max_value=14, value=7)
        
        if st.button("Start Custom Planning", type="primary"):
            st.session_state.custom_mode = True
            st.session_state.custom_days = custom_days
            st.session_state.current_day = 0
            st.session_state.selected_meals = {i: {} for i in range(custom_days)}
        
        if st.session_state.get('custom_mode'):
            current_day = st.session_state.current_day
            total_days = st.session_state.custom_days
            
            if current_day < total_days:
                day_date = start_date + timedelta(days=current_day)
                
                st.subheader(f"Day {current_day + 1} - {day_date.strftime('%A, %B %d')}")
                
                col1, col2 = st.columns(2)
                
                # Combine all breakfast categories
                all_breakfasts = []
                for cat in ['breakfast', 'breakfast_londons_originals', 'breakfast_EXPANDED']:
                    if cat in st.session_state.recipes:
                        all_breakfasts.extend(st.session_state.recipes[cat])
                
                # Combine all lunch/dinner categories
                all_lunch_dinner = []
                for cat in ['lunch_dinner', 'lunch_dinner_londons_originals', 'lunch_dinner_italian', 'lunch_dinner_mexican']:
                    if cat in st.session_state.recipes:
                        all_lunch_dinner.extend(st.session_state.recipes[cat])
                
                with col1:
                    # Breakfast
                    st.markdown("**🍳 Breakfast**")
                    breakfast_options = [f"{r['name']} ({r.get('cuisine', 'N/A')})" for r in all_breakfasts]
                    breakfast_selection = st.selectbox("Select breakfast", breakfast_options, 
                                            key=f"breakfast_{current_day}")
                    breakfast = breakfast_selection.split(' (')[0]
                    
                    # Morning Snack
                    st.markdown("**🥜 Morning Snack**")
                    snack_options = ["Skip"] + [r['name'] for r in st.session_state.recipes.get('snacks', [])]
                    snack_am = st.selectbox("Select snack", snack_options, 
                                           key=f"snack_am_{current_day}")
                
                with col2:
                    # Lunch
                    st.markdown("**🍱 Lunch**")
                    lunch_options = [f"{r['name']} ({r.get('cuisine', 'N/A')})" for r in all_lunch_dinner]
                    lunch_selection = st.selectbox("Select lunch", lunch_options, 
                                       key=f"lunch_{current_day}")
                    lunch = lunch_selection.split(' (')[0]
                    
                    # Dinner
                    st.markdown("**🍽️ Dinner**")
                    dinner_selection = st.selectbox("Select dinner", lunch_options, 
                                        key=f"dinner_{current_day}")
                    dinner = dinner_selection.split(' (')[0]
                
                # Afternoon Snack
                snack_pm = st.selectbox("🥤 Afternoon Snack", snack_options, 
                                       key=f"snack_pm_{current_day}")
                
                # Sweet Treat
                treat_options = ["Skip"] + [r['name'] for r in st.session_state.recipes.get('sweet_treats', [])]
                treat = st.selectbox("🍪 Sweet Treat (optional)", treat_options, 
                                    key=f"treat_{current_day}")
                
                # Navigation
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if current_day > 0:
                        if st.button("← Previous Day"):
                            st.session_state.current_day -= 1
                            st.rerun()
                
                with col2:
                    if st.button("Save Day"):
                        st.session_state.selected_meals[current_day] = {
                            'breakfast': breakfast,
                            'snack_am': snack_am if snack_am != "Skip" else None,
                            'lunch': lunch,
                            'snack_pm': snack_pm if snack_pm != "Skip" else None,
                            'dinner': dinner,
                            'treat': treat if treat != "Skip" else None
                        }
                        st.success(f"Day {current_day + 1} saved!")
                
                with col3:
                    if st.button("Next Day →"):
                        st.session_state.selected_meals[current_day] = {
                            'breakfast': breakfast,
                            'snack_am': snack_am if snack_am != "Skip" else None,
                            'lunch': lunch,
                            'snack_pm': snack_pm if snack_pm != "Skip" else None,
                            'dinner': dinner,
                            'treat': treat if treat != "Skip" else None
                        }
                        st.session_state.current_day += 1
                        st.rerun()
            
            else:
                st.success("🎉 All days planned!")
                if st.button("Generate Shopping List & Recipes"):
                    st.info("Converting to meal plan format...")
    
    # TAB 3: Browse Recipes
    with tab3:
        st.header("📖 Browse All Recipes")
        st.markdown(f"**{sum(len(r) for r in st.session_state.recipes.values())} recipes available**")
        
        # Filter by category
        all_categories = list(st.session_state.recipes.keys())
        category_display = {
            'breakfast': '🍳 Breakfast',
            'breakfast_londons_originals': "🍳 London's Original Breakfasts",
            'breakfast_EXPANDED': '🍳 Breakfast Classics',
            'lunch_dinner': '🍽️ Lunch & Dinner',
            'lunch_dinner_londons_originals': "🍽️ London's Original Meals",
            'lunch_dinner_italian': '🍝 Italian Cuisine',
            'lunch_dinner_mexican': '🌮 Mexican Cuisine',
            'snacks': '🥜 Snacks',
            'sweet_treats': '🍪 Sweet Treats'
        }
        
        selected_category = st.selectbox(
            "Filter by category",
            ['All'] + all_categories,
            format_func=lambda x: category_display.get(x, x.replace('_', ' ').title()) if x != 'All' else 'All Categories'
        )
        
        # Get recipes to display
        if selected_category == 'All':
            recipes_to_show = []
            for cat, recipe_list in st.session_state.recipes.items():
                for recipe in recipe_list:
                    recipe['_category'] = cat
                    recipes_to_show.append(recipe)
        else:
            recipes_to_show = st.session_state.recipes[selected_category]
        
        st.markdown(f"Showing **{len(recipes_to_show)}** recipes")
        
        # Search
        search = st.text_input("🔍 Search recipes", placeholder="e.g., chicken, Italian, oatmeal")
        
        if search:
            recipes_to_show = [
                r for r in recipes_to_show 
                if search.lower() in r['name'].lower() 
                or search.lower() in r.get('cuisine', '').lower()
            ]
            st.caption(f"Found {len(recipes_to_show)} matching recipes")
        
        # Display recipes
        for recipe in recipes_to_show:
            with st.expander(f"**{recipe['name']}** - {recipe.get('cuisine', 'N/A')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Cuisine:** {recipe.get('cuisine', 'N/A')}")
                    st.markdown(f"**Meal Type:** {recipe.get('meal_type', 'N/A').replace('_', ' ').title()}")
                    
                    if 'health_benefits' in recipe:
                        benefits = ", ".join([b.replace('_', ' ').title() for b in recipe['health_benefits'][:3]])
                        st.markdown(f"**Benefits:** {benefits}")
                
                with col2:
                    st.markdown(f"**Servings:** {recipe.get('servings', 'N/A')}")
                    st.markdown(f"**Prep:** {recipe.get('prep_time', 'N/A')} min")
                    st.markdown(f"**Cook:** {recipe.get('cook_time', 'N/A')} min")
                
                # Ingredients
                st.markdown("**Ingredients:**")
                ingredients = recipe.get('ingredients', [])
                
                if isinstance(ingredients, dict):
                    for section, ing_list in ingredients.items():
                        st.markdown(f"*{section.title()}:*")
                        for ing in ing_list[:5]:
                            if isinstance(ing, dict):
                                st.markdown(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                else:
                    for ing in ingredients[:5]:
                        if isinstance(ing, dict):
                            st.markdown(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                
                if len(ingredients) > 5:
                    st.caption(f"... and {len(ingredients) - 5} more ingredients")
                
                # Instructions preview
                instructions = recipe.get('instructions', [])
                if instructions:
                    st.markdown("**Instructions:**")
                    for i, instruction in enumerate(instructions[:2], 1):
                        st.markdown(f"{i}. {instruction}")
                    if len(instructions) > 2:
                        st.caption(f"... and {len(instructions) - 2} more steps")
    
    # TAB 4: View Results
    with tab4:
        if st.session_state.meal_plan is None:
            st.info("Generate a meal plan first to see results here")
        else:
            meal_plan = st.session_state.meal_plan
            
            # Sub-tabs for different views
            subtab1, subtab2, subtab3 = st.tabs(["📅 Meal Plan", "🛒 Shopping List", "📖 Recipes"])
            
            # SUBTAB 1: Meal Plan View
            with subtab1:
                st.header("📅 Your Meal Plan")
                
                for day in meal_plan['days']:
                    with st.expander(f"**Day {day['day']} - {day['day_name']}, {day['date']}**"):
                        for meal_type, meal_info in day['meals'].items():
                            meal_name = meal_type.replace('_', ' ').title()
                            recipe_name = meal_info['recipe']
                            cuisine = meal_info.get('cuisine', '')
                            timing = meal_info.get('time', '')
                            
                            if timing:
                                st.markdown(f"**{meal_name}** ({timing})")
                            else:
                                st.markdown(f"**{meal_name}**")
                            
                            st.markdown(f"→ {recipe_name}")
                            if cuisine:
                                st.caption(f"Cuisine: {cuisine}")
                            st.markdown("")
            
            # SUBTAB 2: Shopping List with Interactive Checklist
            with subtab2:
                # Generate shopping list if not already done
                if 'shopping_list' not in st.session_state:
                    with st.spinner("Generating shopping list..."):
                        generator = ShoppingListGenerator()
                        shopping_list = generator.generate_shopping_list(meal_plan)
                        st.session_state.shopping_list = shopping_list
                
                # Display interactive checklist with PDF download
                auth = FirebaseAuth()
                display_shopping_with_checklist(st.session_state.shopping_list, auth)
            
            # SUBTAB 3: Recipe Booklet with In-App Viewer and PDF
            with subtab3:
                auth = FirebaseAuth()
                display_recipe_booklet_with_pdf(meal_plan, st.session_state.planner, auth)


if __name__ == "__main__":
    main()
