"""
Price API Service
Fetches real-time grocery prices from multiple sources
Supports: Instacart, Kroger, fallback estimates
"""

import os
import requests
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache


class PriceAPIService:
    """
    Unified service for fetching grocery prices from multiple APIs
    """

    def __init__(self):
        print("[INIT] Starting PriceAPIService initialization...")
        
        # API Keys - try multiple sources
        # Priority: 1. Environment vars, 2. Streamlit secrets, 3. Config file
        
        # Try environment variables first
        self.instacart_key = os.getenv('INSTACART_API_KEY')
        self.kroger_client_id = os.getenv('KROGER_CLIENT_ID')
        self.kroger_client_secret = os.getenv('KROGER_CLIENT_SECRET')
        
        
        # If not in env, try Streamlit secrets (when running in Streamlit)
        if not self.kroger_client_id:
            print("[STREAMLIT] Trying Streamlit secrets...")
            try:
                import streamlit as st
                self.instacart_key = self.instacart_key or st.secrets.get('INSTACART_API_KEY')
                self.kroger_client_id = st.secrets.get('KROGER_CLIENT_ID')
                self.kroger_client_secret = st.secrets.get('KROGER_CLIENT_SECRET')
            except Exception as e:
                pass  # Not running in Streamlit context
        else:
            print("[STREAMLIT] Skipped (already have credentials from env)")
        
        # If still not found, try loading from secrets file directly
        if not self.kroger_client_id:
            try:
                import toml
                secrets_path = '.streamlit/secrets.toml'
                
                if os.path.exists(secrets_path):
                    secrets = toml.load(secrets_path)
                    self.instacart_key = self.instacart_key or secrets.get('INSTACART_API_KEY')
                    self.kroger_client_id = secrets.get('KROGER_CLIENT_ID')
                    self.kroger_client_secret = secrets.get('KROGER_CLIENT_SECRET')
                else:
            except Exception as e:
        
        # Cache for API responses (avoid repeated calls)
        self.cache = {}
        self.cache_duration = timedelta(hours=24)  # Prices valid for 24 hours
        
        # Kroger token
        self.kroger_token = None
        self.kroger_token_expiry = None
    
    # ============================================================================
    # MAIN PRICE FETCHING METHOD
    # ============================================================================
    
    def get_price(self, item_name: str, store: str, zipcode: str = "60827") -> Dict:
        """
        Get price for an item from the best available source
        
        Args:
            item_name: Name of grocery item (e.g., "chicken thighs")
            store: Store name (costco, whole_foods, jewel, petes_fresh_market, aldi)
            zipcode: User's zipcode for location-specific pricing
        
        Returns:
            {
                'item': 'Chicken Thighs',
                'price': 24.99,
                'unit': '10 lb pack',
                'price_per_unit': 2.50,
                'unit_type': 'lb',
                'store': 'Costco',
                'source': 'instacart' or 'kroger' or 'estimate',
                'in_stock': True,
                'last_updated': '2026-01-25T10:30:00',
                'confidence': 'high' or 'medium' or 'low'
            }
        """
        # Check cache first
        cache_key = f"{item_name}_{store}_{zipcode}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['data']
        
        # Try Instacart first (best coverage)
        if self.instacart_key:
            price_data = self._fetch_from_instacart(item_name, store, zipcode)
            if price_data:
                self._cache_price(cache_key, price_data)
                return price_data
        
        # Try Kroger for Jewel-Osco
        if store == 'jewel' and self.kroger_client_id:
            price_data = self._fetch_from_kroger(item_name, zipcode)
            if price_data:
                self._cache_price(cache_key, price_data)
                return price_data
        
        # Fallback to estimates
        price_data = self._estimate_price(item_name, store)
        self._cache_price(cache_key, price_data)
        return price_data
    
    # ============================================================================
    # INSTACART API INTEGRATION
    # ============================================================================
    
    def _fetch_from_instacart(self, item_name: str, store: str, zipcode: str) -> Optional[Dict]:
        """
        Fetch price from Instacart API
        
        NOTE: This uses a hypothetical Instacart API structure.
        Actual implementation depends on Instacart's real API documentation.
        Visit: https://www.instacart.com/developer for actual endpoints
        """
        try:
            # Map our store names to Instacart store IDs
            store_mapping = {
                'costco': 'costco',
                'whole_foods': 'whole_foods',
                'jewel': 'jewel_osco',
                'petes_fresh_market': 'petes_fresh_market',
                'aldi': 'aldi'
            }
            
            instacart_store = store_mapping.get(store)
            if not instacart_store:
                return None
            
            # Instacart API call (hypothetical structure)
            url = "https://api.instacart.com/v1/products/search"
            headers = {
                "Authorization": f"Bearer {self.instacart_key}",
                "Content-Type": "application/json"
            }
            params = {
                "query": item_name,
                "store": instacart_store,
                "zipcode": zipcode,
                "limit": 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('products') and len(data['products']) > 0:
                    product = data['products'][0]
                    
                    return {
                        'item': product.get('name', item_name),
                        'price': float(product.get('price', 0)),
                        'unit': product.get('size', 'each'),
                        'price_per_unit': float(product.get('price_per_unit', 0)),
                        'unit_type': product.get('unit_type', 'each'),
                        'store': store,
                        'source': 'instacart',
                        'in_stock': product.get('in_stock', True),
                        'last_updated': datetime.now().isoformat(),
                        'confidence': 'high'
                    }
            
            return None
            
        except Exception as e:
            print(f"Instacart API error: {e}")
            return None
    
    # ============================================================================
    # KROGER API INTEGRATION (For Jewel-Osco)
    # ============================================================================
    
    def _get_kroger_token(self) -> Optional[str]:
        """
        Get OAuth token for Kroger API
        Token is cached and reused until expiry
        """
        
        # Return cached token if still valid
        if self.kroger_token and self.kroger_token_expiry:
            if datetime.now() < self.kroger_token_expiry:
                return self.kroger_token
        
        try:
            # Production API URL
            url = "https://api.kroger.com/v1/connect/oauth2/token"
            
            
            response = requests.post(
                url,
                data={
                    'grant_type': 'client_credentials',
                    'scope': 'product.compact'
                },
                auth=(self.kroger_client_id, self.kroger_client_secret),
                timeout=5
            )
            
            
            if response.status_code == 200:
                data = response.json()
                self.kroger_token = data['access_token']
                # Tokens typically expire in 30 minutes
                self.kroger_token_expiry = datetime.now() + timedelta(minutes=25)
                return self.kroger_token
            else:
            
            return None
            
        except Exception as e:
            return None
    
    def _fetch_from_kroger(self, item_name: str, zipcode: str) -> Optional[Dict]:
        """
        Fetch price from Kroger API (for Jewel-Osco)
        
        Real API docs: https://developer.kroger.com/reference
        """
        
        try:
            token = self._get_kroger_token()
            if not token:
                return None
            
            
            # First, get location ID for zipcode
            # NOTE: Search for ANY Kroger-family store, not just Jewel-Osco
            # Kroger owns: Jewel-Osco, Mariano's, etc.
            location_url = "https://api.kroger.com/v1/locations"
            headers = {"Authorization": f"Bearer {token}"}
            location_params = {
                "filter.zipCode.near": zipcode,
                "filter.limit": "10",  # Get multiple stores, pick closest
                "filter.radiusInMiles": "25"  # Search 25 mile radius
            }
            
            
            location_response = requests.get(
                location_url,
                headers=headers,
                params=location_params,
                timeout=5
            )
            
            
            if location_response.status_code != 200:
                return None
            
            locations = location_response.json().get('data', [])
            
            # DEBUG: Show ALL store names to see what API returns
            for i, loc in enumerate(locations):
                name = loc.get('name', 'Unknown')
                city = loc.get('address', {}).get('city', 'Unknown')
                chain = loc.get('chain', 'Unknown')
            
            if not locations:
                return None
            
            # Map Kroger store names to our app's store names
            store_name_mapping = {
                'jewel': ['jewel', 'jewel-osco', 'jewel osco'],
                'marianos': ['mariano', "mariano's", 'marianos'],
                'food_4_less': ['food 4 less', 'food4less'],
                'pick_n_save': ['pick n save', "pick 'n save"],
            }
            
            # Filter locations to only stores we support
            # Priority: Jewel-Osco first, then Mariano's (both Kroger-owned)
            supported_locations = []
            for loc in locations:
                store_name_lower = loc.get('name', '').lower()
                
                # Check if this is a Jewel-Osco (highest priority)
                if any(keyword in store_name_lower for keyword in store_name_mapping['jewel']):
                    supported_locations.insert(0, loc)  # Add to front
                # Check for Mariano's (also supported - it's Kroger-owned)
                elif any(keyword in store_name_lower for keyword in store_name_mapping.get('marianos', [])):
                    supported_locations.append(loc)  # Add Mariano's
                else:
            
            if not supported_locations:
                return None
            
            # Use the first supported location (prioritized Jewel-Osco)
            location_id = supported_locations[0]['locationId']
            store_name = supported_locations[0].get('name', 'Unknown')
            store_city = supported_locations[0].get('address', {}).get('city', 'Unknown')
            
            # Now search for product
            product_url = "https://api.kroger.com/v1/products"
            product_params = {
                'filter.term': item_name,
                'filter.locationId': location_id,
                'filter.limit': 1
            }
            
            
            product_response = requests.get(
                product_url,
                headers=headers,
                params=product_params,
                timeout=5
            )
            
            
            if product_response.status_code == 200:
                data = product_response.json()
                products = data.get('data', [])
                
                
                if products:
                    product = products[0]
                    
                    items = product.get('items', [])
                    
                    if items:
                        item = items[0]
                        price_info = item.get('price', {})
                        
                        
                        result = {
                            'item': product.get('description', item_name),
                            'price': float(price_info.get('regular', 0)),
                            'unit': item.get('size', 'each'),
                            'price_per_unit': float(price_info.get('promo', price_info.get('regular', 0))),
                            'unit_type': 'each',
                            'store': 'jewel',
                            'source': 'kroger',
                            'in_stock': True,
                            'last_updated': datetime.now().isoformat(),
                            'confidence': 'high'
                        }
                        
                        return result
                    else:
                else:
            else:
            
            return None
            
        except Exception as e:
            print(f"Kroger API error: {e}")
            return None
    
    # ============================================================================
    # FALLBACK: INTELLIGENT PRICE ESTIMATION
    # ============================================================================
    
    def _estimate_price(self, item_name: str, store: str) -> Dict:
        """
        Intelligent price estimation based on item type and store
        Uses heuristics when APIs are unavailable
        """
        item_lower = item_name.lower()
        
        # Base price estimates by category
        base_prices = {
            # Proteins
            'chicken thighs': 2.50,
            'chicken breast': 3.99,
            'salmon': 12.99,
            'white fish': 8.99,
            'whiting': 6.99,
            'ground turkey': 4.99,
            'turkey bacon': 5.99,
            'eggs': 4.99,
            
            # Produce
            'sweet potato': 1.29,
            'onion': 0.89,
            'spinach': 2.99,
            'tomato': 1.99,
            'bell pepper': 1.49,
            'avocado': 1.99,
            'lemon': 0.79,
            
            # Pantry
            'rice': 1.50,
            'olive oil': 8.99,
            'coconut oil': 7.99,
            'canned tomatoes': 1.29,
            'beans': 1.19,
            'lentils': 1.49,
            'pasta': 1.29,
            'oats': 3.99,
        }
        
        # Find matching item
        estimated_price = 5.00  # Default
        unit = 'lb'
        
        for key, price in base_prices.items():
            if key in item_lower:
                estimated_price = price
                break
        
        # Store-specific adjustments
        store_multipliers = {
            'costco': 0.85,  # Costco typically 15% cheaper (but bulk)
            'whole_foods': 1.25,  # Whole Foods ~25% more expensive
            'jewel': 1.0,  # Baseline
            'petes_fresh_market': 0.95,  # Slightly cheaper
            'aldi': 0.80  # Aldi typically cheapest
        }
        
        multiplier = store_multipliers.get(store, 1.0)
        final_price = estimated_price * multiplier
        
        return {
            'item': item_name.title(),
            'price': round(final_price, 2),
            'unit': unit,
            'price_per_unit': round(final_price, 2),
            'unit_type': unit,
            'store': store,
            'source': 'estimate',
            'in_stock': True,
            'last_updated': datetime.now().isoformat(),
            'confidence': 'low'
        }
    
    # ============================================================================
    # BATCH OPERATIONS
    # ============================================================================
    
    def get_shopping_list_prices(self, shopping_list: Dict, stores: List[str], zipcode: str) -> Dict:
        """
        Get prices for entire shopping list across multiple stores
        
        Args:
            shopping_list: Shopping list with items
            stores: List of stores to check
            zipcode: User's zipcode
        
        Returns:
            Dictionary with prices by store
        """
        results = {}
        
        for store_name, store_data in shopping_list.get('stores', {}).items():
            store_prices = []
            total_cost = 0
            
            for item in store_data.get('items', []):
                item_name = item['item']
                amount = item['amount']
                
                # Get price for this item
                price_data = self.get_price(item_name, store_name, zipcode)
                
                # Calculate cost based on amount needed
                item_cost = price_data['price_per_unit'] * amount
                total_cost += item_cost
                
                store_prices.append({
                    **item,
                    'price_data': price_data,
                    'item_cost': round(item_cost, 2)
                })
            
            results[store_name] = {
                'items': store_prices,
                'total_cost': round(total_cost, 2),
                'store_info': store_data.get('store_info', {})
            }
        
        return results
    
    # ============================================================================
    # CACHING
    # ============================================================================
    
    def _cache_price(self, key: str, data: Dict):
        """Cache price data"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def clear_cache(self):
        """Clear all cached prices (e.g., when user wants fresh data)"""
        self.cache = {}
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def health_check(self) -> Dict:
        """
        Check which APIs are available and working
        """
        status = {
            'instacart': False,
            'kroger': False,
            'fallback': True
        }
        
        # Test Instacart
        if self.instacart_key:
            try:
                # Simple test query
                test = self._fetch_from_instacart('eggs', 'costco', '60827')
                status['instacart'] = test is not None
            except:
                pass
        
        # Test Kroger
        if self.kroger_client_id:
            try:
                token = self._get_kroger_token()
                status['kroger'] = token is not None
            except Exception as e:
        
        return status


# ============================================================================
# STREAMLIT INTEGRATION HELPERS
# ============================================================================

# @st.cache_resource  # Disabled for testing
def get_price_service():
    """
    Get cached instance of PriceAPIService
    Use this in Streamlit to avoid recreating service
    """
    return PriceAPIService()


def display_price_info(price_data: Dict, show_confidence: bool = True):
    """
    Display price information in Streamlit UI
    
    Args:
        price_data: Price data from get_price()
        show_confidence: Whether to show confidence indicator
    """
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**{price_data['item']}**")
    
    with col2:
        st.write(f"${price_data['price']:.2f}")
        st.caption(f"{price_data['unit']}")
    
    with col3:
        if show_confidence:
            confidence_colors = {
                'high': '🟢',
                'medium': '🟡',
                'low': '🔴'
            }
            emoji = confidence_colors.get(price_data['confidence'], '⚪')
            st.write(f"{emoji} {price_data['source']}")
