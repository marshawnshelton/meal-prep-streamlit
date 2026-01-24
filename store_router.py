"""
Smart Store Routing System
Intelligently routes ingredients to appropriate stores based on:
- Quantity needed
- Item type (produce, pantry, protein, etc.)
- Store characteristics (bulk, specialty, budget)
"""

import yaml
from typing import Dict, List, Tuple


class StoreRouter:
    """Routes ingredients to optimal stores based on quantity and type"""
    
    def __init__(self):
        self.store_profiles = {
            'costco': {
                'name': 'Costco',
                'type': 'bulk',
                'min_quantity': 3.0,  # Don't route items < 3 cups/lbs here
                'good_for': ['pantry_staples', 'bulk_proteins', 'frozen', 'large_quantities'],
                'avoid': ['fresh_herbs', 'small_produce', 'specialty_items', 'spices_and_seasonings'],
                'package_sizes': 'large'
            },
            'whole_foods': {
                'name': 'Whole Foods',
                'type': 'specialty',
                'min_quantity': 0.0,  # Any quantity OK
                'good_for': ['fresh_produce', 'specialty_items', 'small_quantities', 'organic', 
                            'fresh_herbs', 'spices_and_seasonings', 'oils_and_liquids'],
                'package_sizes': 'small_to_medium'
            },
            'petes_fresh_market': {  # FIXED: Changed from 'petes'
                'name': "Pete's Fresh Market",
                'type': 'specialty',
                'min_quantity': 0.0,
                'good_for': ['fresh_produce', 'ethnic_ingredients', 'small_quantities',
                            'fresh_herbs', 'spices_and_seasonings'],
                'package_sizes': 'small'
            },
            'aldi': {
                'name': 'Aldi',
                'type': 'budget',
                'min_quantity': 0.0,
                'good_for': ['budget_staples', 'medium_quantities', 'frozen', 'pantry_staples',
                            'dairy_and_eggs'],
                'package_sizes': 'medium'
            },
            'jewel': {
                'name': 'Jewel-Osco',
                'type': 'convenience',
                'min_quantity': 0.0,
                'good_for': ['convenience', 'any_quantity', 'last_minute', 'dairy_and_eggs'],
                'package_sizes': 'all_sizes'
            }
        }
        
        # Categorize ingredients by type
        self.ingredient_categories = {
            'pantry_staples': [
                'rice', 'pasta', 'flour', 'sugar', 'salt', 'soy sauce', 'vinegar', 'honey',
                'beans', 'lentils', 'quinoa', 'oats', 'cornmeal'
            ],
            'oils_and_liquids': [
                'oil', 'olive oil', 'vegetable oil', 'canola oil', 'sesame oil', 
                'coconut oil', 'vinegar', 'stock', 'broth', 'wine'
            ],
            'spices_and_seasonings': [
                'paprika', 'cumin', 'coriander', 'turmeric', 'cinnamon', 'pepper',
                'chili powder', 'cayenne', 'nutmeg', 'cardamom', 'cloves',
                'ginger', 'garlic powder', 'onion powder', 'oregano', 'thyme',
                'bay leaf', 'sage', 'rosemary', 'mustard', 'curry'
            ],
            'fresh_produce': [
                'lettuce', 'spinach', 'tomato', 'onion', 'garlic', 'carrot',
                'celery', 'bell pepper', 'cucumber', 'potato', 'broccoli',
                'cabbage', 'kale', 'zucchini', 'squash', 'eggplant', 'mushroom',
                'corn', 'peas', 'green beans', 'asparagus', 'cauliflower'
            ],
            'fresh_herbs': [
                'cilantro', 'parsley', 'basil', 'mint', 'rosemary', 'thyme',
                'oregano', 'dill', 'chives', 'tarragon', 'sage'
            ],
            'bulk_proteins': [
                'chicken breast', 'chicken thigh', 'ground beef', 'ground turkey', 
                'pork chops', 'salmon', 'tilapia', 'shrimp', 'beef', 'pork',
                'turkey', 'lamb', 'fish', 'chicken'
            ],
            'dairy_and_eggs': [
                'milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream',
                'eggs', 'half and half', 'cottage cheese', 'cream cheese'
            ],
            'specialty_items': [
                'tahini', 'miso paste', 'fish sauce', 'gochujang', 'harissa',
                'coconut milk', 'curry paste', 'anchovy', 'capers', 'olives',
                'sun-dried tomato', 'artichoke', 'pesto'
            ],
            'ethnic_ingredients': [
                'kimchi', 'gochujang', 'miso', 'fish sauce', 'tamarind',
                'turmeric', 'cumin', 'coriander', 'curry', 'garam masala',
                'soy sauce', 'rice wine', 'sake', 'mirin'
            ]
        }
    
    def categorize_ingredient(self, ingredient_name: str) -> str:
        """Determine ingredient category"""
        ingredient_lower = ingredient_name.lower()
        
        for category, ingredients in self.ingredient_categories.items():
            for ing in ingredients:
                if ing in ingredient_lower:
                    return category
        
        # Default category
        return 'general'
    
    def convert_to_standard_unit(self, amount: float, unit: str) -> float:
        """Convert various units to standard 'cups' for comparison"""
        # Handle string amounts
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            print(f"[WARNING] Could not convert amount '{amount}' to float, using 1.0")
            amount = 1.0
        
        conversions = {
            'cup': 1.0,
            'cups': 1.0,
            'tablespoon': 0.0625,
            'tablespoons': 0.0625,
            'tbsp': 0.0625,
            'teaspoon': 0.0208,
            'teaspoons': 0.0208,
            'tsp': 0.0208,
            'pound': 2.0,  # Roughly 2 cups per pound for liquids
            'pounds': 2.0,
            'lb': 2.0,
            'lbs': 2.0,
            'ounce': 0.125,
            'ounces': 0.125,
            'oz': 0.125,
            'gram': 0.004,  # Very rough
            'grams': 0.004,
            'g': 0.004,
            'liter': 4.227,
            'liters': 4.227,
            'l': 4.227,
            'milliliter': 0.004,
            'milliliters': 0.004,
            'ml': 0.004,
            'pinch': 0.01,  # Very small
            'dash': 0.01,
            'to taste': 0.01
        }
        
        unit_lower = unit.lower().strip() if unit else 'cup'
        multiplier = conversions.get(unit_lower, 1.0)
        
        return amount * multiplier
    
    def get_store_profile(self, store_id: str) -> dict:
        """Get store profile with flexible ID matching"""
        # Try exact match first
        if store_id in self.store_profiles:
            return self.store_profiles[store_id]
        
        # Try normalized (lowercase, no underscores)
        normalized = store_id.lower().replace('_', '').replace(' ', '')
        
        for profile_id, profile in self.store_profiles.items():
            profile_normalized = profile_id.lower().replace('_', '').replace(' ', '')
            if normalized == profile_normalized:
                return profile
        
        # Return default profile
        return {
            'name': store_id.replace('_', ' ').title(),
            'type': 'convenience',
            'min_quantity': 0.0,
            'good_for': ['convenience', 'any_quantity'],
            'avoid': [],
            'package_sizes': 'all_sizes'
        }
    
    def score_store_for_ingredient(self, store_id: str, ingredient: dict, 
                                   quantity_in_cups: float) -> float:
        """Score how suitable a store is for this ingredient (0-100)"""
        profile = self.get_store_profile(store_id)  # Use flexible matching
        score = 50  # Start neutral
        
        ingredient_name = ingredient.get('item', '').lower()
        category = self.categorize_ingredient(ingredient_name)
        
        # AGGRESSIVE: Heavily penalize Costco for small quantities
        if store_id == 'costco':
            if quantity_in_cups < 0.5:  # Less than half cup
                score -= 60  # Almost disqualify
            elif quantity_in_cups < 1.0:  # Less than 1 cup
                score -= 40
            elif quantity_in_cups < 2.0:  # Less than 2 cups
                score -= 25
            elif quantity_in_cups < 3.0:  # Less than 3 cups
                score -= 15
        
        # Check minimum quantity requirement
        if quantity_in_cups < profile['min_quantity']:
            score -= 30  # Additional penalty
        
        # Check if item type matches store strengths
        if category in profile['good_for']:
            score += 30
        
        # Check if item type is in avoid list
        if category in profile.get('avoid', []):
            score -= 40
        
        # Bonus for bulk items at bulk stores
        if profile['type'] == 'bulk' and quantity_in_cups >= 5.0:
            score += 30  # Increased from 20
        
        # Bonus for small items at specialty stores
        if profile['type'] == 'specialty' and quantity_in_cups < 2.0:
            score += 25  # Increased from 15
        
        # Extra bonus for very small items at specialty stores
        if profile['type'] == 'specialty' and quantity_in_cups < 0.5:
            score += 20  # New bonus
        
        # Fresh herbs should STRONGLY prefer specialty stores
        if category == 'fresh_herbs':
            if profile['type'] == 'specialty':
                score += 40  # Strong bonus
            elif profile['type'] == 'bulk':
                score -= 60  # Strong penalty
        
        # Spices and seasonings should prefer specialty
        if 'powder' in ingredient_name or 'paprika' in ingredient_name or 'cumin' in ingredient_name:
            if profile['type'] == 'specialty' and quantity_in_cups < 1.0:
                score += 30
            elif profile['type'] == 'bulk' and quantity_in_cups < 1.0:
                score -= 40
        
        return max(0, min(100, score))  # Clamp between 0-100
    
    def route_ingredients(self, shopping_list: dict, selected_stores: List[str]) -> dict:
        """
        Intelligently route ingredients to best stores
        
        Args:
            shopping_list: Current shopping list with stores
            selected_stores: List of store IDs user selected
        
        Returns:
            Updated shopping list with optimized routing
        """
        # Build new routing from scratch
        new_routing = {store: [] for store in selected_stores}
        
        # Collect ALL unique ingredients across ALL stores (ignore original assignment)
        all_ingredients = {}
        for store_name, store_data in shopping_list.get('stores', {}).items():
            for item in store_data.get('items', []):
                item_key = item['item'].lower().strip()
                # Keep first occurrence (they should be the same)
                if item_key not in all_ingredients:
                    all_ingredients[item_key] = item.copy()
        
        print(f"[ROUTING] Found {len(all_ingredients)} unique ingredients to route")
        print(f"[ROUTING] Selected stores: {selected_stores}")
        
        # Route each ingredient to best store
        for item_name, ingredient in all_ingredients.items():
            amount = ingredient.get('amount', 0)
            unit = ingredient.get('unit', 'cup')
            
            # Convert to standard unit
            quantity = self.convert_to_standard_unit(amount, unit)
            
            # Score each selected store
            store_scores = {}
            for store_id in selected_stores:
                score = self.score_store_for_ingredient(store_id, ingredient, quantity)
                store_scores[store_id] = score
            
            # Route to highest scoring store
            if store_scores:
                best_store = max(store_scores.items(), key=lambda x: x[1])[0]
                new_routing[best_store].append(ingredient)
                
                # Debug output for small items
                if quantity < 1.0:
                    print(f"[ROUTING] {ingredient['item']} ({amount} {unit} = {quantity:.2f} cups) → {best_store} (scores: {store_scores})")
        
        # Rebuild shopping list with new routing
        optimized_list = {
            'stores': {},
            'total_items': len(all_ingredients),
            'start_date': shopping_list.get('start_date', ''),
            'end_date': shopping_list.get('end_date', '')
        }
        
        for store_id in selected_stores:
            # Only include store if it has items
            if new_routing[store_id]:
                store_name = store_id  # Keep original ID for consistency
                store_profile = self.store_profiles.get(store_id, {})
                
                optimized_list['stores'][store_name] = {
                    'items': sorted(new_routing[store_id], key=lambda x: x['item']),
                    'count': len(new_routing[store_id]),
                    'store_info': {
                        'name': store_profile.get('name', store_name.replace('_', ' ').title()),
                        'type': store_profile.get('type', 'grocery')
                    }
                }
        
        print(f"[ROUTING] Final distribution: {[(s, len(items)) for s, items in new_routing.items()]}")
        
        return optimized_list
    
    def get_routing_explanation(self, ingredient: dict, store_id: str, 
                               quantity_in_cups: float) -> str:
        """Get human-readable explanation for why ingredient was routed to store"""
        category = self.categorize_ingredient(ingredient.get('item', ''))
        profile = self.store_profiles.get(store_id, {})
        
        reasons = []
        
        if quantity_in_cups >= 5.0 and profile.get('type') == 'bulk':
            reasons.append("large quantity, good for bulk purchasing")
        elif quantity_in_cups < 1.0 and profile.get('type') == 'specialty':
            reasons.append("small amount, better at specialty stores")
        
        if category in profile.get('good_for', []):
            reasons.append(f"store specializes in {category.replace('_', ' ')}")
        
        if not reasons:
            reasons.append("best available option")
        
        return " - ".join(reasons)


