import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { ArrowLeft, MapPin, Activity, AlertCircle, Zap, Cpu, Thermometer, Gauge, BarChart3, Settings, Database, Play, Box } from 'lucide-react';
import Breadcrumb from '../../components/Breadcrumb';

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
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: white;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const Title = styled.h1`
  font-size: 2rem;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
`;

const Subtitle = styled.p`
  color: #ccc;
  margin: 0.5rem 0 0 0;
  font-size: 0.9rem;
`;

const ContentContainer = styled.div`
  display: grid;
  gap: 1.5rem;
`;

const Section = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #f0f0f0;
`;

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
  margin: 0;
`;

const SectionIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
`;

const EntityDetailsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const DetailCard = styled.div`
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 1.5rem;
`;

const DetailTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 1rem 0;
`;

const DetailContent = styled.div`
  color: #666;
  line-height: 1.5;
`;

const PropertiesGrid = styled.div`
  display: grid;
  gap: 0.75rem;
`;

const PropertyRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
  
  &:last-child {
    border-bottom: none;
  }
`;

const PropertyKey = styled.span`
  font-weight: 500;
  color: #555;
`;

const PropertyValue = styled.span`
  color: #333;
  font-family: monospace;
  background: #f5f5f5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
`;

const EntitiesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
`;

const EntityCard = styled.div`
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    background: #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
`;

const EntityHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
`;

const EntityIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: white;
  background: ${props => {
    switch(props.type) {
      case 'Equipment': return 'linear-gradient(135deg, #ff6b6b, #ee5a24)';
      case 'Sensor': return 'linear-gradient(135deg, #4ecdc4, #44a08d)';
      case 'Tank': return 'linear-gradient(135deg, #45b7d1, #2980b9)';
      case 'ProcessStep': return 'linear-gradient(135deg, #96ceb4, #27ae60)';
      case 'AssetArea': return 'linear-gradient(135deg, #f093fb, #f5576c)';
      default: return 'linear-gradient(135deg, #667eea, #764ba2)';
    }
  }};
`;

const EntityName = styled.h3`
  font-size: 1rem;
  font-weight: 500;
  color: #333;
  margin: 0;
  flex: 1;
`;

const EntityDescription = styled.p`
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
  margin: 0;
`;

const EntityMeta = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
`;

const MetaTag = styled.span`
  background: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
`;

const RelationshipTag = styled.span`
  background: #d4edda;
  color: #155724;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const StatCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  color: #666;
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

