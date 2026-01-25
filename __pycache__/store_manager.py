"""
Store Management System
Admin interface for managing stores and pricing
"""

import streamlit as st
import requests
import json
from datetime import datetime
from firebase_config import FIRESTORE_URL


class StoreManager:
    """Manage stores and pricing in Firebase"""
    
    def __init__(self):
        self.firestore_url = FIRESTORE_URL
    
    def add_store(self, user_id: str, id_token: str, store_data: dict) -> bool:
        """Add a new store to the system"""
        try:
            store_id = store_data['id']  # e.g., 'costco', 'whole_foods'
            url = f"{self.firestore_url}/stores/{store_id}"
            
            fields = {
                "name": {"stringValue": store_data['name']},
                "type": {"stringValue": store_data.get('type', 'Grocery Store')},
                "address": {"stringValue": store_data.get('address', '')},
                "enabled": {"booleanValue": True},
                "created_at": {"timestampValue": datetime.now().isoformat() + "Z"},
                "created_by": {"stringValue": user_id}
            }
            
            payload = {"fields": fields}
            headers = {"Authorization": f"Bearer {id_token}"}
            
            response = requests.patch(url, json=payload, headers=headers, timeout=5)
            
            # Show actual error if it fails
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                st.error(f"Firebase error: {error_msg}")
                st.error(f"Status code: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            st.error(f"Error adding store: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return False
    
    def get_all_stores(self, id_token: str) -> dict:
        """Get all stores from Firebase"""
        try:
            url = f"{self.firestore_url}/stores"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                stores = {}
                
                if 'documents' in data:
                    for doc in data['documents']:
                        store_id = doc['name'].split('/')[-1]
                        fields = doc.get('fields', {})
                        
                        stores[store_id] = {
                            'name': fields.get('name', {}).get('stringValue', ''),
                            'type': fields.get('type', {}).get('stringValue', ''),
                            'address': fields.get('address', {}).get('stringValue', ''),
                            'enabled': fields.get('enabled', {}).get('booleanValue', True)
                        }
                
                return stores
            
            return {}
            
        except Exception as e:
            st.error(f"Error loading stores: {e}")
            return {}
    
    def update_store_price(self, id_token: str, ingredient: str, store_id: str, 
                          price_data: dict) -> bool:
        """Update price for an ingredient at a specific store"""
        try:
            # Store prices under: store_prices/{ingredient}/{store_id}
            url = f"{self.firestore_url}/store_prices/{ingredient}/prices/{store_id}"
            
            fields = {
                "price": {"doubleValue": price_data['price']},
                "size": {"stringValue": price_data.get('size', '')},
                "unit": {"stringValue": price_data.get('unit', 'each')},
                "updated_at": {"timestampValue": datetime.now().isoformat() + "Z"}
            }
            
            payload = {"fields": fields}
            headers = {"Authorization": f"Bearer {id_token}"}
            
            response = requests.patch(url, json=payload, headers=headers, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            st.error(f"Error updating price: {e}")
            return False
    
    def get_ingredient_prices(self, id_token: str, ingredient: str) -> dict:
        """Get prices for an ingredient across all stores"""
        try:
            url = f"{self.firestore_url}/store_prices/{ingredient}/prices"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                if 'documents' in data:
                    for doc in data['documents']:
                        store_id = doc['name'].split('/')[-1]
                        fields = doc.get('fields', {})
                        
                        prices[store_id] = {
                            'price': fields.get('price', {}).get('doubleValue', 0),
                            'size': fields.get('size', {}).get('stringValue', ''),
                            'unit': fields.get('unit', {}).get('stringValue', 'each')
                        }
                
                return prices
            
            return {}
            
        except Exception as e:
            return {}
    
    def toggle_store_status(self, id_token: str, store_id: str, enabled: bool) -> bool:
        """Enable or disable a store"""
        try:
            url = f"{self.firestore_url}/stores/{store_id}"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            fields = {
                "enabled": {"booleanValue": enabled}
            }
            
            payload = {"fields": fields}
            response = requests.patch(url, json=payload, headers=headers, timeout=5)
            
            return response.status_code == 200
            
        except Exception as e:
            st.error(f"Error toggling store: {e}")
            return False
    
    def update_store(self, id_token: str, store_id: str, update_data: dict) -> bool:
        """Update store information while preserving existing data"""
        try:
            # First, get current store data
            current_store = self.get_all_stores(id_token).get(store_id, {})
            
            url = f"{self.firestore_url}/stores/{store_id}"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            # Build fields, keeping existing data if not being updated
            fields = {
                "name": {"stringValue": update_data.get('name', current_store.get('name', ''))},
                "type": {"stringValue": update_data.get('type', current_store.get('type', 'Grocery Store'))},
                "address": {"stringValue": update_data.get('address', current_store.get('address', ''))},
                "enabled": {"booleanValue": current_store.get('enabled', True)},
                "updated_at": {"timestampValue": datetime.now().isoformat() + "Z"}
            }
            
            payload = {"fields": fields}
            response = requests.patch(url, json=payload, headers=headers, timeout=5)
            
            return response.status_code == 200
            
        except Exception as e:
            st.error(f"Error updating store: {e}")
            return False


def show_admin_panel(user_email: str):
    """Admin panel for managing stores and prices"""
    
    # Only allow specific admin users
    ADMIN_EMAILS = ['marshawnshelton3@gmail.com', 'marshawn.shelton@isosalus.com']
    
    if user_email not in ADMIN_EMAILS:
        st.error("⛔ Admin access only")
        return
    
    st.header("🔧 Store Management Admin")
    st.caption("Add and manage stores, update pricing")
    
    manager = StoreManager()
    user_id = st.session_state.user['user_id']
    id_token = st.session_state.user['id_token']
    
    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["📍 Manage Stores", "💰 Update Prices", "📊 View Data"])
    
    # TAB 1: Add/Manage Stores
    with tab1:
        st.subheader("Add New Store")
        
        col1, col2 = st.columns(2)
        
        with col1:
            store_name = st.text_input("Store Name", placeholder="e.g., Costco")
            store_type = st.selectbox("Store Type", [
                "Wholesale Club",
                "Grocery Store", 
                "Organic/Natural Foods",
                "Discount Grocer",
                "Specialty Market"
            ])
        
        with col2:
            store_id = st.text_input("Store ID", placeholder="e.g., costco (lowercase, no spaces)")
            store_address = st.text_input("Address/Location", placeholder="Optional")
        
        if st.button("➕ Add Store", type="primary"):
            if store_name and store_id:
                store_data = {
                    'id': store_id.lower().replace(' ', '_'),
                    'name': store_name,
                    'type': store_type,
                    'address': store_address
                }
                
                if manager.add_store(user_id, id_token, store_data):
                    st.success(f"✓ Added {store_name}!")
                    st.rerun()
                else:
                    st.error("Failed to add store")
            else:
                st.warning("Store name and ID required")
        
        st.markdown("---")
        
        # Show existing stores
        st.subheader("Current Stores")
        stores = manager.get_all_stores(id_token)
        
        if stores:
            for store_id, store_data in stores.items():
                with st.expander(f"**{store_data['name']}** ({store_data['type']})", expanded=False):
                    st.write(f"**ID:** {store_id}")
                    st.write(f"**Type:** {store_data['type']}")
                    if store_data['address']:
                        st.write(f"**Address:** {store_data['address']}")
                    st.write(f"**Status:** {'✓ Enabled' if store_data['enabled'] else '✗ Disabled'}")
                    
                    st.markdown("---")
                    st.markdown("**Actions:**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Toggle enable/disable
                        if store_data['enabled']:
                            if st.button(f"🚫 Disable", key=f"disable_{store_id}"):
                                if manager.toggle_store_status(id_token, store_id, False):
                                    st.success(f"Disabled {store_data['name']}")
                                    st.rerun()
                        else:
                            if st.button(f"✅ Enable", key=f"enable_{store_id}"):
                                if manager.toggle_store_status(id_token, store_id, True):
                                    st.success(f"Enabled {store_data['name']}")
                                    st.rerun()
                    
                    with col2:
                        # Edit store
                        if st.button(f"✏️ Edit", key=f"edit_{store_id}"):
                            st.session_state[f'editing_{store_id}'] = True
                            st.rerun()
                    
                    # Edit form (shows when Edit clicked)
                    if st.session_state.get(f'editing_{store_id}', False):
                        st.markdown("---")
                        st.markdown("**Edit Store:**")
                        
                        new_name = st.text_input("Store Name", value=store_data['name'], 
                                                key=f"edit_name_{store_id}")
                        
                        new_type = st.selectbox("Store Type", 
                            ["Wholesale Club", "Grocery Store", "Organic/Natural Foods", 
                             "Discount Grocer", "Specialty Market"],
                            index=["Wholesale Club", "Grocery Store", "Organic/Natural Foods", 
                                  "Discount Grocer", "Specialty Market"].index(store_data['type']) 
                                  if store_data['type'] in ["Wholesale Club", "Grocery Store", 
                                  "Organic/Natural Foods", "Discount Grocer", "Specialty Market"] else 0,
                            key=f"edit_type_{store_id}")
                        
                        new_address = st.text_input("Address", value=store_data.get('address', ''), 
                                                   key=f"edit_addr_{store_id}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 Save Changes", key=f"save_{store_id}"):
                                update_data = {
                                    'name': new_name,
                                    'type': new_type,
                                    'address': new_address
                                }
                                if manager.update_store(id_token, store_id, update_data):
                                    st.success("Store updated!")
                                    st.session_state[f'editing_{store_id}'] = False
                                    st.rerun()
                        
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_{store_id}"):
                                st.session_state[f'editing_{store_id}'] = False
                                st.rerun()
        else:
            st.info("No stores added yet. Add your first store above!")
    
    # TAB 2: Update Prices
    with tab2:
        st.subheader("Update Ingredient Prices")
        
        stores = manager.get_all_stores(id_token)
        
        if not stores:
            st.warning("Add stores first before updating prices")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                ingredient_name = st.text_input("Ingredient", 
                    placeholder="e.g., olive oil, chicken breast")
                ingredient_id = st.text_input("Ingredient ID", 
                    placeholder="e.g., olive_oil (lowercase, underscores)",
                    help="This should match the ingredient name in recipes")
            
            with col2:
                selected_store = st.selectbox("Store", 
                    options=list(stores.keys()),
                    format_func=lambda x: stores[x]['name'])
                
                price = st.number_input("Price ($)", min_value=0.0, step=0.01, format="%.2f")
            
            col1, col2 = st.columns(2)
            with col1:
                size = st.text_input("Product Size", placeholder="e.g., 1L, 2 lbs, 12 oz")
            with col2:
                unit = st.selectbox("Unit", ["bottle", "bag", "package", "each", "lb", "oz"])
            
            if st.button("💰 Update Price", type="primary"):
                if ingredient_name and ingredient_id and price > 0:
                    price_data = {
                        'price': price,
                        'size': size,
                        'unit': unit
                    }
                    
                    if manager.update_store_price(id_token, ingredient_id.lower().replace(' ', '_'), 
                                                 selected_store, price_data):
                        st.success(f"✓ Updated {ingredient_name} at {stores[selected_store]['name']}: ${price}")
                    else:
                        st.error("Failed to update price")
                else:
                    st.warning("All fields required")
            
            st.markdown("---")
            st.caption("💡 **Tip:** Update prices as you shop to keep data current")
    
    # TAB 3: View Data
    with tab3:
        st.subheader("Price Database")
        
        ingredient_to_check = st.text_input("Check prices for ingredient", 
            placeholder="e.g., olive_oil")
        
        if ingredient_to_check:
            prices = manager.get_ingredient_prices(id_token, 
                ingredient_to_check.lower().replace(' ', '_'))
            
            if prices:
                st.write(f"**Prices for {ingredient_to_check}:**")
                
                # Create comparison table
                stores = manager.get_all_stores(id_token)
                for store_id, price_data in prices.items():
                    if store_id in stores:
                        store_name = stores[store_id]['name']
                        st.write(f"- **{store_name}:** ${price_data['price']:.2f} "
                               f"({price_data['size']} {price_data['unit']})")
            else:
                st.info(f"No prices found for '{ingredient_to_check}'")


def show_store_selector():
    """User-facing store selection interface"""
    
    st.header("🏪 Select Your Stores")
    st.markdown("Choose which stores you want to shop at for this meal plan")
    
    manager = StoreManager()
    id_token = st.session_state.user['id_token']
    
    # Get available stores
    stores = manager.get_all_stores(id_token)
    
    if not stores:
        st.warning("No stores available. Contact admin to add stores.")
        return None
    
    # Show stores as checkboxes
    st.markdown("### Available Stores:")
    
    selected_stores = []
    
    # Group by type
    store_types = {}
    for store_id, store_data in stores.items():
        store_type = store_data['type']
        if store_type not in store_types:
            store_types[store_type] = []
        store_types[store_type].append((store_id, store_data))
    
    # Display by type
    for store_type, store_list in store_types.items():
        st.markdown(f"**{store_type}:**")
        
        for store_id, store_data in store_list:
            if store_data['enabled']:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    selected = st.checkbox(
                        f"{store_data['name']}", 
                        key=f"store_{store_id}",
                        value=st.session_state.get(f'selected_store_{store_id}', False)
                    )
                    
                    if selected:
                        selected_stores.append(store_id)
                        st.session_state[f'selected_store_{store_id}'] = True
                    
                    if store_data['address']:
                        st.caption(f"📍 {store_data['address']}")
                
                with col2:
                    # Could show store logo here later
                    pass
        
        st.markdown("")
    
    # Save selection
    if selected_stores:
        st.session_state.selected_stores = selected_stores
        st.success(f"✓ Selected {len(selected_stores)} store(s)")
        return selected_stores
    else:
        st.warning("Please select at least one store")
        return None
