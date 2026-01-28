// components/MealPlanCard.tsx
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Meal {
  recipe: string;
  cuisine?: string;
  time?: string;
  neighborhood?: string;
}

interface MealPlanCardProps {
  day: number;
  dayName: string;
  date: string;
  meals: {
    breakfast?: Meal;
    lunch?: Meal;
    dinner?: Meal;
  };
}

export function MealPlanCard({ day, dayName, date, meals }: MealPlanCardProps) {
  return (
    <Card className="p-6 hover:shadow-lg transition-all hover:-translate-y-0.5 border-l-4 border-l-purple-500">
      {/* Header */}
      <div className="flex justify-between items-center mb-4 pb-3 border-b">
        <div>
          <h3 className="text-2xl font-semibold text-purple-500">
            Day {day}
          </h3>
          <p className="text-gray-600 text-sm">
            {dayName}, {date}
          </p>
        </div>
      </div>

      {/* Meals */}
      <div className="space-y-4">
        {meals.breakfast && (
          <MealItem 
            type="Breakfast" 
            meal={meals.breakfast}
            icon="🌅"
            accentColor="border-l-gold-400"
          />
        )}
        
        {meals.lunch && (
          <MealItem 
            type="Lunch" 
            meal={meals.lunch}
            icon="🌞"
            accentColor="border-l-teal-300"
          />
        )}
        
        {meals.dinner && (
          <MealItem 
            type="Dinner" 
            meal={meals.dinner}
            icon="🌙"
            accentColor="border-l-purple-500"
          />
        )}
      </div>
    </Card>
  );
}

function MealItem({ 
  type, 
  meal, 
  icon, 
  accentColor 
}: { 
  type: string;
  meal: Meal;
  icon: string;
  accentColor: string;
}) {
  return (
    <div className={`pl-4 border-l-2 ${accentColor} py-2`}>
      <div className="flex items-start gap-2">
        <span className="text-xl">{icon}</span>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
            {type}
          </p>
          <p className="text-lg font-semibold text-gray-900 mt-1">
            {meal.recipe}
          </p>
          
          <div className="flex gap-2 mt-2 flex-wrap">
            {meal.cuisine && (
              <Badge variant="secondary" className="text-xs">
                {meal.cuisine}
              </Badge>
            )}
            {meal.time && (
              <Badge variant="outline" className="text-xs">
                ⏱️ {meal.time}
              </Badge>
            )}
            {meal.neighborhood && (
              <Badge className="text-xs bg-purple-500">
                📍 {meal.neighborhood}
              </Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
