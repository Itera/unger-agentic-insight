import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { Factory, MapPin, Activity, AlertCircle, ChevronRight } from 'lucide-react';
import { useNavigationContext } from '../../contexts/NavigationContext';
import Breadcrumb from '../../components/Breadcrumb';
import ExpandableEntityCard from '../../components/ExpandableEntityCard';

const OverviewContainer = styled.div`
  width: 100%;
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 3rem;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  color: white;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
`;

const Subtitle = styled.p`
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.1rem;
  margin-bottom: 2rem;
`;

const PlantsContainer = styled.div`
  margin-bottom: 3rem;
`;

const PlantSection = styled.div`
  margin-bottom: 3rem;
`;

const PlantTitle = styled.h2`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
`;

const AreasGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
`;

const AreaCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
    background: rgba(255, 255, 255, 1);
  }

  &:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
`;

const AreaHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: flex-start;
  margin-bottom: 1rem;
`;

const AreaTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
  flex: 1;
`;

const AreaIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  color: white;
  margin-left: 1rem;
`;

const AreaStats = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
`;

const StatItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  font-size: 0.9rem;
`;

const AreaDescription = styled.p`
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 1rem;
`;

const ActionButton = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #667eea;
  font-weight: 500;
  font-size: 0.9rem;
`;

const LoadingState = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4rem;
  color: white;
  font-size: 1.1rem;
`;

const ErrorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem;
  color: white;
  text-align: center;
`;

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
      <LoadingState>
        <Activity className="animate-spin" size={24} style={{ marginRight: '0.5rem' }} />
        Loading factory data...
      </LoadingState>
    );
  }

  if (error) {
    return (
      <ErrorState>
        <AlertCircle size={48} style={{ marginBottom: '1rem' }} />
        <h3>Failed to load factory data</h3>
        <p>{error}</p>
        <button 
          onClick={loadPlantsAndAreas}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            background: 'rgba(255,255,255,0.2)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </ErrorState>
    );
  }

  return (
    <OverviewContainer>
      <Breadcrumb 
        items={[
          { label: 'Plants', path: '/navigate', isActive: true }
        ]} 
      />
      
      <Header>
        <Title>Factory Navigation</Title>
        <Subtitle>
          Explore your industrial assets through an interactive plant and area overview
        </Subtitle>
      </Header>

      <PlantsContainer>
        {plants.map((plant) => (
          <PlantSection key={plant.name}>
            <PlantTitle>
              <Factory size={24} />
              {plant.name}
              {areas[plant.name] && (
                <span style={{ fontSize: '0.9rem', fontWeight: 'normal', color: 'rgba(255,255,255,0.8)' }}>
                  ({areas[plant.name].length} areas)
                </span>
              )}
            </PlantTitle>

            <AreasGrid>
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
            </AreasGrid>
          </PlantSection>
        ))}
      </PlantsContainer>

      {plants.length === 0 && (
        <ErrorState>
          <Factory size={48} style={{ marginBottom: '1rem' }} />
          <h3>No plants found</h3>
          <p>No factory data available. Please check your graph database connection.</p>
        </ErrorState>
      )}
    </OverviewContainer>
  );
};

export default PlantOverview;