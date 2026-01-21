#!/usr/bin/env python3
"""
Shopping List Generator
Aggregates ingredients from meal plan and organizes by store
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class ShoppingListGenerator:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize shopping list generator"""
        self.config = self._load_config(config_path)
        self.recipes = self._load_all_recipes()
        self.store_map = self._load_store_map()
        self.people = self.config['system']['people']
        
    def _load_config(self, config_path: str) -> Dict:
        """Load system configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_all_recipes(self) -> Dict[str, List[Dict]]:
        """Load all recipe files"""
        recipes = {}
        recipe_dir = Path('recipes')
        
        for recipe_file in recipe_dir.glob('*.yaml'):
            with open(recipe_file, 'r') as f:
                recipe_list = yaml.safe_load(f) or []
                for recipe in recipe_list:
                    recipes[recipe['name']] = recipe
        
        return recipes
    
    def _load_store_map(self) -> Dict:
        """Load ingredient to store mapping"""
        with open('data/ingredient_store_map.yaml', 'r') as f:
            return yaml.safe_load(f)
    
    def _find_store_for_ingredient(self, ingredient_name: str) -> str:
        """Find which store to buy ingredient from"""
        # Normalize ingredient name
        ing_lower = ingredient_name.lower().replace('_', ' ')
        
        # Search through store map
        for category, items in self.store_map.items():
            if isinstance(items, dict):
                for item_key, item_info in items.items():
                    item_key_normalized = item_key.replace('_', ' ')
                    
                    # Check for matches
                    if (item_key_normalized in ing_lower or 
                        ing_lower in item_key_normalized):
                        if isinstance(item_info, dict) and 'primary_store' in item_info:
                            store = item_info['primary_store']
                            # Skip if store is aldi (removed store)
                            if store == 'aldi':
                                return 'costco'
                            return store
        
        # Default to Costco if not found (bulk buying)
        return 'costco'
    
    def _convert_units(self, amount: float, unit: str) -> tuple:
        """Convert units to human-readable format"""
        
        # Teaspoon conversions
        if unit in ['tsp', 'teaspoon', 'teaspoons']:
            if amount >= 48:  # 1 cup = 48 tsp
                cups = amount / 48
                return (round(cups, 1), 'cup' if cups == 1 else 'cups')
            elif amount >= 3:  # 1 tbsp = 3 tsp
                tbsp = amount / 3
                return (round(tbsp, 1), 'tbsp')
        
        # Tablespoon conversions
        elif unit in ['tbsp', 'tablespoon', 'tablespoons']:
            if amount >= 16:  # 1 cup = 16 tbsp
                cups = amount / 16
                return (round(cups, 1), 'cup' if cups == 1 else 'cups')
        
        # Ounce conversions
        elif unit in ['oz', 'ounce', 'ounces']:
            if amount >= 16:  # 1 lb = 16 oz
                lbs = amount / 16
                return (round(lbs, 1), 'lb' if lbs == 1 else 'lbs')
        
        # Round the original amount
        if amount < 1:
            return (round(amount, 2), unit)
        else:
            return (round(amount, 1), unit)
    
    def _aggregate_ingredients(self, meal_plan: Dict) -> Dict[str, Dict]:
        """Aggregate ingredients from all meals in plan"""
        ingredient_totals = defaultdict(lambda: {
            'amount': 0,
            'unit': '',
            'items': [],
            'recipes': set()
        })
        
        # Iterate through each day
        for day in meal_plan['days']:
            for meal_type, meal_info in day['meals'].items():
                recipe_name = meal_info['recipe']
                servings_needed = meal_info.get('servings', 1)
                
                # Get recipe details
                if recipe_name not in self.recipes:
                    continue
                
                recipe = self.recipes[recipe_name]
                
                # Handle different ingredient structures
                ingredients = recipe.get('ingredients', [])
                
                # Some recipes have nested ingredient structures
                if isinstance(ingredients, dict):
                    # Flatten nested structure (like Ethiopian lentils)
                    flattened = []
                    for key, ing_list in ingredients.items():
                        if isinstance(ing_list, list):
                            flattened.extend(ing_list)
                    ingredients = flattened
                
                # Process each ingredient
                for ing in ingredients:
                    if not isinstance(ing, dict):
                        continue
                    
                    item = ing.get('item', '')
                    amount = ing.get('amount', 0)
                    unit = ing.get('unit', '')
                    
                    # Skip non-numeric amounts entirely
                    if isinstance(amount, str):
                        # List of non-numeric values to skip
                        skip_values = [
                            'varies', 'optional', '', 'to taste', 'as needed',
                            'pinch', 'dash', 'handful', 'sprinkle', 'as desired'
                        ]
                        if amount.lower() in skip_values:
                            continue
                        
                        # Handle fractions better
                        if '/' in amount:
                            try:
                                # Split fraction and convert
                                if ' ' in amount:  # Handle "1 1/2" format
                                    whole, frac = amount.split(' ', 1)
                                    num, denom = frac.split('/')
                                    amount = float(whole) + (float(num) / float(denom))
                                else:  # Handle "1/2" format
                                    num, denom = amount.split('/')
                                    amount = float(num) / float(denom)
                            except:
                                continue  # Skip if can't parse fraction
                        else:
                            try:
                                amount = float(amount)
                            except ValueError:
                                continue  # Skip if not a number
                    
                    # After parsing, skip if amount is negligible
                    if isinstance(amount, (int, float)) and amount < 0.1:
                        continue
                    
                    # Scale by servings if this is for multiple people
                    # Convert servings_needed to int to handle string values
                    try:
                        servings_int = int(servings_needed) if servings_needed != 'as desired' else 1
                    except (ValueError, TypeError):
                        servings_int = 1
                    
                    if servings_int > 1:
                        try:
                            # Try to multiply numeric amounts
                            if isinstance(amount, (int, float)):
                                amount = amount * servings_int
                        except:
                            pass
                    
                    # Aggregate
                    key = f"{item}_{unit}".lower()
                    ingredient_totals[key]['amount'] += amount if isinstance(amount, (int, float)) else 0
                    ingredient_totals[key]['unit'] = unit
                    ingredient_totals[key]['items'].append(item)
                    ingredient_totals[key]['recipes'].add(recipe_name)
        
        return ingredient_totals
    
    def generate_shopping_list(self, meal_plan: Dict) -> Dict[str, Any]:
        """Generate organized shopping list from meal plan"""
        # Aggregate all ingredients
        ingredient_totals = self._aggregate_ingredients(meal_plan)
        
        # Organize by store
        shopping_by_store = defaultdict(lambda: {
            'store_info': {},
            'items': []
        })
        
        for ing_key, ing_data in ingredient_totals.items():
            item_name = ing_data['items'][0] if ing_data['items'] else ing_key
            store = self._find_store_for_ingredient(item_name)
            
            # Get store info
            store_info = self.config['stores'].get(store, {})
            shopping_by_store[store]['store_info'] = {
                'type': store_info.get('type', ''),
                'best_for': store_info.get('best_for', [])
            }
            
            # Format amount with unit conversion
            amount = ing_data['amount']
            unit = ing_data['unit']
            
            # Convert to better units
            amount, unit = self._convert_units(amount, unit)
            
            # Format the amount
            if isinstance(amount, float):
                if amount < 1:
                    amount = f"{amount:.2f}"
                else:
                    amount = f"{amount:.1f}"
            
            shopping_by_store[store]['items'].append({
                'item': item_name,
                'amount': amount,
                'unit': unit,
                'used_in': list(ing_data['recipes'])[:3]  # Show first 3 recipes
            })
        
        # Create final shopping list structure
        shopping_list = {
            'meal_plan_dates': f"{meal_plan['start_date']} to {meal_plan['end_date']}",
            'people': meal_plan['people'],
            'budget': self.config['system']['budget_per_cycle'],
            'stores': {}
        }
        
        # Sort stores by priority (Costco first for bulk, then others)
        store_priority = ['costco', 'petes_produce', 'aldi', 'whole_foods']
        
        for store in store_priority:
            if store in shopping_by_store:
                shopping_list['stores'][store] = shopping_by_store[store]
        
        # Add any remaining stores
        for store in shopping_by_store:
            if store not in shopping_list['stores']:
                shopping_list['stores'][store] = shopping_by_store[store]
        
        return shopping_list
    
    def save_shopping_list(self, shopping_list: Dict, output_dir: str = "output") -> str:
        """Save shopping list to YAML file"""
        Path(output_dir).mkdir(exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/shopping_list_{timestamp}.yaml"
        
        with open(filename, 'w') as f:
            yaml.dump(shopping_list, f, default_flow_style=False, sort_keys=False)
        
        return filename


if __name__ == "__main__":
    # Test the shopping list generator
    # First, we need a meal plan
    import sys
    sys.path.append('.')
    from src.meal_planner import MealPlanner
    
    planner = MealPlanner()
    meal_plan = planner.generate_meal_plan()
    
    # Generate shopping list
    generator = ShoppingListGenerator()
    shopping_list = generator.generate_shopping_list(meal_plan)
    
    # Print summary
    print(f"Shopping List for {shopping_list['meal_plan_dates']}")
    print(f"Budget: ${shopping_list['budget']}\n")
    
    for store_name, store_data in shopping_list['stores'].items():
        print(f"\n{store_name.upper().replace('_', ' ')}")
        print(f"Type: {store_data['store_info'].get('type', 'N/A')}")
        print(f"Items: {len(store_data['items'])}")
        
        # Show first 5 items as sample
        for item in store_data['items'][:5]:
            print(f"  - {item['amount']} {item['unit']} {item['item']}")
        
        if len(store_data['items']) > 5:
            print(f"  ... and {len(store_data['items']) - 5} more items")
    
    # Save
    filename = generator.save_shopping_list(shopping_list)
    print(f"\n\nFull shopping list saved to: {filename}")
