import { useState } from "react";
import { PostTypeAnalysis } from "../components/PostTypeAnalysis";
import { SemanticAnalysis } from "../components/SemanticAnalysis";
import { QuickStats } from "../components/QuickStats";
import { TourismClassification } from "../components/TourismClassification";
import { AdvancedFilters } from "../components/AdvancedFilters";

export default function Dashboard() {
  const [filters, setFilters] = useState({
    tourismType: "all",
    // tourismOrg: 'all',
    postIntention: "all",
    tourismGeo: "all",
    postType: "all",
    timeRange: "7d",
    sentiment: "all",
  });
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* <AdvancedFilters filters={filters} setFilters={setFilters} /> */}
        {/* <QuickStats filters={filters} /> */}

        <TourismClassification filters={filters} />
        {/* <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <PostTypeAnalysis filters={filters} />
        </div> */}

        <SemanticAnalysis filters={filters} />
      </main>
    </div>
  );
}
