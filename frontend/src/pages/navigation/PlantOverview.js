import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Factory, Activity, AlertCircle } from 'lucide-react';
import { useNavigationContext } from '../../contexts/NavigationContext';
import Breadcrumb from '../../components/Breadcrumb';
import ExpandableEntityCard from '../../components/ExpandableEntityCard';
import { Button } from '../../components/ui/button';


const PlantOverview = () => {
  const navigate = useNavigate();
  const { setPlantContext, clearContext } = useNavigationContext();
  const [plants, setPLants] = useState([]);
  const [areas, setAreas] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Clear context when viewing plant overview
    clearContext();
    loadPlantsAndAreas();
  }, [clearContext]);

  const loadPlantsAndAreas = async () => {
    try {
      setLoading(true);
      
      // Load plants
      const plantsResponse = await fetch('/api/graph/plants');
      if (!plantsResponse.ok) throw new Error('Failed to load plants');
      const plantsData = await plantsResponse.json();
      setPLants(plantsData.plants || []);

      // Load areas for each plant
      const areasData = {};
      for (const plant of plantsData.plants || []) {
        try {
          const areasResponse = await fetch(`/api/graph/plants/${encodeURIComponent(plant.name)}/areas`);
          if (areasResponse.ok) {
            const plantAreas = await areasResponse.json();
            areasData[plant.name] = plantAreas.asset_areas || [];
          }
        } catch (err) {
          console.warn(`Failed to load areas for plant ${plant.name}:`, err);
          areasData[plant.name] = [];
        }
      }
      setAreas(areasData);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAreaClick = (area) => {
    navigate(`/navigate/area/${encodeURIComponent(area.name)}`);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-16 text-stone-700 text-lg">
        <Activity className="animate-spin mr-2" size={24} />
        Loading factory data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center p-16 text-stone-700 text-center">
        <AlertCircle size={48} className="mb-4" />
        <h3 className="text-xl font-semibold mb-2">Failed to load factory data</h3>
        <p className="mb-4">{error}</p>
        <Button onClick={loadPlantsAndAreas}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full">
      <Breadcrumb 
        items={[
          { label: 'Plants', path: '/navigate', isActive: true }
        ]} 
      />
      
      <div className="text-center mb-12">
        <h1 className="text-4xl text-stone-900 mb-2 font-bold tracking-tight">Factory Navigation</h1>
        <p className="text-stone-500 text-lg mb-8">
          Explore your industrial assets through an interactive plant and area overview
        </p>
      </div>

      <div className="mb-12">
        {plants.map((plant) => (
          <div key={plant.name} className="mb-12">
            <div className="flex items-center gap-3 text-stone-900 text-2xl mb-6 p-4 bg-white rounded-xl shadow-sm border border-stone-200">
              <Factory size={24} />
              <span className="font-semibold">{plant.name}</span>
              {areas[plant.name] && (
                <span className="text-base font-normal text-stone-500">
                  ({areas[plant.name].length} areas)
                </span>
              )}
            </div>

            <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-6 mt-4">
              {(areas[plant.name] || []).map((area, index) => (
                <ExpandableEntityCard
                  key={area.id || area.name || index}
                  entity={{
                    ...area,
                    description: area.description || `Asset area ${area.name} - Click to explore sensors and equipment`
                  }}
                  entityType="AssetArea"
                  onNavigate={(entity, type, id) => handleAreaClick(entity)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {plants.length === 0 && (
        <div className="flex flex-col items-center p-16 text-stone-700 text-center">
          <Factory size={48} className="mb-4" />
          <h3 className="text-xl font-semibold mb-2">No plants found</h3>
          <p>No factory data available. Please check your graph database connection.</p>
        </div>
      )}
    </div>
  );
};

export default PlantOverview;