// app/page.tsx - UPDATED VERSION WITH REAL DATA
'use client';

import { useEffect, useState } from 'react';
import { MealPlanCard } from '@/components/MealPlanCard';
import { getMealPlan, getRecipes } from '@/lib/api';
import type { MealPlan, Recipe } from '@/lib/api';

export default function Home() {
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        
        // Fetch meal plan and recipes in parallel
        const [planResponse, recipesResponse] = await Promise.all([
          getMealPlan(),
          getRecipes()
        ]);
        
        setMealPlan(planResponse.meal_plan);
        setRecipes(recipesResponse.recipes);
        setError(null);
      } catch (err) {
        console.error('Failed to load data:', err);
        setError('Failed to load data from API. Make sure the backend is running on port 8000.');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-teal-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your meal plan...</p>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-teal-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-orange-100 border-l-4 border-orange-400 p-6 rounded-lg">
            <h3 className="text-orange-800 font-semibold mb-2">⚠️ Connection Error</h3>
            <p className="text-orange-700">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-4 bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
            >
              Retry
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-teal-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-purple-500 mb-2">
            🍴 Meal Prep System
          </h1>
          <p className="text-gray-600">
            Chicago food, from plan to plate.
          </p>
          <div className="mt-2 flex gap-2">
            <span className="text-sm text-teal-600 bg-teal-50 px-3 py-1 rounded-full">
              ✅ API Connected
            </span>
            <span className="text-sm text-purple-600 bg-purple-50 px-3 py-1 rounded-full">
              {recipes.length} Recipes Loaded
            </span>
          </div>
        </div>

<div className="mb-4">
  <a 
    href="/recipes" 
    className="inline-block bg-purple-500 text-white px-6 py-3 rounded-lg hover:bg-purple-600 transition-colors font-semibold"
  >
    🍳 Browse All Recipes →
  </a>
</div>
        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <StatCard 
            label="This Week" 
            value="$87.50" 
            subtext="Under budget" 
            color="teal"
          />
          <StatCard 
            label="Meals Planned" 
            value={mealPlan ? (mealPlan.days.length * 3).toString() : '0'}
            subtext={mealPlan ? `${mealPlan.planning_days} days` : 'No plan'} 
            color="purple"
          />
          <StatCard 
            label="Recipes Available" 
            value={recipes.length.toString()} 
            subtext="Ready to cook" 
            color="gold"
          />
        </div>

        {/* Meal Plan */}
        {mealPlan && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              📅 {mealPlan.plan_name}
            </h2>
            
            {mealPlan.days.slice(0, 7).map((day) => (
              <MealPlanCard 
                key={day.day}
                day={day.day}
                dayName={day.day_name}
                date={day.date}
                meals={day.meals}
              />
            ))}

            {mealPlan.days.length > 7 && (
              <div className="text-center py-4">
                <button className="text-purple-500 hover:text-purple-700 font-semibold">
                  Show {mealPlan.days.length - 7} more days →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

function StatCard({ 
  label, 
  value, 
  subtext, 
  color 
}: { 
  label: string;
  value: string;
  subtext: string;
  color: 'purple' | 'teal' | 'gold';
}) {
  const colorClasses = {
    purple: 'bg-gradient-to-br from-purple-500 to-purple-600',
    teal: 'bg-gradient-to-br from-teal-300 to-teal-600',
    gold: 'bg-gradient-to-br from-gold-400 to-gold-600',
  };

  return (
    <div className={`${colorClasses[color]} text-white p-6 rounded-xl shadow-lg`}>
      <p className="text-sm opacity-90 mb-1">{label}</p>
      <p className="text-3xl font-bold mb-1">{value}</p>
      <p className="text-xs opacity-75">{subtext}</p>
    </div>
  );
}
