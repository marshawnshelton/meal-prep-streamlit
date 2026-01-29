// app/recipes/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { RecipeCard } from '@/components/RecipeCard';
import { getRecipes } from '@/lib/api';
import type { Recipe } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Search } from 'lucide-react';

export default function RecipesPage() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [filteredRecipes, setFilteredRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMealType, setSelectedMealType] = useState<string>('all');
  const [selectedCuisine, setSelectedCuisine] = useState<string>('all');

  // Load recipes
  useEffect(() => {
    async function loadRecipes() {
      try {
        const response = await getRecipes();
        setRecipes(response.recipes);
        setFilteredRecipes(response.recipes);
      } catch (error) {
        console.error('Failed to load recipes:', error);
      } finally {
        setLoading(false);
      }
    }
    loadRecipes();
  }, []);

  // Get unique meal types and cuisines
  const mealTypes = ['all', ...new Set(recipes.map(r => r.meal_type).filter(Boolean))];
  const cuisines = ['all', ...new Set(recipes.map(r => r.cuisine).filter(Boolean))];

  // Filter recipes
  useEffect(() => {
    let filtered = recipes;

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(recipe =>
        recipe.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        recipe.cuisine?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by meal type
    if (selectedMealType !== 'all') {
      filtered = filtered.filter(recipe => recipe.meal_type === selectedMealType);
    }

    // Filter by cuisine
    if (selectedCuisine !== 'all') {
      filtered = filtered.filter(recipe => recipe.cuisine === selectedCuisine);
    }

    setFilteredRecipes(filtered);
  }, [searchQuery, selectedMealType, selectedCuisine, recipes]);

  if (loading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-teal-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading recipes...</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-teal-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-purple-500 mb-2">
            🍳 Recipe Collection
          </h1>
          <p className="text-gray-600">
            Browse {recipes.length} delicious, healthy recipes
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-xl">
            <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search recipes by name or cuisine..."
              className="pl-10 h-12 text-base"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Filters */}
        <div className="mb-8 space-y-4">
          {/* Meal Type Filter */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Meal Type:</p>
            <div className="flex flex-wrap gap-2">
              {mealTypes.map((mealType) => (
                <button
                  key={mealType}
                  onClick={() => setSelectedMealType(mealType)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    selectedMealType === mealType
                      ? 'bg-purple-500 text-white'
                      : 'bg-white text-gray-700 hover:bg-purple-100 border border-gray-200'
                  }`}
                >
                  {mealType === 'all' ? 'All Meals' : mealType.charAt(0).toUpperCase() + mealType.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Cuisine Filter */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Cuisine:</p>
            <div className="flex flex-wrap gap-2">
              {cuisines.slice(0, 8).map((cuisine) => (
                <button
                  key={cuisine}
                  onClick={() => setSelectedCuisine(cuisine)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    selectedCuisine === cuisine
                      ? 'bg-teal-500 text-white'
                      : 'bg-white text-gray-700 hover:bg-teal-100 border border-gray-200'
                  }`}
                >
                  {cuisine === 'all' ? 'All Cuisines' : cuisine}
                </button>
              ))}
              {cuisines.length > 8 && (
                <span className="px-4 py-2 text-sm text-gray-500">
                  +{cuisines.length - 8} more
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-gray-600">
            Showing <span className="font-semibold text-purple-600">{filteredRecipes.length}</span> recipes
          </p>
        </div>

        {/* Recipe Grid */}
        {filteredRecipes.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRecipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onClick={() => {
                  // TODO: Navigate to recipe detail page
                  console.log('Clicked recipe:', recipe.name);
                }}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <p className="text-gray-500 text-lg">No recipes found matching your filters</p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedMealType('all');
                setSelectedCuisine('all');
              }}
              className="mt-4 text-purple-500 hover:text-purple-700 font-semibold"
            >
              Clear all filters
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
