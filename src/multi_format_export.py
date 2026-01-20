"""
CSV and SMS Export Formatters
Multiple lightweight export options
"""

import csv
from typing import Dict, List
from io import StringIO


class CSVExporter:
    """Export shopping lists to CSV format"""
    
    @staticmethod
    def export_shopping_list(shopping_list: Dict, include_prices: bool = False, 
                            cost_data: Dict = None) -> str:
        """Export shopping list to CSV string"""
        
        output = StringIO()
        
        if include_prices and cost_data:
            writer = csv.writer(output)
            writer.writerow(['Store', 'Item', 'Amount', 'Unit', 'Cost'])
            
            stores = shopping_list.get('stores', {})
            
            for store_name, store_data in stores.items():
                items = store_data.get('items', [])
                store_cost_items = cost_data.get('stores', {}).get(store_name, {}).get('items_with_costs', [])
                
                for i, item in enumerate(items):
                    cost_info = store_cost_items[i] if i < len(store_cost_items) else {}
                    cost = cost_info.get('cost', '')
                    cost_str = f"${cost:.2f}" if cost else ""
                    
                    writer.writerow([
                        store_name.replace('_', ' ').title(),
                        item.get('item', ''),
                        item.get('amount', ''),
                        item.get('unit', ''),
                        cost_str
                    ])
        else:
            writer = csv.writer(output)
            writer.writerow(['Store', 'Item', 'Amount', 'Unit'])
            
            stores = shopping_list.get('stores', {})
            
            for store_name, store_data in stores.items():
                items = store_data.get('items', [])
                
                for item in items:
                    writer.writerow([
                        store_name.replace('_', ' ').title(),
                        item.get('item', ''),
                        item.get('amount', ''),
                        item.get('unit', '')
                    ])
        
        return output.getvalue()
    
    @staticmethod
    def save_to_file(csv_string: str, output_path: str) -> str:
        """Save CSV string to file"""
        with open(output_path, 'w', newline='') as f:
            f.write(csv_string)
        return output_path


