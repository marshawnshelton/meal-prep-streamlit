"""
Simplified Shopping Checklist - Guaranteed to work!
"""

import streamlit as st
from datetime import datetime


def display_shopping_with_checklist(shopping_list, auth):
    """Display shopping list with basic functionality"""
    
    st.header("🛒 Shopping Checklist")
    
    # Stats
    total_items = sum(len(store['items']) for store in shopping_list['stores'].values())
    
    st.info(f"**Total Items:** {total_items} across {len(shopping_list['stores'])} stores")
    st.markdown("---")
    
    # Display by store
    for store_name, store_data in shopping_list['stores'].items():
        store_display = store_name.replace('_', ' ').title()
        
        with st.expander(f"**{store_display}** ({len(store_data['items'])} items)", expanded=True):
            
            # Store info
            if 'store_info' in store_data:
                st.caption(f"📍 {store_data['store_info'].get('type', '')}")
            
            st.markdown("")
            
            # Items with checkboxes
            for idx, item in enumerate(store_data['items']):
                col1, col2 = st.columns([1, 5])
                
                with col1:
                    # Checkbox
                    checked = st.checkbox(
                        "✓",
                        key=f"{store_name}_{idx}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    # Item details
                    if checked:
                        st.markdown(f"~~{item['amount']} {item['unit']} **{item['item']}**~~")
                    else:
                        st.markdown(f"{item['amount']} {item['unit']} **{item['item']}**")
                    
                    # Show recipes
                    if 'used_in' in item and item['used_in']:
                        recipes = ", ".join(item['used_in'][:2])
                        st.caption(f"Used in: {recipes}")
    
    st.markdown("---")
    st.caption("💡 Tip: Check off items as you shop! (Note: Checkboxes reset when you refresh)")
