"""
Meal Plan History and Selection
Allow users to view and select from past generated plans
"""

import streamlit as st
from datetime import datetime
from auth import FirebaseAuth


class PlanHistory:
    """Manage meal plan history and selection"""
    
    def __init__(self):
        self.auth = FirebaseAuth()
    
    def format_plan_display_name(self, plan: dict) -> str:
        """Create display name for a plan"""
        start = plan.get('start_date', 'Unknown')
        end = plan.get('end_date', 'Unknown')
        days = len(plan.get('days', []))
        
        # Parse date for better display
        try:
            start_obj = datetime.strptime(start, '%Y-%m-%d')
            start_formatted = start_obj.strftime('%b %d, %Y')
        except:
            start_formatted = start
        
        return f"{days}-day plan starting {start_formatted}"
    
    def get_plan_preview(self, plan: dict) -> str:
        """Get preview text for a plan"""
        if not plan or 'days' not in plan:
            return "No preview available"
        
        first_day = plan['days'][0] if plan['days'] else {}
        meals = first_day.get('meals', {})
        
        preview_meals = []
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            if meal_type in meals:
                recipe = meals[meal_type].get('recipe', '')
                if recipe:
                    preview_meals.append(f"{meal_type.title()}: {recipe}")
        
        return " • ".join(preview_meals[:2])  # Show first 2 meals