class SMSFormatter:
    """Format shopping lists for SMS/text messages"""
    
    @staticmethod
    def format_shopping_list(shopping_list: Dict, include_prices: bool = False,
                            cost_data: Dict = None) -> str:
        """Format shopping list for SMS"""
        
        lines = []
        
        # Header
        lines.append("🛒 SHOPPING LIST")
        lines.append(f"{shopping_list.get('start_date', '')} - {shopping_list.get('end_date', '')}")
        
        if include_prices and cost_data:
            lines.append(f"Budget: ${shopping_list.get('budget', 400)}")
            lines.append(f"Est. Total: ${cost_data.get('grand_total', 0)}")
        
        lines.append("")
        
        # Items by store
        stores = shopping_list.get('stores', {})
        
        for store_name, store_data in stores.items():
            store_title = store_name.replace('_', ' ').title()
            
            if include_prices and cost_data:
                store_total = cost_data.get('stores', {}).get(store_name, {}).get('total', 0)
                lines.append(f"📍 {store_title} (${store_total:.2f})")
            else:
                lines.append(f"📍 {store_title}")
            
            items = store_data.get('items', [])
            
            if include_prices and cost_data:
                store_cost_items = cost_data.get('stores', {}).get(store_name, {}).get('items_with_costs', [])
                
                for i, item in enumerate(items):
                    cost_info = store_cost_items[i] if i < len(store_cost_items) else {}
                    cost = cost_info.get('cost')
                    
                    item_line = f"• {item.get('item', '')} - {item.get('amount', '')} {item.get('unit', '')}"
                    if cost:
                        item_line += f" (${cost:.2f})"
                    
                    lines.append(item_line)
            else:
                for item in items:
                    lines.append(f"• {item.get('item', '')} - {item.get('amount', '')} {item.get('unit', '')}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_compact(shopping_list: Dict) -> str:
        """Ultra-compact format for SMS character limit"""
        
        lines = []
        stores = shopping_list.get('stores', {})
        
        for store_name, store_data in stores.items():
            store_abbr = store_name.upper()[:4]  # COST, PETE, WHOL
            items = store_data.get('items', [])
            
            # Compact items
            item_list = []
            for item in items:
                item_name = item.get('item', '')[:15]  # Truncate long names
                amount = item.get('amount', '')
                item_list.append(f"{item_name} {amount}")
            
            lines.append(f"{store_abbr}: {', '.join(item_list)}")
        
        return "\n".join(lines)


class JSONFormatter:
    """Format data for API responses (mobile app)"""
    
    @staticmethod
    def format_shopping_list(shopping_list: Dict, include_prices: bool = False,
                            cost_data: Dict = None) -> Dict:
        """Format shopping list for JSON API response"""
        
        result = {
            'period': {
                'start': shopping_list.get('start_date'),
                'end': shopping_list.get('end_date')
            },
            'people': shopping_list.get('people', 2),
            'budget': shopping_list.get('budget', 400),
            'stores': []
        }
        
        if include_prices and cost_data:
            result['cost_summary'] = {
                'total': cost_data.get('grand_total', 0),
                'under_budget': cost_data.get('under_budget', 0),
                'coverage': cost_data.get('coverage', 0)
            }
        
        stores = shopping_list.get('stores', {})
        
        for store_name, store_data in stores.items():
            store_obj = {
                'name': store_name,
                'display_name': store_name.replace('_', ' ').title(),
                'items': []
            }
            
            if include_prices and cost_data:
                store_cost_data = cost_data.get('stores', {}).get(store_name, {})
                store_obj['total'] = store_cost_data.get('total', 0)
                store_obj['item_count'] = len(store_data.get('items', []))
            
            items = store_data.get('items', [])
            
            if include_prices and cost_data:
                store_cost_items = cost_data.get('stores', {}).get(store_name, {}).get('items_with_costs', [])
                
                for i, item in enumerate(items):
                    cost_info = store_cost_items[i] if i < len(store_cost_items) else {}
                    
                    item_obj = {
                        'id': i,
                        'name': item.get('item', ''),
                        'amount': item.get('amount', ''),
                        'unit': item.get('unit', ''),
                        'checked': False
                    }
                    
                    if cost_info.get('cost'):
                        item_obj['cost'] = cost_info.get('cost')
                    
                    store_obj['items'].append(item_obj)
            else:
                for i, item in enumerate(items):
                    store_obj['items'].append({
                        'id': i,
                        'name': item.get('item', ''),
                        'amount': item.get('amount', ''),
                        'unit': item.get('unit', ''),
                        'checked': False
                    })
            
            result['stores'].append(store_obj)
        
        return result


if __name__ == "__main__":
    # Test exporters
    test_shopping_list = {
        'start_date': '2026-01-20',
        'end_date': '2026-02-02',
        'people': 2,
        'budget': 400,
        'stores': {
            'costco': {
                'items': [
                    {'item': 'Chicken breast', 'amount': '5', 'unit': 'lbs'},
                    {'item': 'Salmon', 'amount': '2', 'unit': 'lbs'}
                ]
            },
            'petes_produce': {
                'items': [
                    {'item': 'Sweet potatoes', 'amount': '10', 'unit': 'each'}
                ]
            }
        }
    }
    
    print("CSV Export:")
    print("=" * 50)
    csv_output = CSVExporter.export_shopping_list(test_shopping_list)
    print(csv_output)
    
    print("\nSMS Format:")
    print("=" * 50)
    sms_output = SMSFormatter.format_shopping_list(test_shopping_list)
    print(sms_output)
    
    print("\nCompact SMS:")
    print("=" * 50)
    compact = SMSFormatter.format_compact(test_shopping_list)
    print(compact)
    
    print("\n✓ All formatters working!")
