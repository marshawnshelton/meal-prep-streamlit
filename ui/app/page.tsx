// app/page.tsx
import { MealPlanCard } from '@/components/MealPlanCard';

export default function Home() {
  const samplePlan = {
    day: 1,
    dayName: 'Monday',
    date: '01/27/2026',
    meals: {
      breakfast: {
        recipe: 'Pullman Porter\'s Morning Power Bowl',
        cuisine: 'American Soul',
        time: '25 min',
        neighborhood: 'Pullman',
      },
      lunch: {
        recipe: 'Mediterranean Quinoa Bowl',
        cuisine: 'Mediterranean',
        time: '15 min',
      },
      dinner: {
        recipe: 'Za\'atar Roasted Chicken',
        cuisine: 'Middle Eastern',
        time: '45 min',
        neighborhood: 'Hyde Park',
      },
    },
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-teal-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-purple-500 mb-2">
            🍴 Meal Prep System
          </h1>
          <p className="text-gray-600">
            Chicago's neighborhoods, in your kitchen
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <StatCard 
            label="This Week" 
            value="$87.50" 
            subtext="Under budget" 
            color="teal"
          />
          <StatCard 
            label="Meals Planned" 
            value="21" 
            subtext="7 days" 
            color="purple"
          />
          <StatCard 
            label="Recipes Saved" 
            value="156" 
            subtext="+12 this week" 
            color="gold"
          />
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            📅 This Week's Meals
          </h2>
          <MealPlanCard {...samplePlan} />
          
          <MealPlanCard 
            day={2}
            dayName="Tuesday"
            date="01/28/2026"
            meals={{
              breakfast: {
                recipe: 'Classic Oatmeal Bowl',
                time: '10 min',
              },
              lunch: {
                recipe: 'Grilled Chicken Salad',
                cuisine: 'American',
                time: '20 min',
              },
              dinner: {
                recipe: 'Humboldt Harmony Bowl',
                cuisine: 'Fusion',
                time: '35 min',
                neighborhood: 'Humboldt Park',
              },
            }}
          />
        </div>
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
