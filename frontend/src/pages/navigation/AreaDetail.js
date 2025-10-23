import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { ArrowLeft, MapPin, Activity, AlertCircle, Zap, Cpu, Thermometer, Gauge, BarChart3, Settings, Database, Play, Box } from 'lucide-react';
import { useNavigationContext } from '../../contexts/NavigationContext';
import Breadcrumb from '../../components/Breadcrumb';
import ExpandableEntityCard from '../../components/ExpandableEntityCard';
import WorkOrdersSection from '../../components/WorkOrdersSection';

const DetailContainer = styled.div`
  width: 100%;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
`;

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #ffffff;
  border: 1px solid #e7e5e4;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #1c1917;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: #f5f5f4;
    border-color: #047857;
    color: #047857;
  }
`;

const Title = styled.h1`
  font-size: 2rem;
  color: #1c1917;
  font-weight: 700;
  letter-spacing: -0.025em;
`;

const ContentContainer = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const Section = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
  border: 1px solid #e7e5e4;
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e7e5e4;
`;

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: #1c1917;
  margin: 0;
`;

const SectionIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #047857;
  border-radius: 8px;
  color: white;
`;

const EntitiesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
`;

// Styled components for EntityCard removed - now using ExpandableEntityCard component

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const StatCard = styled.div`
  background: rgba(4, 120, 87, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  border: 1px solid rgba(4, 120, 87, 0.2);
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: #047857;
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  color: #44403c;
  font-size: 0.9rem;
  font-weight: 500;
`;

const LoadingState = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4rem;
  color: #44403c;
  font-size: 1.1rem;
`;

const ErrorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem;
  color: #44403c;
  text-align: center;
`;

const AreaDetail = () => {
  const { areaId } = useParams();
  const navigate = useNavigate();
  const { setAreaContext } = useNavigationContext();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [areaData, setAreaData] = useState(null);
  const [connectedEntities, setConnectedEntities] = useState({});
  const [stats, setStats] = useState({});
  const [plantName, setPlantName] = useState(null);

  useEffect(() => {
    const fetchAreaDetail = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const areaName = decodeURIComponent(areaId);
        
        // Try to fetch from API first - using new graph API endpoints
        try {
          const [equipmentResponse, sensorsResponse] = await Promise.all([
            fetch(`/api/graph/areas/${encodeURIComponent(areaName)}/equipment`),
            fetch(`/api/graph/areas/${encodeURIComponent(areaName)}/sensors/categorized`)
          ]);

          if (equipmentResponse.ok && sensorsResponse.ok) {
            const equipmentData = await equipmentResponse.json();
            const sensorsData = await sensorsResponse.json();
            
            // Create area data from the response context
            const area = {
              name: areaName,
              description: `Industrial processing area ${areaName}`,
              type: 'AssetArea',
              properties: {
                area_code: areaName,
                status: 'Active'
              }
            };
            
            // Organize entities with categorized sensors
            const entities = {};
            
            // Add equipment if available
            if (equipmentData.equipment && equipmentData.equipment.length > 0) {
              entities.Equipment = equipmentData.equipment;
            }
            
            // Add categorized sensors
            const categorizedSensors = sensorsData.categorized_sensors;
            if (categorizedSensors.equipment_connected && categorizedSensors.equipment_connected.length > 0) {
              entities['Equipment Sensors'] = categorizedSensors.equipment_connected;
            }
            if (categorizedSensors.area_only && categorizedSensors.area_only.length > 0) {
              entities['Area Sensors'] = categorizedSensors.area_only;
            }
            
            setAreaData(area);
            setConnectedEntities(entities);
            
            // Extract plant name - try to infer from area code or set default
            const plantCode = areaName.split('-')[0]; // e.g., "40" from "40-10"
            const plant = plantCode === '40' ? 'S-Plant' : 'S-Plant'; // Default fallback
            setPlantName(plant);
            
            // Set navigation context for this area
            setAreaContext(areaName, area, plant);
            
            // Calculate stats
            const totalEntities = Object.values(entities).reduce((sum, arr) => sum + arr.length, 0);
            const entityCounts = Object.entries(entities).reduce((acc, [type, items]) => {
              acc[type] = items.length;
              return acc;
            }, {});
            
            setStats({
              totalEntities,
              ...entityCounts
            });
            return;
          }
        } catch (apiError) {
          console.log('API not available, using mock data');
        }
        
        // Fallback to mock data
        const mockData = {
          name: areaName,
          description: `Industrial processing area containing various equipment and monitoring systems for ${areaName} operations.`,
          type: 'Area',
          properties: {
            location: 'Plant Floor 2',
            status: 'Active',
            lastMaintenance: '2024-01-15'
          }
        };
        
        const mockEntities = {
          Equipment: [
            {
              id: 'eq_001',
              name: `${areaName} Primary Pump`,
              description: 'Main circulation pump for processing operations',
              properties: { status: 'Running', power: '85%' }
            },
            {
              id: 'eq_002', 
              name: `${areaName} Heat Exchanger`,
              description: 'Primary heat exchange unit',
              properties: { status: 'Active', efficiency: '92%' }
            }
          ],
          Sensor: [
            {
              id: 'sens_001',
              name: `${areaName} Temperature Sensor`,
              description: 'Monitors process temperature',
              properties: { value: '85.2°C', status: 'Normal' }
            },
            {
              id: 'sens_002',
              name: `${areaName} Pressure Sensor`, 
              description: 'Monitors system pressure',
              properties: { value: '2.4 bar', status: 'Normal' }
            },
            {
              id: 'sens_003',
              name: `${areaName} Flow Sensor`,
              description: 'Measures fluid flow rate',
              properties: { value: '150 L/min', status: 'Normal' }
            }
          ],
          ProcessStep: [
            {
              id: 'ps_001',
              name: `${areaName} Mixing Process`,
              description: 'Primary mixing operation',
              properties: { status: 'Running', progress: '65%' }
            }
          ]
        };
        
        setAreaData(mockData);
        setConnectedEntities(mockEntities);
        
        const totalEntities = Object.values(mockEntities).reduce((sum, arr) => sum + arr.length, 0);
        setStats({
          totalEntities,
          Equipment: mockEntities.Equipment.length,
          Sensor: mockEntities.Sensor.length,
          ProcessStep: mockEntities.ProcessStep.length
        });
        
      } catch (err) {
        console.error('Error fetching area details:', err);
        setError('Failed to load area details');
      } finally {
        setLoading(false);
      }
    };

    if (areaId) {
      fetchAreaDetail();
    }
  }, [areaId]);

  const getEntityIcon = (type) => {
    switch (type) {
      case 'Equipment': return <Settings />;
      case 'Equipment Sensors': return <Cpu />;
      case 'Area Sensors': return <Zap />;
      default: return <Box />;
    }
  };

  const handleEntityClick = (entity, type) => {
    console.log(`Clicked ${type}:`, entity);
    // Navigate to entity detail page
    // Try multiple possible identifiers from both top level and properties
    const entityId = entity.id || 
                     entity.name || 
                     entity.equipment_id || 
                     entity.tag ||
                     entity.properties?.equipment_id ||
                     entity.properties?.equipment_name ||
                     entity.properties?.tag ||
                     entity.properties?.name;
    
    if (entityId) {
      console.log(`Navigating to: /navigate/entity/${type}/${entityId}`);
      navigate(`/navigate/entity/${type}/${encodeURIComponent(entityId)}`);
    } else {
      console.warn('No valid ID found for entity:', entity);
    }
  };

  const handleBack = () => {
    navigate('/navigate');
  };

  if (loading) {
    return (
      <LoadingState>
        <Activity className="animate-spin" size={24} style={{ marginRight: '0.5rem' }} />
        Loading area details...
      </LoadingState>
    );
  }

  if (error) {
    return (
      <ErrorState>
        <h2>Error Loading Area</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()} style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Retry
        </button>
      </ErrorState>
    );
  }

  // Build breadcrumb items
  const breadcrumbItems = [];
  if (plantName) {
    breadcrumbItems.push({
      label: plantName,
      path: '/navigate',
      isActive: false
    });
  }
  breadcrumbItems.push({
    label: areaData?.name || decodeURIComponent(areaId),
    path: `/navigate/area/${areaId}`,
    isActive: true
  });

  return (
    <DetailContainer>
      <Breadcrumb items={breadcrumbItems} />
      
      <Header>
        <BackButton onClick={handleBack}>
          <ArrowLeft size={20} />
          Back to Overview
        </BackButton>
        <MapPin size={24} color="white" />
        <Title>{areaData?.name || decodeURIComponent(areaId)}</Title>
      </Header>

      <ContentContainer>
        {/* Stats Overview */}
        <StatsContainer>
          <StatCard>
            <StatValue>{stats.totalEntities || 0}</StatValue>
            <StatLabel>Total Connected Entities</StatLabel>
          </StatCard>
          {Object.entries(stats).map(([key, value]) => {
            if (key === 'totalEntities') return null;
            return (
              <StatCard key={key}>
                <StatValue>{value}</StatValue>
                <StatLabel>{key}</StatLabel>
              </StatCard>
            );
          })}
        </StatsContainer>

        {/* Connected Entities */}
        {Object.entries(connectedEntities).map(([entityType, entities]) => {
          if (!entities || entities.length === 0) return null;
          
          return (
            <Section key={entityType}>
              <SectionHeader>
                <SectionIcon>
                  {getEntityIcon(entityType)}
                </SectionIcon>
                <SectionTitle>{entityType} ({entities.length})</SectionTitle>
              </SectionHeader>
              
              <EntitiesGrid>
                {entities.map((entity, index) => (
                  <ExpandableEntityCard
                    key={entity.id || entity.properties?.tag || index}
                    entity={entity}
                    entityType={entityType}
                    onNavigate={handleEntityClick}
                  />
                ))}
              </EntitiesGrid>
            </Section>
          );
        })}
        
        {Object.keys(connectedEntities).length === 0 && (
          <Section>
            <SectionHeader>
              <SectionIcon>
                <Box />
              </SectionIcon>
              <SectionTitle>No Connected Entities</SectionTitle>
            </SectionHeader>
            <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
              No connected entities found for this area.
            </p>
          </Section>
        )}
        
        {/* Work Orders Section */}
        <WorkOrdersSection 
          entityType="AssetArea" 
          entityName={areaData?.name || decodeURIComponent(areaId)}
          areaName={areaData?.name || decodeURIComponent(areaId)}
        />
      </ContentContainer>
    </DetailContainer>
  );
};

export default AreaDetail;