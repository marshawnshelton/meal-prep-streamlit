#!/usr/bin/env python3
"""
Meal Planning Engine
Generates diverse 14-day meal plans with cultural variety
"""

import yaml
import random
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta


class MealPlanner:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the meal planner with configuration"""
        self.config = self._load_config(config_path)
        self.recipes = self._load_all_recipes()
        self.planning_days = self.config['system']['planning_cycle_days']
        
    def _load_config(self, config_path: str) -> Dict:
        """Load system configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_all_recipes(self) -> Dict[str, List[Dict]]:
        """Load all recipe files"""
        recipes = {
            'breakfast': [],
            'lunch_dinner': [],
            'snacks': [],
            'sweet_treats': []
        }
        
        recipe_dir = Path('recipes')
        for recipe_file in recipe_dir.glob('*.yaml'):
            category = recipe_file.stem
            with open(recipe_file, 'r') as f:
                recipes[category] = yaml.safe_load(f) or []
        
        return recipes
    
    def _filter_recipes_by_proteins(self, recipes: List[Dict]) -> List[Dict]:
        """Filter recipes that only use allowed proteins"""
        allowed_proteins = set(self.config['dietary_goals']['protein_sources'])
        excluded = set(self.config['dietary_goals']['excluded_ingredients'])
        
        filtered = []
        for recipe in recipes:
            # Check if recipe uses any excluded ingredients
            has_excluded = False
            if 'ingredients' in recipe:
                for ing in recipe['ingredients']:
                    if isinstance(ing, dict) and 'item' in ing:
                        item_lower = ing['item'].lower()
                        for excluded_item in excluded:
                            if excluded_item.replace('_', ' ') in item_lower:
                                has_excluded = True
                                break
            
            if not has_excluded:
                filtered.append(recipe)
        
        return filtered
    
    def _ensure_variety(self, selected_recipes: List[Dict], new_recipe: Dict, 
                       lookback_days: int = 3) -> bool:
        """Ensure we don't repeat same cuisine or protein too frequently"""
        if len(selected_recipes) < lookback_days:
            lookback_days = len(selected_recipes)
        
        recent = selected_recipes[-lookback_days:]
        
        # Check cuisine variety
        recent_cuisines = [r.get('cuisine', '') for r in recent]
        if new_recipe.get('cuisine', '') in recent_cuisines:
            return False
        
        # Check protein variety (if applicable)
        new_proteins = self._extract_proteins(new_recipe)
        for recent_recipe in recent:
            recent_proteins = self._extract_proteins(recent_recipe)
            if new_proteins & recent_proteins:  # If there's overlap
                return False
        
        return True
    
    def _extract_proteins(self, recipe: Dict) -> set:
        """Extract protein types from recipe"""
        proteins = set()
        protein_keywords = ['chicken', 'turkey', 'salmon', 'fish', 'catfish', 
                          'barramundi', 'whiting', 'duck', 'lobster', 'crab']
        
        if 'ingredients' in recipe:
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'item' in ing:
                    item_lower = ing['item'].lower()
                    for protein in protein_keywords:
                        if protein in item_lower:
                            proteins.add(protein)
        
        return proteins
    
    def generate_meal_plan(self, start_date: datetime = None) -> Dict[str, Any]:
        """Generate a 14-day meal plan with variety"""
        if start_date is None:
            start_date = datetime.now()
        
        meal_plan = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': (start_date + timedelta(days=self.planning_days - 1)).strftime('%Y-%m-%d'),
            'people': self.config['system']['people'],
            'days': []
        }
        
        # Get filtered recipes
        breakfasts = self._filter_recipes_by_proteins(self.recipes['breakfast'])
        lunch_dinners = self._filter_recipes_by_proteins(self.recipes['lunch_dinner'])
        snacks = self.recipes['snacks']
        treats = self.recipes['sweet_treats']
        
        selected_lunches = []
        selected_dinners = []
        
        for day_num in range(self.planning_days):
            current_date = start_date + timedelta(days=day_num)
            day_name = current_date.strftime('%A')
            
            # Select breakfast (with variety)
            breakfast_options = [b for b in breakfasts 
                               if self._ensure_variety(meal_plan['days'], b, 4)]
            if not breakfast_options:
                breakfast_options = breakfasts
            breakfast = random.choice(breakfast_options)
            
            # Select morning snack (alternate between different types)
            snack_am_options = [s for s in snacks if s.get('name') != 'Greek Yogurt Power Bowl']
            if day_num % 3 == 0:  # Yogurt every 3rd day
                snack_am_options = [s for s in snacks if 'Yogurt' in s.get('name', '')]
            snack_am = random.choice(snack_am_options) if snack_am_options else snacks[0]
            
            # Select lunch (with variety)
            lunch_options = [l for l in lunch_dinners 
                           if self._ensure_variety(selected_lunches, l, 3)]
            if not lunch_options:
                lunch_options = lunch_dinners
            lunch = random.choice(lunch_options)
            selected_lunches.append(lunch)
            
            # Select afternoon snack
            snack_pm_options = [s for s in snacks 
                              if s.get('name') != snack_am.get('name')]
            snack_pm = random.choice(snack_pm_options)
            
            # Select dinner (with variety, and different from lunch)
            dinner_options = [d for d in lunch_dinners 
                            if d.get('name') != lunch.get('name') 
                            and self._ensure_variety(selected_dinners, d, 3)]
            if not dinner_options:
                dinner_options = [d for d in lunch_dinners 
                                if d.get('name') != lunch.get('name')]
            dinner = random.choice(dinner_options)
            selected_dinners.append(dinner)
            
            # Occasionally add a sweet treat (2-3 times per week)
            treat = None
            if day_num % 3 == 0 or day_num % 5 == 0:
                treat = random.choice(treats)
            
            day_meals = {
                'day': day_num + 1,
                'date': current_date.strftime('%Y-%m-%d'),
                'day_name': day_name,
                'meals': {
                    'breakfast': {
                        'time': self.config['meal_structure']['breakfast']['timing'],
                        'recipe': breakfast['name'],
                        'cuisine': breakfast.get('cuisine', ''),
                        'servings': 1
                    },
                    'snack_morning': {
                        'time': self.config['meal_structure']['snack_morning']['timing'],
                        'recipe': snack_am['name'],
                        'servings': 1
                    },
                    'lunch': {
                        'time': self.config['meal_structure']['lunch']['timing'],
                        'recipe': lunch['name'],
                        'cuisine': lunch.get('cuisine', ''),
                        'servings': self.config['system']['people']
                    },
                    'snack_afternoon': {
                        'time': self.config['meal_structure']['snack_afternoon']['timing'],
                        'recipe': snack_pm['name'],
                        'servings': 1
                    },
                    'dinner': {
                        'time': self.config['meal_structure']['dinner']['timing'],
                        'recipe': dinner['name'],
                        'cuisine': dinner.get('cuisine', ''),
                        'servings': self.config['system']['people']
                    }
                }
            }
            
            if treat:
                day_meals['meals']['sweet_treat'] = {
                    'recipe': treat['name'],
                    'cuisine': treat.get('cuisine', ''),
                    'servings': 'as desired'
                }
            
            meal_plan['days'].append(day_meals)
        
        return meal_plan
    
    def save_meal_plan(self, meal_plan: Dict, output_dir: str = "output") -> str:
        """Save meal plan to YAML file"""
        Path(output_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/meal_plan_{timestamp}.yaml"
        
        with open(filename, 'w') as f:
            yaml.dump(meal_plan, f, default_flow_style=False, sort_keys=False)
        
        return filename


if __name__ == "__main__":
    # Test the meal planner
    planner = MealPlanner()
    plan = planner.generate_meal_plan()
    
    # Print summary
    print(f"Generated {len(plan['days'])}-day meal plan")
    print(f"Start: {plan['start_date']}")
    print(f"End: {plan['end_date']}")
    print(f"For {plan['people']} people\n")
    
    # Show first day as example
    first_day = plan['days'][0]
    print(f"Day 1 - {first_day['day_name']} ({first_day['date']}):")
    for meal_name, meal_info in first_day['meals'].items():
        print(f"  {meal_name.replace('_', ' ').title()}: {meal_info['recipe']}")
    
    # Save
    filename = planner.save_meal_plan(plan)
    print(f"\nFull meal plan saved to: {filename}")
