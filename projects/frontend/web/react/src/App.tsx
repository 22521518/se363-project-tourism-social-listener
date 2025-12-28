import { useState } from 'react';
import { Header } from './components/Header';
import { QuickStats } from './components/QuickStats';
import { TourismClassification } from './components/TourismClassification';
import { PostTypeAnalysis } from './components/PostTypeAnalysis';
import { SemanticAnalysis } from './components/SemanticAnalysis';
import { AdvancedFilters } from './components/AdvancedFilters';
import { DetailedMentions } from './components/DetailedMentions';
import { ItineraryTracker } from './components/ItineraryTracker';

export default function App() {
  const [filters, setFilters] = useState({
    tourismPurpose: 'all',
    tourismOrg: 'all',
    tourismGeo: 'all',
    postType: 'all',
    timeRange: '7d',
    sentiment: 'all'
  });

  const [selectedView, setSelectedView] = useState<'overview' | 'posts' | 'itinerary'>('overview');

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        selectedView={selectedView}
        setSelectedView={setSelectedView}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <AdvancedFilters filters={filters} setFilters={setFilters} />
        
        {selectedView === 'overview' && (
          <>
            <QuickStats filters={filters} />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <TourismClassification filters={filters} />
              <PostTypeAnalysis filters={filters} />
            </div>
            
            <SemanticAnalysis filters={filters} />
          </>
        )}
        
        {selectedView === 'posts' && (
          <DetailedMentions filters={filters} />
        )}
        
        {selectedView === 'itinerary' && (
          <ItineraryTracker filters={filters} />
        )}
      </main>
    </div>
  );
}