def apply_smart_routing(shopping_list: dict, selected_stores: List[str]) -> dict:
    """
    Main function to apply smart routing to shopping list
    
    Usage:
        optimized_list = apply_smart_routing(shopping_list, ['costco', 'whole_foods', 'petes'])
    """
    print(f"\n{'='*60}")
    print(f"[ROUTING START] Selected stores: {selected_stores}")
    print(f"[ROUTING START] Shopping list has stores: {list(shopping_list.get('stores', {}).keys())}")
    print(f"{'='*60}\n")
    
    # If only one store selected, no routing needed
    if len(selected_stores) <= 1:
        print("[ROUTING] Only one store selected, skipping smart routing")
        return shopping_list
    
    # Normalize selected store IDs (lowercase, no spaces)
    normalized_stores = [s.lower().replace(' ', '_').replace("'", '') for s in selected_stores]
    print(f"[ROUTING] Normalized store IDs: {normalized_stores}")
    
    router = StoreRouter()
    result = router.route_ingredients(shopping_list, normalized_stores)
    
    print(f"\n[ROUTING COMPLETE] Result has stores: {list(result.get('stores', {}).keys())}")
    for store, data in result.get('stores', {}).items():
        print(f"  - {store}: {data.get('count', 0)} items")
    print(f"{'='*60}\n")
    
    return result