const EntityDetail = () => {
  const { entityType, entityId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [entityData, setEntityData] = useState(null);
  const [connectedEntities, setConnectedEntities] = useState({});
  const [stats, setStats] = useState({});
  const [plantName, setPlantName] = useState(null);
  const [areaName, setAreaName] = useState(null);

  useEffect(() => {
    const fetchEntityDetail = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch entity details and connected entities
        const [entityResponse, connectedResponse] = await Promise.all([
          fetch(`/api/entities/${entityType}/${encodeURIComponent(entityId)}`),
          fetch(`/api/entities/${entityType}/${encodeURIComponent(entityId)}/connected`)
        ]);

        if (!entityResponse.ok || !connectedResponse.ok) {
          throw new Error('Failed to fetch entity data');
        }

        const entity = await entityResponse.json();
        const connected = await connectedResponse.json();
        
        setEntityData(entity);
        setConnectedEntities(connected);
        
        // Extract context from entity properties
        if (entity.properties?.plant_name) {
          setPlantName(entity.properties.plant_name);
        }
        if (entity.properties?.area_code) {
          setAreaName(entity.properties.area_code);
        }
        
        // Calculate stats
        const totalConnected = Object.values(connected).reduce((sum, arr) => sum + arr.length, 0);
        const entityCounts = Object.entries(connected).reduce((acc, [type, items]) => {
          acc[type] = items.length;
          return acc;
        }, {});
        
        setStats({
          totalConnected,
          ...entityCounts
        });
        
      } catch (err) {
        console.error('Error fetching entity details:', err);
        setError('Failed to load entity details');
      } finally {
        setLoading(false);
      }
    };

    if (entityType && entityId) {
      fetchEntityDetail();
    }
  }, [entityType, entityId]);

  const getEntityIcon = (type) => {
    switch (type) {
      case 'Equipment': return <Settings />;
      case 'Sensor': return <Activity />;
      case 'Tank': return <Database />;
      case 'ProcessStep': return <Play />;
      case 'AssetArea': return <MapPin />;
      default: return <Box />;
    }
  };

  const handleEntityClick = (entity, type) => {
    console.log(`Clicked ${type}:`, entity);
    // Navigate to the clicked entity's detail page  
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
    navigate(-1); // Go back to previous page
  };

  if (loading) {
    return (
      <LoadingState>
        <Activity className="animate-spin" size={24} style={{ marginRight: '0.5rem' }} />
        Loading entity details...
      </LoadingState>
    );
  }

  if (error) {
    return (
      <ErrorState>
        <h2>Error Loading Entity</h2>
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
  if (areaName) {
    breadcrumbItems.push({
      label: areaName,
      path: `/navigate/area/${encodeURIComponent(areaName)}`,
      isActive: false
    });
  }
  breadcrumbItems.push({
    label: entityData?.properties?.equipment_name || entityData?.properties?.tag || entityId,
    path: `/navigate/entity/${entityType}/${encodeURIComponent(entityId)}`,
    isActive: true
  });

  return (
    <DetailContainer>
      <Breadcrumb items={breadcrumbItems} />
      
      <Header>
        <BackButton onClick={handleBack}>
          <ArrowLeft size={20} />
          Back
        </BackButton>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', background: 'rgba(255,255,255,0.2)', borderRadius: '8px', color: 'white' }}>
            {getEntityIcon(entityType)}
          </div>
          <div>
            <Title>
              {entityData?.name || 
               entityData?.properties?.equipment_name ||
               entityData?.properties?.tag ||
               entityData?.properties?.name ||
               entityId}
            </Title>
            {entityData?.description && (
              <Subtitle>{entityData.description}</Subtitle>
            )}
          </div>
        </div>
      </Header>

      <ContentContainer>
        {/* Entity Details */}
        <EntityDetailsGrid>
          <DetailCard>
            <DetailTitle>Entity Information</DetailTitle>
            <DetailContent>
              <PropertiesGrid>
                <PropertyRow>
                  <PropertyKey>Type:</PropertyKey>
                  <PropertyValue>{entityType}</PropertyValue>
                </PropertyRow>
                {entityData?.labels && entityData.labels.length > 0 && (
                  <PropertyRow>
                    <PropertyKey>Labels:</PropertyKey>
                    <PropertyValue>{entityData.labels.join(', ')}</PropertyValue>
                  </PropertyRow>
                )}
                {entityData?.id && (
                  <PropertyRow>
                    <PropertyKey>ID:</PropertyKey>
                    <PropertyValue>{entityData.id}</PropertyValue>
                  </PropertyRow>
                )}
              </PropertiesGrid>
            </DetailContent>
          </DetailCard>
          
          {entityData?.properties && Object.keys(entityData.properties).length > 0 && (
            <DetailCard>
              <DetailTitle>Properties</DetailTitle>
              <DetailContent>
                <PropertiesGrid>
                  {Object.entries(entityData.properties).map(([key, value]) => (
                    <PropertyRow key={key}>
                      <PropertyKey>{key}:</PropertyKey>
                      <PropertyValue>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</PropertyValue>
                    </PropertyRow>
                  ))}
                </PropertiesGrid>
              </DetailContent>
            </DetailCard>
          )}
        </EntityDetailsGrid>

        {/* Connected Entities Stats */}
        {stats.totalConnected > 0 && (
          <StatsContainer>
            <StatCard>
              <StatValue>{stats.totalConnected || 0}</StatValue>
              <StatLabel>Total Connected Entities</StatLabel>
            </StatCard>
            {Object.entries(stats).map(([key, value]) => {
              if (key === 'totalConnected') return null;
              return (
                <StatCard key={key}>
                  <StatValue>{value}</StatValue>
                  <StatLabel>Connected {key}</StatLabel>
                </StatCard>
              );
            })}
          </StatsContainer>
        )}

        {/* Connected Entities */}
        {Object.entries(connectedEntities).map(([connectedType, entities]) => {
          if (!entities || entities.length === 0) return null;
          
          return (
            <Section key={connectedType}>
              <SectionHeader>
                <SectionIcon>
                  {getEntityIcon(connectedType)}
                </SectionIcon>
                <SectionTitle>Connected {connectedType} ({entities.length})</SectionTitle>
              </SectionHeader>
              
              <EntitiesGrid>
                {entities.map((entity, index) => {
                  const entityKey = entity.id || entity.name || `${connectedType}_${index}`;
                  return (
                    <EntityCard 
                      key={entityKey}
                      onClick={() => handleEntityClick(entity, connectedType)}
                    >
                      <EntityHeader>
                        <EntityIcon type={connectedType}>
                          {getEntityIcon(connectedType)}
                        </EntityIcon>
                        <EntityName>
                          {entity.name || 
                           entity.properties?.equipment_name || 
                           entity.properties?.tag || 
                           entity.properties?.name ||
                           entity.id || 
                           'Unknown'}
                        </EntityName>
                      </EntityHeader>
                      
                      {entity.description && (
                        <EntityDescription>{entity.description}</EntityDescription>
                      )}
                      
                      <EntityMeta>
                        {entity.relationship_type && (
                          <RelationshipTag>
                            {entity.relationship_type}
                          </RelationshipTag>
                        )}
                        {entity.properties && Object.entries(entity.properties).slice(0, 3).map(([key, value]) => (
                          <MetaTag key={key}>
                            {key}: {typeof value === 'object' ? 'Object' : String(value).slice(0, 20)}
                          </MetaTag>
                        ))}
                      </EntityMeta>
                    </EntityCard>
                  );
                })}
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
              No connected entities found for this {entityType.toLowerCase()}.
            </p>
          </Section>
        )}
      </ContentContainer>
    </DetailContainer>
  );
};

export default EntityDetail;