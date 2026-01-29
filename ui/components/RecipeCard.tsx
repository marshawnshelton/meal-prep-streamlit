// components/RecipeCard.tsx
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, Users, ChefHat } from 'lucide-react';

interface RecipeCardProps {
  recipe: {
    id: string;
    name: string;
    cuisine: string;
    meal_type: string;
    prep_time?: number;
    cook_time?: number;
    servings?: number;
    health_benefits?: string[];
    neighborhood?: string;
    cultural_note?: string;
  };
  onClick?: () => void;
}

export function RecipeCard({ recipe, onClick }: RecipeCardProps) {
  const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);
  
  // Map meal type to color
  const mealTypeColors = {
    breakfast: 'bg-gold-400 text-white',
    lunch: 'bg-teal-300 text-white',
    dinner: 'bg-purple-500 text-white',
    snack: 'bg-orange-400 text-white',
  };
  
  const mealTypeColor = mealTypeColors[recipe.meal_type?.toLowerCase() as keyof typeof mealTypeColors] || 'bg-gray-500 text-white';

  return (
    <Card 
      className="overflow-hidden hover:shadow-xl transition-all hover:-translate-y-1 cursor-pointer group"
      onClick={onClick}
    >
      {/* Image Placeholder with Gradient */}
      <div className="relative h-48 bg-gradient-to-br from-purple-100 via-teal-50 to-gold-100 flex items-center justify-center">
        <div className="text-6xl opacity-30 group-hover:scale-110 transition-transform">
          🍽️
        </div>
        {/* Meal Type Badge */}
        <div className={`absolute top-3 left-3 ${mealTypeColor} px-3 py-1 rounded-full text-xs font-semibold uppercase`}>
          {recipe.meal_type}
        </div>
      </div>
      
      {/* Content */}
      <div className="p-4">
        {/* Recipe Name */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 min-h-[3.5rem]">
          {recipe.name}
        </h3>
        
        {/* Cuisine Badge */}
        <div className="mb-3">
          <Badge variant="secondary" className="text-xs">
            <ChefHat className="w-3 h-3 mr-1" />
            {recipe.cuisine}
          </Badge>
        </div>

        {/* Neighborhood Badge (if exists) */}
        {recipe.neighborhood && (
          <div className="mb-3">
            <Badge className="text-xs bg-purple-500">
              📍 {recipe.neighborhood}
            </Badge>
          </div>
        )}
        
        {/* Meta Info */}
        <div className="flex gap-3 text-sm text-gray-600 mb-3">
          {totalTime > 0 && (
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{totalTime} min</span>
            </div>
          )}
          {recipe.servings && (
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              <span>{recipe.servings}</span>
            </div>
          )}
        </div>

        {/* Health Benefits */}
        {recipe.health_benefits && recipe.health_benefits.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {recipe.health_benefits.slice(0, 2).map((benefit, idx) => (
              <span 
                key={idx}
                className="text-xs bg-teal-50 text-teal-700 px-2 py-1 rounded"
              >
                {benefit.replace(/_/g, ' ')}
              </span>
            ))}
            {recipe.health_benefits.length > 2 && (
              <span className="text-xs text-gray-500">
                +{recipe.health_benefits.length - 2} more
              </span>
            )}
          </div>
        )}

        {/* Cultural Note Preview */}
        {recipe.cultural_note && (
          <p className="text-xs text-gray-500 mt-2 line-clamp-2">
            {recipe.cultural_note}
          </p>
        )}
      </div>
    </Card>
  );
}
