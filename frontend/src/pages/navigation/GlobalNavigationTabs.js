import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Factory, Settings, Activity, MapPin, Database, Search, Filter, List } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ExpandableEntityCard from '../../components/ExpandableEntityCard';
import Breadcrumb from '../../components/Breadcrumb';

const NavigationContainer = styled.div`
  width: 100%;
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 2rem;
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
`;

const NavigationToggle = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
`;

const ToggleButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }
`;

const TabsContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 0.5rem;
  backdrop-filter: blur(10px);
`;

const Tab = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: ${props => props.active ? 'rgba(255, 255, 255, 0.2)' : 'transparent'};
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1.5rem;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: ${props => props.active ? '600' : '400'};

  &:hover {
    background: rgba(255, 255, 255, 0.15);
  }
`;

const ContentContainer = styled.div`
  min-height: 400px;
`;

const StatsBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  backdrop-filter: blur(10px);
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.25rem;
`;

const StatLabel = styled.div`
  color: #666;
  font-size: 0.9rem;
`;

const SearchContainer = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  align-items: center;
`;

const SearchInput = styled.input`
  flex: 1;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: none;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  font-size: 1rem;
  color: #333;
  backdrop-filter: blur(10px);
  
  &::placeholder {
    color: #999;
  }
  
  &:focus {
    outline: none;
    background: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`;

const SearchIcon = styled.div`
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
`;

const SearchWrapper = styled.div`
  position: relative;
  flex: 1;
`;

const FilterButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  color: #333;
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &:hover {
    background: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
`;

const EntitiesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
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

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
`;

const tabs = [
  { id: 'plants', label: 'Plants', icon: Factory, endpoint: null },
  { id: 'equipment', label: 'All Equipment', icon: Settings, endpoint: '/api/navigation/all-equipment' },
  { id: 'sensors', label: 'All Sensors', icon: Activity, endpoint: '/api/navigation/all-sensors' },
  { id: 'areas', label: 'All Areas', icon: MapPin, endpoint: '/api/navigation/all-areas' }
];

const GlobalNavigationTabs = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('plants');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({});

  useEffect(() => {
    if (activeTab !== 'plants') {
      loadTabData(activeTab);
    }
  }, [activeTab]);

  const loadTabData = async (tabId) => {
    const tab = tabs.find(t => t.id === tabId);
    if (!tab || !tab.endpoint) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(tab.endpoint);
      if (!response.ok) throw new Error(`Failed to load ${tab.label.toLowerCase()}`);
      
      const result = await response.json();
      setData(prev => ({ ...prev, [tabId]: result }));
      
      // Update stats
      setStats(prev => ({
        ...prev,
        [tabId]: {
          total: result.total_count,
          loaded: new Date().toLocaleTimeString()
        }
      }));
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEntityClick = (entity, entityType) => {
    // Determine the appropriate navigation path
    let path;
    
    if (entityType === 'AssetArea' || entityType === 'Area') {
      path = `/navigate/area/${encodeURIComponent(entity.name)}`;
    } else {
      // For equipment, sensors, etc., use the entity detail page
      const entityId = entity.id || entity.name || entity.properties?.equipment_name || entity.properties?.tag;
      if (entityId) {
        path = `/navigate/entity/${entityType}/${encodeURIComponent(entityId)}`;
      }
    }
    
    if (path) {
      navigate(path);
    }
  };

  const getFilteredData = () => {
    const currentData = data[activeTab];
    if (!currentData) return [];

    let items = [];
    switch (activeTab) {
      case 'equipment':
        items = currentData.equipment || [];
        break;
      case 'sensors':
        items = currentData.sensors || [];
        break;
      case 'areas':
        items = currentData.areas || [];
        break;
      default:
        return [];
    }

    if (!searchTerm) return items;

    return items.filter(item => 
      item.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.properties?.equipment_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.properties?.tag?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const renderContent = () => {
    if (activeTab === 'plants') {
      return (
        <EmptyState>
          <Factory size={64} style={{ marginBottom: '1rem' }} />
          <h3>Plant View</h3>
          <p>Plant hierarchical navigation is handled by the existing PlantOverview component.</p>
          <button 
            onClick={() => navigate('/navigate')}
            style={{
              marginTop: '1rem',
              padding: '0.75rem 1.5rem',
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            Go to Plant View
          </button>
        </EmptyState>
      );
    }

    if (loading) {
      return (
        <LoadingState>
          <Activity className="animate-spin" size={24} style={{ marginRight: '0.5rem' }} />
          Loading {tabs.find(t => t.id === activeTab)?.label.toLowerCase()}...
        </LoadingState>
      );
    }

    if (error) {
      return (
        <ErrorState>
          <h3>Error Loading Data</h3>
          <p>{error}</p>
          <button 
            onClick={() => loadTabData(activeTab)}
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

    const filteredItems = getFilteredData();
    
    if (filteredItems.length === 0) {
      return (
        <EmptyState>
          <Database size={64} style={{ marginBottom: '1rem' }} />
          <h3>No {tabs.find(t => t.id === activeTab)?.label} Found</h3>
          <p>No data available for the selected category.</p>
        </EmptyState>
      );
    }

    return (
      <EntitiesGrid>
        {filteredItems.map((item, index) => {
          // Create enhanced entity for display
          const enhancedEntity = {
            ...item,
            description: item.description || generateDescription(item, activeTab)
          };

          return (
              <ExpandableEntityCard
                key={item.id || item.name || index}
                entity={enhancedEntity}
                entityType={getEntityType(activeTab)}
                onNavigate={handleEntityClick}
              />
          );
        })}
      </EntitiesGrid>
    );
  };

  const generateDescription = (item, tabType) => {
    switch (tabType) {
      case 'equipment':
        const areaInfo = item.area_context ? ` in ${item.area_context.area_name}` : '';
        return `Industrial equipment${areaInfo}. Click to explore connected sensors and relationships.`;
      case 'sensors':
        const sensorContext = [];
        if (item.area_context) sensorContext.push(`Area: ${item.area_context.area_name}`);
        if (item.equipment_context && item.equipment_context.length > 0) {
          sensorContext.push(`Equipment: ${item.equipment_context.slice(0, 2).join(', ')}`);
        }
        const contextText = sensorContext.length > 0 ? ` - ${sensorContext.join(', ')}` : '';
        return `Sensor monitoring${contextText}. Click to view details and data.`;
      case 'areas':
        const counts = item.counts || {};
        const equipCount = counts.equipment || 0;
        const sensorCount = counts.sensors || 0;
        return `Asset area with ${equipCount} equipment and ${sensorCount} sensors. Click to explore.`;
      default:
        return 'Click to explore this entity and its relationships.';
    }
  };

  const getEntityType = (tabType) => {
    const typeMap = {
      'equipment': 'Equipment',
      'sensors': 'Sensor', 
      'areas': 'AssetArea'
    };
    return typeMap[tabType] || 'Entity';
  };

  return (
    <NavigationContainer>
      <Breadcrumb 
        items={[
          { label: 'Global Navigation', path: '/navigate/global', isActive: true }
        ]} 
      />
      
      <Header>
        <Title>Industrial Asset Navigation</Title>
        <Subtitle>
          Explore your entire industrial facility - from individual sensors to complete plant systems
        </Subtitle>
      </Header>

      <NavigationToggle>
        <ToggleButton onClick={() => navigate('/navigate')}>
          <List size={18} />
          Switch to Hierarchical View
          <span style={{ fontSize: '0.8rem', opacity: 0.8, marginLeft: '0.5rem' }}>
            (Plant → Area → Equipment structure)
          </span>
        </ToggleButton>
      </NavigationToggle>

      <TabsContainer>
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <Tab
              key={tab.id}
              active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={18} />
              {tab.label}
              {stats[tab.id] && (
                <span style={{ 
                  fontSize: '0.8rem', 
                  opacity: 0.8,
                  marginLeft: '0.5rem' 
                }}>
                  ({stats[tab.id].total})
                </span>
              )}
            </Tab>
          );
        })}
      </TabsContainer>

      {activeTab !== 'plants' && (
        <>
          {stats[activeTab] && (
            <StatsBar>
              <StatItem>
                <StatValue>{stats[activeTab].total || 0}</StatValue>
                <StatLabel>Total {tabs.find(t => t.id === activeTab)?.label}</StatLabel>
              </StatItem>
              <StatItem>
                <StatValue>{getFilteredData().length}</StatValue>
                <StatLabel>Displayed</StatLabel>
              </StatItem>
              <StatItem>
                <StatValue>{stats[activeTab].loaded || 'N/A'}</StatValue>
                <StatLabel>Last Updated</StatLabel>
              </StatItem>
            </StatsBar>
          )}

          <SearchContainer>
            <SearchWrapper>
              <SearchIcon>
                <Search size={18} />
              </SearchIcon>
              <SearchInput
                type="text"
                placeholder={`Search ${tabs.find(t => t.id === activeTab)?.label.toLowerCase()}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </SearchWrapper>
            <FilterButton>
              <Filter size={18} />
              Filter
            </FilterButton>
          </SearchContainer>
        </>
      )}

      <ContentContainer>
        {renderContent()}
      </ContentContainer>
    </NavigationContainer>
  );
};

export default GlobalNavigationTabs;