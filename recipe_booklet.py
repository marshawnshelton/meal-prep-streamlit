"""
Simplified Recipe Booklet - Guaranteed to work!
"""

import streamlit as st
from datetime import datetime


def display_recipe_booklet_with_pdf(meal_plan, planner, auth):
    """Display recipe booklet in-app"""
    
    st.header("📖 Recipe Booklet")
    
    # Get unique recipes
    unique_recipes = set()
    for day in meal_plan['days']:
        for meal_type, meal_info in day.get('meals', {}).items():
            if meal_info and meal_info.get('recipe'):
                unique_recipes.add(meal_info['recipe'])
    
    st.markdown(f"### {len(unique_recipes)} Recipes in Your Plan")
    st.markdown(f"**Meal Plan:** {meal_plan['start_date']} to {meal_plan['end_date']}")
    st.markdown("---")
    
    # Display each recipe
    for i, recipe_name in enumerate(sorted(unique_recipes), 1):
        # Find recipe
        recipe = None
        for category, recipes in planner.recipes.items():
            for r in recipes:
                if r['name'] == recipe_name:
                    recipe = r
                    break
            if recipe:
                break
        
        if recipe:
            with st.expander(f"**{i}. {recipe['name']}** - {recipe.get('cuisine', 'N/A')}", 
                           expanded=(i == 1)):
                
                # Basic info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Servings", recipe.get('servings', 'N/A'))
                with col2:
                    st.metric("Prep", f"{recipe.get('prep_time', 'N/A')} min")
                with col3:
                    st.metric("Cook", f"{recipe.get('cook_time', 'N/A')} min")
                
                st.markdown("---")
                
                # Ingredients
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
                
                # Instructions
                st.markdown("### 👩‍🍳 Instructions")
                instructions = recipe.get('instructions', [])
                for j, step in enumerate(instructions, 1):
                    st.markdown(f"**{j}.** {step}")
                
                # Cultural note
                if recipe.get('cultural_note'):
                    st.markdown("---")
                    st.info(f"💡 {recipe.get('cultural_note')}")
    
    st.markdown("---")
    st.caption("💡 PDF download feature coming in next update!")
