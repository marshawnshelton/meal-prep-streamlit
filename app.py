#!/usr/bin/env python3
"""
Meal Prep System - Web Interface
Built with Streamlit for easy, user-friendly meal planning
Now with Firebase Authentication!
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from meal_planner import MealPlanner
from shopping_list import ShoppingListGenerator
from excel_export import ExcelExporter

# Import authentication
from auth import init_session_state, show_auth_page, logout, FirebaseAuth
from store_manager import StoreManager, show_admin_panel, show_store_selector
from store_router import apply_smart_routing
from plan_history import show_plan_selector, show_active_plan_indicator


# Inline helper functions (avoiding import issues)
def _update_checkbox(item_id):
    """Update checkbox state without blocking UI"""
    # Update in session state immediately
    st.session_state.checklist_state[item_id] = st.session_state[item_id]
    
    # Save to Firebase in background (non-blocking)
    import threading
    def save_async():
        try:
            from firebase_config import FIRESTORE_URL
            user_id = st.session_state.user['user_id']
            id_token = st.session_state.user['id_token']
            
            url = f"{FIRESTORE_URL}/users/{user_id}/checklist/current"
            headers = {"Authorization": f"Bearer {id_token}"}
            fields = {
                "state": {"stringValue": json.dumps(st.session_state.checklist_state)},
                "updated_at": {"timestampValue": datetime.now().isoformat() + "Z"}
            }
            requests.patch(url, json={"fields": fields}, headers=headers, timeout=1)
        except:
            pass
    
    # Run in background thread
    thread = threading.Thread(target=save_async, daemon=True)
    thread.start()


def display_shopping_with_checklist(shopping_list, auth):
    """Display shopping list with Firebase-synced checkboxes"""
    import json
    import requests
    from firebase_config import FIRESTORE_URL
    
    st.header("🛒 Shopping Checklist")
    
    # Get user info
    user_id = st.session_state.user['user_id']
    id_token = st.session_state.user['id_token']
    
    # Load saved state from Firebase
    if 'checklist_state' not in st.session_state:
        try:
            url = f"{FIRESTORE_URL}/users/{user_id}/checklist/current"
            headers = {"Authorization": f"Bearer {id_token}"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get('fields', {})
                if 'state' in fields:
                    state_json = fields['state'].get('stringValue', '{}')
                    st.session_state.checklist_state = json.loads(state_json)
                else:
                    st.session_state.checklist_state = {}
            else:
                st.session_state.checklist_state = {}
        except:
            st.session_state.checklist_state = {}
    
    checklist_state = st.session_state.checklist_state
    
    # Stats - only count checkboxes for items in CURRENT shopping list
    total_items = sum(len(store['items']) for store in shopping_list['stores'].values())
    
    # Count only items that exist in current list AND are checked
    checked_items = 0
    for store_name, store_data in shopping_list['stores'].items():
        for idx in range(len(store_data['items'])):
            item_id = f"{store_name}_{idx}"
            if checklist_state.get(item_id, False) is True:
                checked_items += 1
    
    progress = checked_items / total_items if total_items > 0 else 0
    
    # Progress bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        st.metric("Checked", f"{checked_items}/{total_items}")
    with col3:
        if st.button("📄 PDF", use_container_width=True):
            st.session_state.show_shopping_pdf = True
    with col4:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.checklist_state = {}
            try:
                url = f"{FIRESTORE_URL}/users/{user_id}/checklist/current"
                headers = {"Authorization": f"Bearer {id_token}"}
                fields = {
                    "state": {"stringValue": "{}"},
                    "updated_at": {"timestampValue": datetime.now().isoformat() + "Z"}
                }
                requests.patch(url, json={"fields": fields}, headers=headers, timeout=5)
            except:
                pass
            st.rerun()
    
    # PDF Download modal
    if st.session_state.get('show_shopping_pdf', False):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import inch
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            story.append(Paragraph("🛒 Shopping List", styles['Title']))
            story.append(Spacer(1, 0.3*inch))
            
            for store_name, store_data in shopping_list['stores'].items():
                story.append(Paragraph(store_name.replace('_', ' ').title(), styles['Heading2']))
                
                table_data = [['☐', 'Item', 'Amount']]
                for idx, item in enumerate(store_data['items']):
                    item_id = f"{store_name}_{idx}"
                    checked = '✓' if checklist_state.get(item_id, False) else '☐'
                    table_data.append([checked, item['item'], f"{item['amount']} {item['unit']}"])
                
                table = Table(table_data, colWidths=[0.5*inch, 3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.3*inch))
            
            doc.build(story)
            buffer.seek(0)
            
            st.download_button(
                "⬇️ Download Shopping List PDF",
                buffer.getvalue(),
                f"shopping_list_{datetime.now().strftime('%Y%m%d')}.pdf",
                "application/pdf",
                use_container_width=True
            )
            st.session_state.show_shopping_pdf = False
        except Exception as e:
            st.error(f"PDF generation error: {e}")
    
    st.markdown("---")
    
    # Display by store
    for store_name, store_data in shopping_list['stores'].items():
        store_display = store_name.replace('_', ' ').title()
        store_items = store_data['items']
        
        # Count checked items for this store
        store_checked = sum(1 for idx in range(len(store_items))
                           if checklist_state.get(f"{store_name}_{idx}", False))
        
        with st.expander(f"**{store_display}** ({store_checked}/{len(store_items)} checked)", 
                        expanded=(store_checked < len(store_items))):
            if 'store_info' in store_data:
                st.caption(f"📍 {store_data['store_info'].get('type', '')}")
            st.markdown("")
            
            for idx, item in enumerate(store_items):
                item_id = f"{store_name}_{idx}"
                col1, col2 = st.columns([1, 5])
                
                with col1:
                    # Simplified checkbox - direct binding to session state
                    checked = st.checkbox("✓", value=checklist_state.get(item_id, False),
                                        key=item_id, label_visibility="collapsed",
                                        on_change=lambda iid=item_id: _update_checkbox(iid))
                
                with col2:
                    if checklist_state.get(item_id, False):
                        st.markdown(f"~~{item['amount']} {item['unit']} **{item['item']}**~~")
                    else:
                        st.markdown(f"{item['amount']} {item['unit']} **{item['item']}**")
                    
                    if 'used_in' in item and item['used_in']:
                        recipes = ", ".join(item['used_in'][:2])
                        if len(item['used_in']) > 2:
                            recipes += f" +{len(item['used_in'])-2}"
                        st.caption(f"Used in: {recipes}")
    
    st.markdown("---")
    st.success("✅ Your progress is automatically saved!")


def display_recipe_booklet_with_pdf(meal_plan, planner, auth):
    """Display recipe booklet with PDF download"""
    st.header("📖 Recipe Booklet")
    unique_recipes = set()
    for day in meal_plan['days']:
        for meal_type, meal_info in day.get('meals', {}).items():
            if meal_info and meal_info.get('recipe'):
                unique_recipes.add(meal_info['recipe'])
    
    st.markdown(f"### {len(unique_recipes)} Recipes in Your Plan")
    st.markdown(f"**Meal Plan:** {meal_plan['start_date']} to {meal_plan['end_date']}")
    
    # PDF Download button at top
    if st.button("📄 Download PDF Booklet", type="primary", use_container_width=True):
        with st.spinner("Generating professional PDF..."):
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                from io import BytesIO
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
                styles = getSampleStyleSheet()
                
                title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, 
                                            textColor=colors.HexColor('#1f77b4'), spaceAfter=20, alignment=1)
                recipe_style = ParagraphStyle('Recipe', parent=styles['Heading2'], fontSize=16,
                                             textColor=colors.HexColor('#2ca02c'), spaceAfter=12)
                
                story = []
                
                # Cover
                story.append(Spacer(1, 1.5*inch))
                story.append(Paragraph("📖 Recipe Booklet", title_style))
                story.append(Spacer(1, 0.5*inch))
                story.append(Paragraph(f"Meal Plan: {meal_plan['start_date']} to {meal_plan['end_date']}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(f"{len(unique_recipes)} Delicious Recipes", styles['Normal']))
                story.append(PageBreak())
                
                # Each recipe
                for i, recipe_name in enumerate(sorted(unique_recipes), 1):
                    recipe = None
                    for category, recipes in planner.recipes.items():
                        for r in recipes:
                            if r['name'] == recipe_name:
                                recipe = r
                                break
                        if recipe:
                            break
                    
                    if recipe:
                        story.append(Paragraph(f"{i}. {recipe['name']}", recipe_style))
                        story.append(Paragraph(f"<b>Cuisine:</b> {recipe.get('cuisine', 'N/A')} | "
                                             f"<b>Servings:</b> {recipe.get('servings', 'N/A')} | "
                                             f"<b>Time:</b> {recipe.get('prep_time', 0)}+{recipe.get('cook_time', 0)} min",
                                             styles['Normal']))
                        story.append(Spacer(1, 0.2*inch))
                        
                        # Ingredients
                        story.append(Paragraph("<b>Ingredients:</b>", styles['Normal']))
                        ingredients = recipe.get('ingredients', [])
                        if isinstance(ingredients, dict):
                            for section, ing_list in ingredients.items():
                                story.append(Paragraph(f"<i>{section.title()}:</i>", styles['Normal']))
                                for ing in ing_list:
                                    if isinstance(ing, dict):
                                        story.append(Paragraph(f"• {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}", 
                                                             styles['Normal']))
                        else:
                            for ing in ingredients:
                                if isinstance(ing, dict):
                                    story.append(Paragraph(f"• {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}", 
                                                         styles['Normal']))
                        
                        story.append(Spacer(1, 0.2*inch))
                        story.append(Paragraph("<b>Instructions:</b>", styles['Normal']))
                        for j, step in enumerate(recipe.get('instructions', []), 1):
                            story.append(Paragraph(f"{j}. {step}", styles['Normal']))
                        
                        if i < len(unique_recipes):
                            story.append(PageBreak())
                
                doc.build(story)
                buffer.seek(0)
                
                st.download_button(
                    label="⬇️ Download PDF",
                    data=buffer.getvalue(),
                    file_name=f"recipe_booklet_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✓ PDF generated successfully!")
                
            except ImportError:
                st.error("PDF generation requires 'reportlab' package. Add it to requirements.txt!")
            except Exception as e:
                st.error(f"PDF generation error: {e}")
    
    st.markdown("---")
    
    # In-app viewer
    for i, recipe_name in enumerate(sorted(unique_recipes), 1):
        recipe = None
        for category, recipes in planner.recipes.items():
            for r in recipes:
                if r['name'] == recipe_name:
                    recipe = r
                    break
            if recipe:
                break
        
        if recipe:
            with st.expander(f"**{i}. {recipe['name']}** - {recipe.get('cuisine', 'N/A')}", expanded=(i == 1)):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Servings", recipe.get('servings', 'N/A'))
                with col2:
                    st.metric("Prep", f"{recipe.get('prep_time', 'N/A')} min")
                with col3:
                    st.metric("Cook", f"{recipe.get('cook_time', 'N/A')} min")
                
                st.markdown("---")
                st.markdown("### 🥘 Ingredients")
                ingredients = recipe.get('ingredients', [])
                if isinstance(ingredients, dict):
                    for section, ing_list in ingredients.items():
                        st.markdown(f"**{section.title()}:**")
                        for ing in ing_list:
                            if isinstance(ing, dict):
                                st.markdown(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                        st.markdown("")
                else:
                    for ing in ingredients:
                        if isinstance(ing, dict):
                            st.markdown(f"- {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}")
                
                st.markdown("---")
                st.markdown("### 👩‍🍳 Instructions")
                for j, step in enumerate(recipe.get('instructions', []), 1):
                    st.markdown(f"**{j}.** {step}")
                
                if recipe.get('cultural_note'):
                    st.markdown("---")
                    st.info(f"💡 {recipe.get('cultural_note')}")


# Page configuration
st.set_page_config(
    page_title="Meal Prep System",
    page_icon="🍽️",
    layout="wide"
)

# Initialize authentication
init_session_state()

# Initialize other session state
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = None
if 'selected_meals' not in st.session_state:
    st.session_state.selected_meals = {}
if 'recipes' not in st.session_state:
    planner = MealPlanner()
    st.session_state.recipes = planner.recipes
    st.session_state.planner = planner

# Load user's last meal plan if authenticated
if 'meal_plan_loaded' not in st.session_state:
    st.session_state.meal_plan_loaded = False

if st.session_state.authenticated and not st.session_state.meal_plan_loaded:
    try:
        auth = FirebaseAuth()
        user_id = st.session_state.user['user_id']
        id_token = st.session_state.user['id_token']
        
        # Get most recent meal plan
        meal_plans = auth.get_meal_plans(user_id, id_token)
        if meal_plans and len(meal_plans) > 0:
            # Load most recent plan
            latest_plan = meal_plans[0]
            st.session_state.meal_plan = latest_plan
        
        st.session_state.meal_plan_loaded = True
    except:
        st.session_state.meal_plan_loaded = True  # Mark as attempted even if failed


def main():
    if not st.session_state.authenticated:
        show_auth_page()
        return
    
    show_main_app()


def show_main_app():
    """Main application after authentication"""
    
    # Check if admin panel should be shown
    if st.session_state.get('show_admin', False):
        show_admin_panel(st.session_state.user['email'])
        
        if st.button("← Back to App"):
            st.session_state.show_admin = False
            st.rerun()
        
        return  # Don't show main app while in admin
    
    # Check if recipe admin should be shown
    if st.session_state.get('show_recipe_admin', False):
        from recipe_manager import show_recipe_admin
        show_recipe_admin()
        
        if st.button("← Back to App"):
            st.session_state.show_recipe_admin = False
            st.rerun()
        
        return  # Don't show main app while in recipe admin
    
    # Top bar
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🍽️ Meal Prep System")
        st.markdown("### Plan your meals, generate shopping lists, get recipes")
    with col2:
        user_email = st.session_state.user['email']
        st.write("")
        st.caption(f"👤 {user_email.split('@')[0]}")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        profile = st.session_state.user.get('profile', {})
        if profile:
            with st.expander("👤 Your Profile"):
                st.caption(f"**Goal:** {profile.get('primary_goal', 'N/A')}")
                st.caption(f"**Household:** {profile.get('household_size', 2)} people")
                st.caption(f"**ZIP:** {profile.get('zipcode', 'N/A')}")
        
        st.markdown("---")
        
        people = st.number_input("Number of people", min_value=1, max_value=10, 
                                value=config['system']['people'])
        budget = st.number_input("Bi-weekly budget ($)", min_value=100, max_value=1000, 
                                value=config['system']['budget_per_cycle'], step=50)
        days = st.slider("Planning days", min_value=1, max_value=30, 
                        value=config['system']['planning_cycle_days'])
        start_date = st.date_input("Start date", value=datetime.now())
        
        st.markdown("---")
        st.markdown("**Stores:**")
        for store in config['stores'].keys():
            st.markdown(f"✓ {store.replace('_', ' ').title()}")
        
        st.markdown("---")
        st.markdown(f"**📖 Total Recipes: {sum(len(r) for r in st.session_state.recipes.values())}**")
        for category, recipe_list in st.session_state.recipes.items():
            category_name = category.replace('_', ' ').title()
            st.caption(f"{category_name}: {len(recipe_list)}")
        
        # Admin panel access (if admin user)
        ADMIN_EMAILS = ['marshawnshelton3@gmail.com', 'marshawn.shelton@isosalus.com']
        if user_email in ADMIN_EMAILS:
            st.markdown("---")
            if st.button("🔧 Store Admin", use_container_width=True):
                st.session_state.show_admin = True
            if st.button("🍳 Recipe Admin", use_container_width=True):
                st.session_state.show_recipe_admin = True
    
    # Show which plan is currently active
    if 'meal_plan' in st.session_state:
        show_active_plan_indicator()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Plans", "✋ Custom Select", "📖 Browse Recipes", "📊 View Results"])
    
    with tab1:
        st.header("Meal Plan Selection")
        show_plan_selector()
    
    with tab2:
        st.header("Custom Meal Selection")
        st.info("⚠️ Custom meal selection temporarily disabled for optimization. Coming back soon!")
    
    with tab3:
        st.header("📖 Browse All Recipes")
        st.markdown(f"**{sum(len(r) for r in st.session_state.recipes.values())} recipes available**")
        
        # Search
        search = st.text_input("🔍 Search recipes", placeholder="e.g., chicken, Italian, breakfast")
        
        # Get all recipes
        all_recipes = []
        for cat, recipe_list in st.session_state.recipes.items():
            all_recipes.extend(recipe_list)
        
        # Filter if search
        if search:
            all_recipes = [r for r in all_recipes 
                          if search.lower() in r['name'].lower() 
                          or search.lower() in r.get('cuisine', '').lower()]
            st.caption(f"Found {len(all_recipes)} matching recipes")
        
        # Display recipes (limit to 20)
        for recipe in all_recipes[:20]:
            with st.expander(f"**{recipe['name']}** - {recipe.get('cuisine', 'N/A')}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Cuisine:** {recipe.get('cuisine', 'N/A')}")
                    st.markdown(f"**Meal Type:** {recipe.get('meal_type', 'N/A').replace('_', ' ').title()}")
                with col2:
                    st.markdown(f"**Servings:** {recipe.get('servings', 'N/A')}")
                    st.markdown(f"**Time:** {recipe.get('prep_time', 0)}+{recipe.get('cook_time', 0)} min")
    
    with tab4:
        if st.session_state.meal_plan is None:
            st.info("Generate a meal plan first to see results here")
        else:
            meal_plan = st.session_state.meal_plan
            
            # Show if this is a loaded plan
            if st.session_state.get('meal_plan_loaded') and not st.session_state.get('just_generated'):
                st.info(f"📋 Loaded your saved meal plan from {meal_plan.get('start_date', 'recently')}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Meal Plan", "🛒 Shopping List", "📖 Recipes"])
            
            with subtab1:
                st.header("📅 Your Meal Plan")
                for day in meal_plan['days']:
                    with st.expander(f"**Day {day['day']} - {day['day_name']}, {day['date']}**"):
                        for meal_type, meal_info in day['meals'].items():
                            meal_name = meal_type.replace('_', ' ').title()
                            recipe_name = meal_info['recipe']
                            cuisine = meal_info.get('cuisine', '')
                            timing = meal_info.get('time', '')
                            
                            # Restored detailed display
                            if timing:
                                st.markdown(f"**{meal_name}** ({timing})")
                            else:
                                st.markdown(f"**{meal_name}**")
                            
                            st.markdown(f"→ {recipe_name}")
                            if cuisine:
                                st.caption(f"Cuisine: {cuisine}")
                            st.markdown("")
            
            with subtab2:
                # Add refresh button at top for debugging
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown("")  # Spacer
                with col2:
                    if st.button("🔄 Refresh", key="refresh_shopping"):
                        # Clear shopping list
                        if 'shopping_list' in st.session_state:
                            del st.session_state.shopping_list
                        
                        # Clear all checkbox states
                        keys_to_delete = [key for key in st.session_state.keys() 
                                         if any(key.startswith(store) for store in 
                                               ['costco_', 'whole_foods_', 'petes_fresh_market_', 
                                                'jewel_', 'aldi_'])]
                        for key in keys_to_delete:
                            del st.session_state[key]
                        
                        st.rerun()
                
                # Clear shopping list if stores changed
                if 'last_selected_stores' not in st.session_state:
                    st.session_state.last_selected_stores = []
                
                current_stores = st.session_state.get('selected_stores', [])
                if current_stores != st.session_state.last_selected_stores:
                    # Stores changed, regenerate shopping list
                    if 'shopping_list' in st.session_state:
                        del st.session_state.shopping_list
                    st.session_state.last_selected_stores = current_stores
                
                if 'shopping_list' not in st.session_state:
                    with st.spinner("Generating shopping list..."):
                        generator = ShoppingListGenerator()
                        shopping_list = generator.generate_shopping_list(meal_plan)
                        
                        # Apply smart routing if stores were selected
                        if st.session_state.get('selected_stores'):
                            st.info(f"🔄 Routing to: {', '.join([s.replace('_', ' ').title() for s in st.session_state.selected_stores])}")
                            shopping_list = apply_smart_routing(
                                shopping_list, 
                                st.session_state.selected_stores
                            )
                            st.success("✨ Smart routing applied - check terminal for details!")
                        
                        st.session_state.shopping_list = shopping_list
                
                auth = FirebaseAuth()
                display_shopping_with_checklist(st.session_state.shopping_list, auth)
            
            with subtab3:
                auth = FirebaseAuth()
                display_recipe_booklet_with_pdf(meal_plan, st.session_state.planner, auth)


if __name__ == "__main__":
    main()
