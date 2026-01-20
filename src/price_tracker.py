"""
Price Tracking System
Calculates shopping list costs based on ingredient prices
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PriceTracker:
    """Track ingredient prices and calculate costs"""
    
    def __init__(self, prices_file: str = "data/ingredient_prices.yaml"):
        self.prices_file = Path(prices_file)
        self.prices = self._load_prices()
    
    def _load_prices(self) -> Dict:
        """Load price database"""
        if not self.prices_file.exists():
            return {}
        
        with open(self.prices_file, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def get_price(self, ingredient: str, store: str) -> Optional[float]:
        """Get price for ingredient at specific store"""
        ingredient_lower = ingredient.lower().replace(' ', '_')
        
        # Search through all categories
        for category, items in self.prices.items():
            if ingredient_lower in items:
                price_info = items[ingredient_lower]
                return price_info.get(store)
        
        return None
    
    def get_cheapest_store(self, ingredient: str) -> Tuple[Optional[str], Optional[float]]:
        """Find cheapest store for an ingredient"""
        ingredient_lower = ingredient.lower().replace(' ', '_')
        
        for category, items in self.prices.items():
            if ingredient_lower in items:
                price_info = items[ingredient_lower]
                
                # Get all available prices
                store_prices = {
                    store: price 
                    for store, price in price_info.items() 
                    if store != 'unit' and price is not None
                }
                
                if store_prices:
                    cheapest_store = min(store_prices, key=store_prices.get)
                    return cheapest_store, store_prices[cheapest_store]
        
        return None, None
    
    def calculate_item_cost(self, item: Dict, store: str) -> Optional[float]:
        """Calculate cost for a single shopping list item"""
        ingredient = item.get('item', '').lower().replace(' ', '_')
        amount = item.get('amount', 0)
        
        # Try to convert amount to float
        try:
            amount_float = float(str(amount).split()[0])  # Handle "5 lbs" format
        except (ValueError, IndexError):
            amount_float = 1.0
        
        price = self.get_price(ingredient, store)
        
        if price is None:
            return None
        
        return price * amount_float
    
    def calculate_store_total(self, items: List[Dict], store: str) -> Dict:
        """Calculate total cost for a store"""
        total = 0.0
        priced_items = 0
        unpriced_items = 0
        
        item_costs = []
        
        for item in items:
            cost = self.calculate_item_cost(item, store)
            
            if cost is not None:
                total += cost
                priced_items += 1
                item_costs.append({
                    'item': item.get('item'),
                    'amount': item.get('amount'),
                    'unit': item.get('unit'),
                    'cost': cost
                })
            else:
                unpriced_items += 1
                item_costs.append({
                    'item': item.get('item'),
                    'amount': item.get('amount'),
                    'unit': item.get('unit'),
                    'cost': None
                })
        
        return {
            'total': round(total, 2),
            'priced_items': priced_items,
            'unpriced_items': unpriced_items,
            'items_with_costs': item_costs
        }
    
    def calculate_shopping_list_total(self, shopping_list: Dict) -> Dict:
        """Calculate total cost for entire shopping list"""
        stores_data = shopping_list.get('stores', {})
        
        store_totals = {}
        grand_total = 0.0
        total_priced = 0
        total_unpriced = 0
        
        for store_name, store_data in stores_data.items():
            items = store_data.get('items', [])
            store_calc = self.calculate_store_total(items, store_name)
            
            store_totals[store_name] = store_calc
            grand_total += store_calc['total']
            total_priced += store_calc['priced_items']
            total_unpriced += store_calc['unpriced_items']
        
        return {
            'grand_total': round(grand_total, 2),
            'total_priced_items': total_priced,
            'total_unpriced_items': total_unpriced,
            'stores': store_totals,
            'budget': shopping_list.get('budget', 400),
            'under_budget': shopping_list.get('budget', 400) - grand_total,
            'coverage': round((total_priced / (total_priced + total_unpriced) * 100), 1) if (total_priced + total_unpriced) > 0 else 0
        }
    
    def suggest_savings(self, shopping_list: Dict) -> List[Dict]:
        """Suggest items where switching stores could save money"""
        suggestions = []
        stores_data = shopping_list.get('stores', {})
        
        for store_name, store_data in stores_data.items():
            items = store_data.get('items', [])
            
            for item in items:
                ingredient = item.get('item')
                current_price = self.get_price(ingredient, store_name)
                
                if current_price is not None:
                    cheapest_store, cheapest_price = self.get_cheapest_store(ingredient)
                    
                    if cheapest_store and cheapest_store != store_name:
                        savings = current_price - cheapest_price
                        
                        if savings > 0.50:  # Only suggest if saving > $0.50
                            suggestions.append({
                                'item': ingredient,
                                'current_store': store_name,
                                'current_price': current_price,
                                'cheaper_store': cheapest_store,
                                'cheaper_price': cheapest_price,
                                'savings': round(savings, 2)
                            })
        
        # Sort by savings amount (highest first)
        suggestions.sort(key=lambda x: x['savings'], reverse=True)
        
        return suggestions
    
    def update_price(self, ingredient: str, store: str, price: float) -> bool:
        """Update price for an ingredient"""
        ingredient_lower = ingredient.lower().replace(' ', '_')
        
        # Find and update the ingredient
        for category, items in self.prices.items():
            if ingredient_lower in items:
                self.prices[category][ingredient_lower][store] = price
                
                # Save to file
                with open(self.prices_file, 'w') as f:
                    yaml.dump(self.prices, f, default_flow_style=False, sort_keys=False)
                
                return True
        
        return False
    
    def add_ingredient_price(self, category: str, ingredient: str, 
                            prices: Dict[str, float], unit: str = "each") -> bool:
        """Add new ingredient with prices"""
        ingredient_lower = ingredient.lower().replace(' ', '_')
        
        if category not in self.prices:
            self.prices[category] = {}
        
        self.prices[category][ingredient_lower] = {
            **prices,
            'unit': unit
        }
        
        # Save to file
        with open(self.prices_file, 'w') as f:
            yaml.dump(self.prices, f, default_flow_style=False, sort_keys=False)
        
        return True


if __name__ == "__main__":
    # Test the price tracker
    tracker = PriceTracker()
    
    print("Testing Price Tracker")
    print("=" * 50)
    
    # Test getting a price
    price = tracker.get_price("chicken_breast", "costco")
    print(f"\nChicken breast at Costco: ${price}/lb")
    
    # Test finding cheapest store
    store, price = tracker.get_cheapest_store("chicken_breast")
    print(f"Cheapest chicken breast: {store} at ${price}/lb")
    
    # Test calculating item cost
    test_item = {
        'item': 'chicken breast',
        'amount': '5',
        'unit': 'lbs'
    }
    cost = tracker.calculate_item_cost(test_item, 'costco')
    print(f"\n5 lbs chicken breast at Costco: ${cost}")
    
    print("\n✓ Price tracker working!")