def show_plan_selector():
    """Show interface to select from past plans or generate new"""
    
    st.subheader("📅 Select or Generate Meal Plan")
    
    # Show success message if plan was just activated
    if st.session_state.get('plan_just_activated', False):
        st.success("✅ **Plan Activated Successfully!**")
        st.info("👉 Click the **'View Results'** tab above to see your meal plan and shopping list.")
        
        # Add button to generate another plan
        if st.button("🎲 Generate Another Plan", use_container_width=True, type="primary"):
            st.session_state.plan_just_activated = False
            st.rerun()
        
        # Don't show selector if we just activated
        st.session_state.plan_just_activated = False  # Clear for next time
        return
    
    user_id = st.session_state.user['user_id']
    id_token = st.session_state.user['id_token']
    
    auth = FirebaseAuth()
    history = PlanHistory()
    
    # Get saved plans
    saved_plans = auth.get_meal_plans(user_id, id_token)
    
    # Tab options
    tab1, tab2 = st.tabs(["📂 Past Plans", "✨ Generate New"])
    
    # TAB 1: Past Plans
    with tab1:
        if saved_plans:
            st.write(f"You have **{len(saved_plans)}** saved plan(s)")
            
            # Show each plan
            for idx, plan in enumerate(saved_plans):
                plan_name = history.format_plan_display_name(plan)
                plan_preview = history.get_plan_preview(plan)
                
                with st.expander(f"**{idx + 1}.** {plan_name}", expanded=(idx == 0)):
                    st.caption(plan_preview)
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Start:** {plan.get('start_date', 'N/A')}")
                    with col2:
                        st.write(f"**End:** {plan.get('end_date', 'N/A')}")
                    with col3:
                        st.write(f"**Days:** {len(plan.get('days', []))}")
                    
                    # Show first 3 days preview
                    if plan.get('days'):
                        st.markdown("**Sample Days:**")
                        for day in plan['days'][:3]:
                            meals = day.get('meals', {})
                            breakfast = meals.get('breakfast', {}).get('recipe', 'N/A')
                            lunch = meals.get('lunch', {}).get('recipe', 'N/A')
                            dinner = meals.get('dinner', {}).get('recipe', 'N/A')
                            
                            st.write(f"**Day {day.get('day', '?')}:** {breakfast} • {lunch} • {dinner}")
                    
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(f"📋 Use This Plan", key=f"use_plan_{idx}", type="primary"):
                            # Set as active plan
                            st.session_state.meal_plan = plan
                            st.session_state.active_plan_index = idx
                            st.session_state.just_generated = False  # Not newly generated
                            st.session_state.plan_just_activated = True  # Show success message
                            
                            # Clear shopping list to regenerate
                            if 'shopping_list' in st.session_state:
                                del st.session_state.shopping_list
                            
                            # Clear checkbox states
                            keys_to_delete = [key for key in st.session_state.keys() 
                                             if any(key.startswith(store) for store in 
                                                   ['costco_', 'whole_foods_', 'petes_fresh_market_', 
                                                    'jewel_', 'aldi_'])]
                            for key in keys_to_delete:
                                del st.session_state[key]
                            
                            st.rerun()
                    
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_plan_{idx}"):
                            if auth.delete_meal_plan(user_id, id_token, idx):
                                st.success("Plan deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete plan")
        
        else:
            st.info("No saved plans yet. Generate your first plan in the 'Generate New' tab!")
    
    # TAB 2: Generate New (current functionality)
    with tab2:
        st.write("Generate a fresh meal plan")
        
        # Step 1: Store Selection
        if not st.session_state.get('stores_selected', False):
            st.markdown("### 👉 Step 1: Choose Your Stores")
            st.info("Select which stores you want to shop at for this meal plan")
            
            from store_manager import show_store_selector
            selected_stores = show_store_selector()
            
            if selected_stores:
                if st.button("Continue to Plan Generation →", type="primary", use_container_width=True):
                    st.session_state.stores_selected = True
                    st.session_state.selected_stores = selected_stores
                    st.rerun()
        else:
            # Show selected stores
            selected_stores_display = ', '.join([s.replace('_', ' ').title() 
                                                 for s in st.session_state.get('selected_stores', [])])
            st.success(f"✓ Shopping at: {selected_stores_display}")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("### Step 2: Configure & Generate")
            with col2:
                if st.button("← Change Stores", use_container_width=True):
                    st.session_state.stores_selected = False
                    st.rerun()
            
            # Configuration
            col1, col2 = st.columns(2)
            
            with col1:
                days = st.number_input("Planning days", min_value=7, max_value=21, value=14,
                                      help="How many days to plan for")
            
            with col2:
                start_date = st.date_input("Start date", value=datetime.now())
            
            if st.button("🎲 Generate New Plan", type="primary", use_container_width=True):
                with st.spinner("Generating your meal plan..."):
                    # Clear ALL old data completely
                    if 'shopping_list' in st.session_state:
                        del st.session_state.shopping_list
                    if 'last_selected_stores' in st.session_state:
                        del st.session_state.last_selected_stores
                    if 'checklist_state' in st.session_state:
                        st.session_state.checklist_state = {}
                    
                    # Clear all checkbox states
                    keys_to_delete = [key for key in st.session_state.keys() 
                                     if any(key.startswith(store) for store in 
                                           ['costco_', 'whole_foods_', 'petes_fresh_market_', 
                                            'jewel_', 'aldi_'])]
                    for key in keys_to_delete:
                        del st.session_state[key]
                    
                    # Generate new plan
                    from src.meal_planner import MealPlanner
                    planner = MealPlanner()
                    meal_plan = planner.generate_meal_plan(start_date)
                    
                    # Save to Firebase
                    if auth.save_meal_plan(user_id, id_token, meal_plan):
                        st.session_state.meal_plan = meal_plan
                        st.session_state.just_generated = True
                        st.session_state.active_plan_index = 0
                        st.session_state.plan_just_activated = True
                        st.success(f"✓ Generated {days}-day meal plan and saved!")
                        st.rerun()
                    else:
                        st.session_state.meal_plan = meal_plan
                        st.session_state.just_generated = True
                        st.session_state.plan_just_activated = True
                        st.warning("Plan generated but cloud sync failed")
                        st.rerun()


def show_active_plan_indicator():
    """Show which plan is currently active"""
    
    # Don't show if no plan loaded
    if 'meal_plan' not in st.session_state or st.session_state.meal_plan is None:
        return
    
    plan = st.session_state.meal_plan
    
    # Double-check plan is valid
    if not plan or not isinstance(plan, dict):
        return
    
    # Create indicator with clear action items
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        start_date = plan.get('start_date', 'Unknown')
        end_date = plan.get('end_date', 'Unknown')
        
        if st.session_state.get('just_generated', False):
            st.info(f"📋 **Active Plan:** {start_date} to {end_date} (Just Generated)")
        else:
            st.info(f"📋 **Active Plan:** {start_date} to {end_date} (Loaded from history)")
    
    with col2:
        if st.button("📅 Switch", use_container_width=True, key="switch_plan_btn"):
            # Clear meal plan to force showing selector
            st.session_state.meal_plan = None
            st.session_state.just_generated = False
            if 'active_plan_index' in st.session_state:
                del st.session_state.active_plan_index
            st.rerun()
    
    with col3:
        # Add shortcut to View Results
        if st.button("📊 View", use_container_width=True, key="view_results_btn", 
                    help="Jump to View Results tab"):
            st.info("👉 Click the **'View Results'** tab above to see your meal plan and shopping list")
            st.balloons()
