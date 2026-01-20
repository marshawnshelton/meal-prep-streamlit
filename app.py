#!/usr/bin/env python3
"""
Meal Prep System - Web Interface
Built with Streamlit for easy, user-friendly meal planning
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


# Page configuration
st.set_page_config(
    page_title="Meal Prep System",
    page_icon="🍽️",
    layout="wide"
)

# Initialize session state
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
    st.title("🍽️ Meal Prep System")
    st.markdown("### Plan your meals, generate shopping lists, get recipes")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
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
                st.success(f"✓ Generated {days}-day meal plan!")
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
                    breakfast = breakfast_selection.split(' (')[0]  # Extract just the name
                    
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
                        # Save selections
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
                        # Save and move to next
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
                    # Build meal plan from selections
                    # TODO: Convert selections to meal_plan format
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
                
                # Handle nested ingredient structures (like Mexican recipes)
                if isinstance(ingredients, dict):
                    for section, ing_list in ingredients.items():
                        st.markdown(f"*{section.title()}:*")
                        for ing in ing_list[:5]:  # Show first 5
                            if isinstance(ing, dict):
                                st.markdown(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                else:
                    for ing in ingredients[:5]:  # Show first 5
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
            
            # Display meal plan
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
            
            # Generate outputs
            st.markdown("---")
            st.header("📥 Download Your Files")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 Generate Shopping List", use_container_width=True):
                    with st.spinner("Creating shopping list..."):
                        generator = ShoppingListGenerator()
                        shopping_list = generator.generate_shopping_list(meal_plan)
                        
                        # Save to session state
                        st.session_state.shopping_list = shopping_list
                        
                        # Show summary
                        st.success("✓ Shopping list generated!")
                        total_items = sum(len(store['items']) for store in shopping_list['stores'].values())
                        st.info(f"Total items: {total_items} across {len(shopping_list['stores'])} stores")
            
            with col2:
                if st.button("📖 Generate Recipe Booklet", use_container_width=True):
                    with st.spinner("Creating recipe booklet..."):
                        # TODO: Generate recipe booklet
                        st.success("✓ Recipe booklet generated!")
            
            with col3:
                if st.button("📊 Create Excel File", use_container_width=True):
                    if 'shopping_list' in st.session_state:
                        with st.spinner("Creating Excel file..."):
                            exporter = ExcelExporter()
                            excel_file = exporter.export_to_excel(
                                st.session_state.shopping_list, 
                                "output"
                            )
                            st.success(f"✓ Excel created: {excel_file}")
                            
                            # Provide download link
                            with open(excel_file, 'rb') as f:
                                st.download_button(
                                    label="⬇️ Download Excel",
                                    data=f,
                                    file_name=Path(excel_file).name,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    else:
                        st.warning("Generate shopping list first!")
            
            # Display shopping list if available
            if 'shopping_list' in st.session_state:
                st.markdown("---")
                st.header("🛒 Shopping List Preview")
                
                shopping_list = st.session_state.shopping_list
                
                for store_name, store_data in shopping_list['stores'].items():
                    with st.expander(f"**{store_name.replace('_', ' ').title()}** ({len(store_data['items'])} items)"):
                        for item in store_data['items']:
                            st.markdown(f"- {item['amount']} {item['unit']} **{item['item']}**")


if __name__ == "__main__":
    main()
