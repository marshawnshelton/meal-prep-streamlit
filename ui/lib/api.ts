// lib/api.ts
/**
 * API client for Meal Prep backend
 * Connects React frontend to Python FastAPI server
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ===== TYPES =====

export interface Meal {
  recipe: string;
  cuisine?: string;
  time?: string;
  neighborhood?: string;
}

export interface MealPlanDay {
  day: number;
  day_name: string;
  date: string;
  meals: {
    breakfast?: Meal;
    lunch?: Meal;
    dinner?: Meal;
  };
}

export interface MealPlan {
  plan_name: string;
  start_date: string;
  end_date: string;
  planning_days: number;
  people: number;
  budget: number;
  days: MealPlanDay[];
}

export interface Recipe {
  id: string;
  name: string;
  cuisine: string;
  meal_type: string;
  prep_time: number;
  cook_time: number;
  servings: number;
  cost_tier: string;
  ingredients: any[];
  instructions: string[];
  neighborhood?: string;
  cultural_story?: string;
}

export interface ShoppingItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  price: number;
  checked: boolean;
}

export interface ShoppingList {
  total_items: number;
  total_cost: number;
  stores: {
    [storeName: string]: ShoppingItem[];
  };
}

export interface Store {
  name: string;
  type: string;
  address?: string;
  tier?: string;
}

// ===== API CLIENT =====

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ===== MEAL PLAN =====

  async getMealPlan(userId?: string): Promise<{ success: boolean; meal_plan: MealPlan }> {
    const params = userId ? `?user_id=${userId}` : '';
    return this.request(`/api/meal-plan${params}`);
  }

  async generateMealPlan(config: {
    people: number;
    budget: number;
    days: number;
    stores: string[];
    start_date: string;
  }): Promise<{ success: boolean; meal_plan: MealPlan; shopping_list: ShoppingList }> {
    return this.request('/api/generate', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // ===== RECIPES =====

  async getRecipes(): Promise<{ success: boolean; count: number; recipes: Recipe[] }> {
    return this.request('/api/recipes');
  }

  async getRecipe(recipeId: string): Promise<{ success: boolean; recipe: Recipe }> {
    return this.request(`/api/recipes/${recipeId}`);
  }

  // ===== SHOPPING LIST =====

  async getShoppingList(userId?: string): Promise<{ success: boolean; shopping_list: ShoppingList }> {
    const params = userId ? `?user_id=${userId}` : '';
    return this.request(`/api/shopping-list${params}`);
  }

  // ===== STORES =====

  async getStores(): Promise<{ success: boolean; stores: any }> {
    return this.request('/api/stores');
  }

  // ===== HEALTH CHECK =====

  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.request('/');
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export individual functions for convenience
export const getMealPlan = (userId?: string) => api.getMealPlan(userId);
export const generateMealPlan = (config: any) => api.generateMealPlan(config);
export const getRecipes = () => api.getRecipes();
export const getRecipe = (id: string) => api.getRecipe(id);
export const getShoppingList = (userId?: string) => api.getShoppingList(userId);
export const getStores = () => api.getStores();
