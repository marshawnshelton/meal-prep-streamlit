# api_server.py
"""
Simple FastAPI server that sits alongside Streamlit
Provides REST API endpoints for the React frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from datetime import datetime
from typing import Optional, Dict, List

# Import your existing modules
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.meal_planner import MealPlanner
    from src.shopping_list import ShoppingListGenerator
except ImportError:
    # If src/ imports fail, try without src/
    from meal_planner import MealPlanner
    from shopping_list import ShoppingListGenerator

app = FastAPI(title="Meal Prep API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
planner = MealPlanner()
shopping_gen = ShoppingListGenerator()

# ===== MODELS =====

class GeneratePlanRequest(BaseModel):
    people: int
    budget: float
    days: int
    stores: List[str]
    start_date: str

# ===== ENDPOINTS =====

@app.get("/")
def root():
    """Health check"""
    return {
        "status": "running",
        "service": "Meal Prep API",
        "version": "1.0.0"
    }

@app.get("/api/recipes")
def get_recipes():
    """Get all recipes"""
    try:
        recipes = []
        
        # Your recipes are organized by meal type: {'breakfast': [...], 'lunch': [...]}
        if isinstance(planner.recipes, dict):
            for meal_type, recipe_list in planner.recipes.items():
                if isinstance(recipe_list, list):
                    for recipe_data in recipe_list:
                        # Add an ID if not present
                        recipe_with_id = recipe_data.copy()
                        if 'id' not in recipe_with_id:
                            # Create ID from name
                            recipe_with_id['id'] = recipe_data['name'].lower().replace(' ', '_')
                        recipes.append(recipe_with_id)
                else:
                    # Single recipe object
                    recipe_with_id = recipe_list.copy()
                    if 'id' not in recipe_with_id:
                        recipe_with_id['id'] = recipe_list['name'].lower().replace(' ', '_')
                    recipes.append(recipe_with_id)
        
        return {
            "success": True,
            "count": len(recipes),
            "recipes": recipes
        }
    except Exception as e:
        print(f"Error loading recipes: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list instead of failing
        return {
            "success": True,
            "count": 0,
            "recipes": []
        }

@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get single recipe by ID"""
    try:
        if recipe_id not in planner.recipes:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        recipe = planner.recipes[recipe_id]
        return {
            "success": True,
            "recipe": {
                "id": recipe_id,
                **recipe
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meal-plan")
def get_meal_plan(user_id: Optional[str] = None):
    """
    Get active meal plan
    In production, this would get from Firebase using user_id
    For now, returns sample data
    """
    try:
        # TODO: Get from Firebase when authentication is integrated
        # For now, return sample structure that matches your Streamlit app
        
        sample_plan = {
            "plan_name": "Sample Plan",
            "start_date": "2026-01-27",
            "end_date": "2026-02-09",
            "planning_days": 14,
            "people": 2,
            "budget": 400,
            "days": []
        }
        
        # Add sample days (in production, this comes from Firebase)
        for day in range(1, 8):  # First week
            sample_plan["days"].append({
                "day": day,
                "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day-1],
                "date": f"01/{26+day}/2026",
                "meals": {
                    "breakfast": {
                        "recipe": "Sample Breakfast",
                        "cuisine": "American",
                        "time": "20 min"
                    } if day <= 5 else None,
                    "lunch": {
                        "recipe": "Sample Lunch",
                        "cuisine": "Mediterranean",
                        "time": "30 min"
                    },
                    "dinner": {
                        "recipe": "Sample Dinner",
                        "cuisine": "Various",
                        "time": "45 min"
                    }
                }
            })
        
        return {
            "success": True,
            "meal_plan": sample_plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
def generate_meal_plan(request: GeneratePlanRequest):
    """Generate new meal plan"""
    try:
        # Use your existing meal planner logic
        meal_plan = planner.generate_plan(
            people=request.people,
            budget=request.budget,
            days=request.days,
            start_date=datetime.strptime(request.start_date, "%Y-%m-%d")
        )
        
        # Generate shopping list
        shopping_list = shopping_gen.generate_list(meal_plan, planner.recipes)
        
        # Apply store routing
        try:
            from src.store_router import apply_smart_routing
        except ImportError:
            from store_router import apply_smart_routing
        shopping_list = apply_smart_routing(shopping_list, request.stores)
        
        return {
            "success": True,
            "meal_plan": meal_plan,
            "shopping_list": shopping_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shopping-list")
def get_shopping_list(user_id: Optional[str] = None):
    """Get shopping list for active meal plan"""
    try:
        # TODO: Get from Firebase when authentication is integrated
        # For now, return sample structure
        
        sample_list = {
            "total_items": 25,
            "total_cost": 87.50,
            "stores": {
                "Costco": [
                    {
                        "id": "item_1",
                        "name": "Chicken Breast",
                        "quantity": 3,
                        "unit": "lbs",
                        "price": 12.99,
                        "checked": False
                    },
                    {
                        "id": "item_2",
                        "name": "Brown Rice",
                        "quantity": 2,
                        "unit": "lbs",
                        "price": 4.99,
                        "checked": False
                    }
                ],
                "Whole Foods": [
                    {
                        "id": "item_3",
                        "name": "Organic Spinach",
                        "quantity": 1,
                        "unit": "bunch",
                        "price": 2.99,
                        "checked": False
                    }
                ]
            }
        }
        
        return {
            "success": True,
            "shopping_list": sample_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stores")
def get_stores():
    """Get available stores"""
    try:
        # Read from your stores.json
        with open('data/stores.json', 'r') as f:
            stores_data = json.load(f)
        
        return {
            "success": True,
            "stores": stores_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== RUN =====

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Meal Prep API Server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 Docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
