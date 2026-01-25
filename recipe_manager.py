"""
Recipe Management Admin Panel
Add, edit, browse, and manage recipes with serving size tracking
"""

import streamlit as st
import yaml
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class RecipeManager:
    """Manage recipes with YAML file storage"""
    
    def __init__(self, recipes_dir: str = "recipes"):
        self.recipes_dir = Path(recipes_dir)
        self.recipes_dir.mkdir(exist_ok=True)
        
        self.categories = [
            'breakfast',
            'breakfast_londons_originals',
            'lunch_dinner_italian',
            'lunch_dinner_african',
            'lunch_dinner_caribbean',
            'lunch_dinner_asian',
            'lunch_dinner_mediterranean',
            'snacks',
            'sweet_treats'
        ]
        
        self.cuisines = [
            'African American Soul',
            'West African',
            'Caribbean',
            'Mediterranean',
            'Italian',
            'Asian',
            'Latin American',
            'Ethiopian',
            'Classic American'
        ]
        
        self.meal_types = [
            'breakfast',
            'lunch_or_dinner',
            'snack',
            'sweet_treat'
        ]
    
    def load_recipes_from_category(self, category: str) -> List[Dict]:
        """Load all recipes from a category file"""
        file_path = self.recipes_dir / f"{category}.yaml"
        
        if not file_path.exists():
            return []
        
        with open(file_path, 'r') as f:
            recipes = yaml.safe_load(f) or []
        
        return recipes
    
    def save_recipes_to_category(self, category: str, recipes: List[Dict]) -> bool:
        """Save recipes to category file"""
        try:
            file_path = self.recipes_dir / f"{category}.yaml"
            
            with open(file_path, 'w') as f:
                yaml.dump(recipes, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            return True
        except Exception as e:
            st.error(f"Error saving recipes: {e}")
            return False
    
    def add_recipe(self, category: str, recipe: Dict) -> bool:
        """Add a new recipe to a category"""
        recipes = self.load_recipes_from_category(category)
        recipes.append(recipe)
        return self.save_recipes_to_category(category, recipes)
    
    def update_recipe(self, category: str, recipe_index: int, updated_recipe: Dict) -> bool:
        """Update an existing recipe"""
        recipes = self.load_recipes_from_category(category)
        
        if 0 <= recipe_index < len(recipes):
            recipes[recipe_index] = updated_recipe
            return self.save_recipes_to_category(category, recipes)
        
        return False
    
    def delete_recipe(self, category: str, recipe_index: int) -> bool:
        """Delete a recipe"""
        recipes = self.load_recipes_from_category(category)
        
        if 0 <= recipe_index < len(recipes):
            del recipes[recipe_index]
            return self.save_recipes_to_category(category, recipes)
        
        return False
    
    def search_recipes(self, query: str) -> List[Dict]:
        """Search for recipes across all categories"""
        results = []
        query_lower = query.lower()
        
        for category in self.categories:
            recipes = self.load_recipes_from_category(category)
            
            for idx, recipe in enumerate(recipes):
                name = recipe.get('name', '').lower()
                cuisine = recipe.get('cuisine', '').lower()
                
                if query_lower in name or query_lower in cuisine:
                    results.append({
                        'category': category,
                        'index': idx,
                        'recipe': recipe
                    })
        
        return results


def show_recipe_admin():
    """Recipe administration interface"""
    
    st.header("🍳 Recipe Management")
    st.caption("Add, edit, and manage your meal prep recipes")
    
    manager = RecipeManager()
    
    # Tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Browse Recipes", "➕ Add Recipe", "✏️ Edit Recipe", "📋 Bulk Import"])
    
    # TAB 1: Browse Recipes
    with tab1:
        st.subheader("Browse All Recipes")
        
        # Search
        search_query = st.text_input("🔍 Search recipes", placeholder="e.g., chicken, Italian, breakfast")
        
        if search_query:
            results = manager.search_recipes(search_query)
            
            if results:
                st.write(f"Found {len(results)} recipe(s)")
                
                for result in results:
                    recipe = result['recipe']
                    with st.expander(f"**{recipe['name']}** ({recipe.get('cuisine', 'N/A')})"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Category:** {result['category']}")
                        with col2:
                            st.write(f"**Servings:** {recipe.get('servings', 'N/A')}")
                        with col3:
                            st.write(f"**Cuisine:** {recipe.get('cuisine', 'N/A')}")
                        
                        if 'ingredients' in recipe:
                            st.write("**Ingredients:**")
                            for ing in recipe['ingredients'][:5]:
                                if isinstance(ing, dict):
                                    st.write(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                        
                        if len(recipe.get('ingredients', [])) > 5:
                            st.caption(f"... and {len(recipe['ingredients']) - 5} more ingredients")
            else:
                st.info("No recipes found")
        else:
            # Show by category
            category = st.selectbox("Select category to browse", manager.categories)
            recipes = manager.load_recipes_from_category(category)
            
            if recipes:
                st.write(f"**{len(recipes)} recipe(s) in {category}:**")
                
                for idx, recipe in enumerate(recipes):
                    with st.expander(f"{idx + 1}. {recipe['name']}"):
                        st.json(recipe)
            else:
                st.info(f"No recipes in {category}")
    
    # TAB 2: Add New Recipe
    with tab2:
        st.subheader("Add New Recipe")
        
        with st.form("add_recipe_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                recipe_name = st.text_input("Recipe Name *", placeholder="e.g., Jollof-Style Savory Grits")
                cuisine = st.selectbox("Cuisine *", manager.cuisines)
                meal_type = st.selectbox("Meal Type *", manager.meal_types)
                category = st.selectbox("Category File *", manager.categories)
            
            with col2:
                servings = st.number_input("Servings *", min_value=1, max_value=12, value=2, 
                                          help="How many people this recipe serves (for ML scaling)")
                prep_time = st.number_input("Prep Time (min)", min_value=0, value=10)
                cook_time = st.number_input("Cook Time (min)", min_value=0, value=15)
            
            st.markdown("---")
            st.subheader("Ingredients")
            st.caption("Add ingredients one at a time")
            
            # Dynamic ingredient fields
            if 'new_ingredients' not in st.session_state:
                st.session_state.new_ingredients = []
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
            with col1:
                ing_amount = st.text_input("Amount", key="ing_amount", placeholder="1/2")
            with col2:
                ing_unit = st.text_input("Unit", key="ing_unit", placeholder="cup")
            with col3:
                if st.form_submit_button("Add Ingredient"):
                    if ing_amount and st.session_state.get('ing_item'):
                        st.session_state.new_ingredients.append({
                            'amount': ing_amount,
                            'unit': ing_unit,
                            'item': st.session_state.ing_item,
                            'prep': st.session_state.get('ing_prep', '')
                        })
            with col4:
                ing_item = st.text_input("Ingredient", key="ing_item", placeholder="sweet potato")
            
            ing_prep = st.text_input("Prep (optional)", key="ing_prep", placeholder="diced small")
            
            # Show current ingredients
            if st.session_state.new_ingredients:
                st.write("**Current Ingredients:**")
                for i, ing in enumerate(st.session_state.new_ingredients):
                    st.write(f"{i+1}. {ing['amount']} {ing['unit']} {ing['item']} {f'({ing['prep']})' if ing.get('prep') else ''}")
            
            st.markdown("---")
            st.subheader("Instructions")
            instructions = st.text_area("Cooking Instructions (one per line)", 
                                       placeholder="Step 1\nStep 2\nStep 3...", 
                                       height=150)
            
            cultural_note = st.text_input("Cultural Note (optional)", 
                                         placeholder="e.g., Jollof rice meets Southern grits")
            
            submitted = st.form_submit_button("💾 Save Recipe", type="primary")
            
            if submitted:
                if not recipe_name or not cuisine or not servings:
                    st.error("Please fill in all required fields (*)")
                elif not st.session_state.new_ingredients:
                    st.error("Please add at least one ingredient")
                else:
                    # Build recipe dict
                    new_recipe = {
                        'name': recipe_name,
                        'cuisine': cuisine,
                        'meal_type': meal_type,
                        'servings': servings,
                        'prep_time': prep_time,
                        'cook_time': cook_time,
                        'ingredients': st.session_state.new_ingredients,
                        'instructions': instructions.split('\n') if instructions else [],
                    }
                    
                    if cultural_note:
                        new_recipe['cultural_note'] = cultural_note
                    
                    # Save
                    if manager.add_recipe(category, new_recipe):
                        st.success(f"✓ Added '{recipe_name}' to {category}!")
                        st.session_state.new_ingredients = []  # Clear
                        st.rerun()
                    else:
                        st.error("Failed to save recipe")
    
    # TAB 3: Edit Recipe
    with tab3:
        st.subheader("Edit Existing Recipe")
        
        category = st.selectbox("Select category", manager.categories, key="edit_category")
        recipes = manager.load_recipes_from_category(category)
        
        if recipes:
            recipe_names = [r['name'] for r in recipes]
            selected_name = st.selectbox("Select recipe", recipe_names)
            selected_index = recipe_names.index(selected_name)
            selected_recipe = recipes[selected_index]
            
            st.json(selected_recipe)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit in Form"):
                    st.info("Edit form coming soon - for now, use Bulk Import tab to modify YAML directly")
            with col2:
                if st.button("🗑️ Delete Recipe", type="secondary"):
                    if manager.delete_recipe(category, selected_index):
                        st.success(f"Deleted '{selected_name}'")
                        st.rerun()
        else:
            st.info(f"No recipes in {category}")
    
    # TAB 4: Bulk Import
    with tab4:
        st.subheader("Bulk Import Recipes (YAML)")
        st.caption("Paste YAML directly to add multiple recipes at once")
        
        category = st.selectbox("Target category", manager.categories, key="bulk_category")
        
        yaml_text = st.text_area("Paste YAML here", height=400, placeholder="""- name: "Recipe Name"
  cuisine: "Italian"
  meal_type: breakfast
  servings: 2
  ingredients:
    - item: "eggs"
      amount: 2
      unit: "whole"
""")
        
        if st.button("📋 Import Recipes", type="primary"):
            try:
                imported = yaml.safe_load(yaml_text)
                
                if not isinstance(imported, list):
                    imported = [imported]
                
                # Validate each recipe has required fields
                valid = True
                for recipe in imported:
                    if not all(k in recipe for k in ['name', 'servings']):
                        st.error(f"Recipe missing required fields: {recipe.get('name', 'Unknown')}")
                        valid = False
                
                if valid:
                    # Get existing recipes
                    existing = manager.load_recipes_from_category(category)
                    existing.extend(imported)
                    
                    if manager.save_recipes_to_category(category, existing):
                        st.success(f"✓ Imported {len(imported)} recipe(s) to {category}!")
                    else:
                        st.error("Failed to save recipes")
                        
            except yaml.YAMLError as e:
                st.error(f"YAML parsing error: {e}")
            except Exception as e:
                st.error(f"Error: {e}")


# For testing standalone
if __name__ == "__main__":
    show_recipe_admin()
