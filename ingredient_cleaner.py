"""
Ingredient Data Cleanup Utility
Fixes common data quality issues in recipe ingredients
"""

import re
from typing import Dict, Tuple


class IngredientCleaner:
    """Clean and normalize ingredient data"""
    
    def __init__(self):
        # Common redundancies to fix
        self.redundancy_patterns = [
            # "white egg white" → "egg whites"  
            (r'\b(\d+)\s+white\s+egg\s+white\b', r'\1 egg whites'),
            (r'\b(\d+)\s+whites\s+egg\s+whites\b', r'\1 egg whites'),
            
            # "dates medjool dates" → "medjool dates"
            (r'\b(\d+)\s+dates\s+medjool\s+dates\b', r'\1 medjool dates'),
            (r'\b(\d+)\s+dates\s+dates\b', r'\1 dates'),
            
            # "scoop protein powder" → "scoops protein powder"
            (r'\b(\d+)\s+scoop\s+', r'\1 scoops '),
            
            # "mediums apples" → "medium apples"
            (r'\b(\d+)\s+mediums\s+', r'\1 medium '),
            (r'\b(\d+)\s+wholes\s+', r'\1 whole '),
            (r'\b(\d+)\s+cloves\s+', r'\1 cloves '),
            
            # "lemons lemon" → "lemons"
            (r'\b(\d+)\s+lemons\s+lemon\b', r'\1 lemons'),
            (r'\b(\d+)\s+lemon\s+lemons\b', r'\1 lemons'),
            
            # "onion" singular when plural needed
            (r'\b([2-9]|[1-9]\d+)\s+medium\s+onion\b', r'\1 medium onions'),
            (r'\b([2-9]|[1-9]\d+)\s+medium\s+apple\b', r'\1 medium apples'),
            (r'\b([2-9]|[1-9]\d+)\s+medium\s+lemon\b', r'\1 medium lemons'),
            
            # Generic pattern: "X item item" → "X item" (but preserve if different)
            # This is tricky, so we'll handle it manually in clean_ingredient_name
        ]
        
        # Unit pluralization rules
        self.plural_units = {
            'slice': 'slices',
            'piece': 'pieces',
            'scoop': 'scoops',
            'clove': 'cloves',
            'leaf': 'leaves',
            'sprig': 'sprigs',
            'stalk': 'stalks',
            'strip': 'strips',
            'medium': 'medium',  # Don't pluralize "medium"
            'whole': 'whole',    # Don't pluralize "whole"
        }
    
    def clean_ingredient_name(self, item: str, amount: float = 1) -> str:
        """
        Clean ingredient name removing redundancies
        
        Args:
            item: Raw ingredient name
            amount: Quantity (for pluralization)
        
        Returns:
            Cleaned ingredient name
        """
        if not item:
            return item
        
        cleaned = item.strip()
        
        # First convert to string with amount for pattern matching
        full_text = f"{amount} {cleaned}"
        
        # Apply redundancy patterns
        for pattern, replacement in self.redundancy_patterns:
            full_text = re.sub(pattern, replacement, full_text, flags=re.IGNORECASE)
        
        # Remove the amount from the beginning to get just the cleaned item
        cleaned = re.sub(r'^\d+\.?\d*\s+', '', full_text).strip()
        
        # Remove double spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Handle singular/plural based on amount
        if amount > 1:
            # Pluralize common items if not already plural
            if not cleaned.endswith('s') and not cleaned.endswith('ch'):
                # Common exceptions
                if 'egg white' in cleaned and 'egg whites' not in cleaned:
                    cleaned = cleaned.replace('egg white', 'egg whites')
                elif cleaned in ['onion', 'apple', 'lemon', 'banana', 'potato']:
                    cleaned += 's'
        
        return cleaned.strip()
    
    def pluralize_unit(self, unit: str, amount: float) -> str:
        """
        Pluralize units when amount > 1
        
        Args:
            unit: Unit of measurement
            amount: Quantity
        
        Returns:
            Pluralized unit if needed
        """
        if not unit or amount <= 1:
            return unit
        
        unit_lower = unit.lower().strip()
        
        # Check if already plural
        if unit_lower.endswith('s'):
            return unit
        
        # Apply pluralization rules
        if unit_lower in self.plural_units:
            return self.plural_units[unit_lower]
        
        # Standard English pluralization
        if unit_lower.endswith('y'):
            return unit_lower[:-1] + 'ies'
        elif unit_lower in ['tsp', 'tbsp', 'oz', 'lb', 'cup']:
            # These don't pluralize in abbreviation
            return unit
        
        return unit + 's'
    
    def normalize_ingredient_display(self, item: str, amount: float, unit: str) -> Dict[str, any]:
        """
        Normalize complete ingredient for display
        
        Args:
            item: Ingredient name
            amount: Quantity
            unit: Unit of measurement
        
        Returns:
            Dict with cleaned data
        """
        # Clean the item name
        cleaned_item = self.clean_ingredient_name(item, amount)
        
        # Pluralize unit if needed
        cleaned_unit = self.pluralize_unit(unit, amount)
        
        # Format amount nicely
        if isinstance(amount, (int, float)):
            if amount == int(amount):
                formatted_amount = int(amount)
            elif amount < 1:
                formatted_amount = round(amount, 2)
            else:
                formatted_amount = round(amount, 1)
        else:
            formatted_amount = amount
        
        return {
            'item': cleaned_item,
            'amount': formatted_amount,
            'unit': cleaned_unit,
            'display': f"{formatted_amount} {cleaned_unit} {cleaned_item}".strip()
        }
    
    def clean_shopping_list_item(self, ingredient: Dict) -> Dict:
        """
        Clean a shopping list ingredient entry
        
        Args:
            ingredient: Raw ingredient dict with 'item', 'amount', 'unit'
        
        Returns:
            Cleaned ingredient dict
        """
        item = ingredient.get('item', '')
        amount = ingredient.get('amount', 0)
        unit = ingredient.get('unit', '')
        
        # Convert amount to float if string
        if isinstance(amount, str):
            try:
                amount = float(amount)
            except ValueError:
                amount = 0
        
        cleaned = self.normalize_ingredient_display(item, amount, unit)
        
        # Preserve other fields
        result = ingredient.copy()
        result.update({
            'item': cleaned['item'],
            'amount': cleaned['amount'],
            'unit': cleaned['unit']
        })
        
        return result


# Example usage and tests
if __name__ == "__main__":
    cleaner = IngredientCleaner()
    
    # Test cases
    test_cases = [
        {"item": "white egg white", "amount": 4, "unit": ""},
        {"item": "whites egg whites", "amount": 2, "unit": ""},
        {"item": "dates medjool dates", "amount": 6, "unit": ""},
        {"item": "protein powder", "amount": 3, "unit": "scoop"},
        {"item": "chicken thighs", "amount": 6.5, "unit": "lbs"},
    ]
    
    print("Ingredient Cleanup Tests:\n")
    for test in test_cases:
        cleaned = cleaner.clean_shopping_list_item(test)
        print(f"BEFORE: {test['amount']} {test['unit']} {test['item']}")
        print(f"AFTER:  {cleaned['amount']} {cleaned['unit']} {cleaned['item']}")
        print()
