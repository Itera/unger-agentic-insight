import React, { useState } from 'react';
import styled from 'styled-components';
import { ChevronDown, ChevronUp, Settings, Activity, Cpu, Zap, Database, Play, Box, Info, Tag, Calendar, AlertCircle, MapPin } from 'lucide-react';

const CardContainer = styled.div`
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

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: between;
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
  flex-shrink: 0;
  background: ${props => {
    switch(props.type) {
      case 'Equipment': return 'linear-gradient(135deg, #ff6b6b, #ee5a24)';
      case 'Sensor': return 'linear-gradient(135deg, #4ecdc4, #44a08d)';
      case 'Equipment Sensors': return 'linear-gradient(135deg, #fd79a8, #e84393)';
      case 'Area Sensors': return 'linear-gradient(135deg, #fdcb6e, #e17055)';
      case 'AssetArea': return 'linear-gradient(135deg, #a29bfe, #6c5ce7)'; // Purple gradient for asset areas
      case 'Tank': return 'linear-gradient(135deg, #45b7d1, #2980b9)';
      case 'ProcessStep': return 'linear-gradient(135deg, #96ceb4, #27ae60)';
      default: return 'linear-gradient(135deg, #667eea, #764ba2)';
    }
  }};
`;

const EntityInfo = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const EntityName = styled.h3`
  font-size: 1rem;
  font-weight: 500;
  color: #333;
  margin: 0;
  line-height: 1.3;
`;

const EntityDescription = styled.p`
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
  margin: 0;
`;

const ExpandButton = styled.button`
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(0, 0, 0, 0.05);
    color: #333;
  }
`;

const ExpandedContent = styled.div`
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
  animation: ${props => props.isExpanded ? 'expandIn' : 'expandOut'} 0.3s ease;
  
  @keyframes expandIn {
    from {
      opacity: 0;
      max-height: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      max-height: 500px;
      transform: translateY(0);
    }
  }
  
  @keyframes expandOut {
    from {
      opacity: 1;
      max-height: 500px;
      transform: translateY(0);
    }
    to {
      opacity: 0;
      max-height: 0;
      transform: translateY(-10px);
    }
  }
`;

const DetailSection = styled.div`
  margin-bottom: 1rem;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const DetailSectionTitle = styled.h4`
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const PropertyGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
`;

const PropertyItem = styled.div`
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  padding: 0.5rem;
  border-radius: 6px;
`;

const PropertyLabel = styled.span`
  font-size: 0.8rem;
  color: #666;
  font-weight: 500;
  text-transform: capitalize;
`;

const PropertyValue = styled.span`
  font-size: 0.9rem;
  color: #333;
  word-break: break-word;
`;

const MetaTagsContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
`;

const MetaTag = styled.span`
  background: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const ActionButton = styled.button`
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const ExpandableEntityCard = ({ entity, entityType, onNavigate }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getEntityIcon = (type) => {
    switch (type) {
      case 'Equipment': return <Settings size={16} />;
      case 'Sensor': return <Activity size={16} />;
      case 'Equipment Sensors': return <Cpu size={16} />;
      case 'Area Sensors': return <Zap size={16} />;
      case 'AssetArea': return <MapPin size={16} />;
      case 'Tank': return <Database size={16} />;
      case 'ProcessStep': return <Play size={16} />;
      default: return <Box size={16} />;
    }
  };

  const getEntityName = (entity) => {
    return entity.name || 
           entity.properties?.equipment_name || 
           entity.properties?.tag || 
           entity.properties?.name ||
           entity.description ||
           entity.id || 
           'Unknown';
  };

  const getEntityDescription = (entity) => {
    let description = entity.description || entity.properties?.description;
    
    // Add unit information for sensors
    if (entityType === 'Sensor' && entity.properties?.unit) {
      description = `${description || 'Sensor'} (${entity.properties.unit})`;
    }
    
    // Add equipment type for equipment
    if (entityType === 'Equipment' && entity.properties?.equipment_type) {
      description = `${description || 'Equipment'} - ${entity.properties.equipment_type}`;
    }
    
    return description || `${entityType} entity`;
  };

  const formatPropertyValue = (value) => {
    if (typeof value === 'object' && value !== null) {
      // Handle Neo4j DateTime objects
      if (value._DateTime__date) {
        const date = value._DateTime__date;
        const time = value._DateTime__time;
        return `${date._Date__year}-${String(date._Date__month).padStart(2, '0')}-${String(date._Date__day).padStart(2, '0')} ${String(time._Time__hour).padStart(2, '0')}:${String(time._Time__minute).padStart(2, '0')}`;
      }
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const handleCardClick = (e) => {
    e.preventDefault();
    setIsExpanded(!isExpanded);
  };

  const handleNavigateClick = (e) => {
    e.stopPropagation();
    if (onNavigate) {
      const entityId = entity.id || 
                       entity.name || 
                       entity.equipment_id || 
                       entity.tag ||
                       entity.properties?.equipment_id ||
                       entity.properties?.equipment_name ||
                       entity.properties?.tag ||
                       entity.properties?.name;
      
      if (entityId) {
        onNavigate(entity, entityType, entityId);
      }
    }
  };

  return (
    <CardContainer onClick={handleCardClick}>
      <CardHeader>
        <EntityIcon type={entityType}>
          {getEntityIcon(entityType)}
        </EntityIcon>
        <EntityInfo>
          <EntityName>{getEntityName(entity)}</EntityName>
          <EntityDescription>{getEntityDescription(entity)}</EntityDescription>
        </EntityInfo>
        <ExpandButton onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }}>
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </ExpandButton>
      </CardHeader>
      
      {isExpanded && (
        <ExpandedContent isExpanded={isExpanded}>
          {/* Key Information for Sensors and Equipment */}
          {(entityType === 'Sensor' || entityType === 'Equipment') && entity.properties && (
            <DetailSection>
              <DetailSectionTitle>
                <Activity size={14} />
                Key Information
              </DetailSectionTitle>
              <PropertyGrid>
                {/* Sensor-specific key info */}
                {entityType === 'Sensor' && (
                  <>
                    {entity.properties.unit && (
                      <PropertyItem>
                        <PropertyLabel>Unit</PropertyLabel>
                        <PropertyValue style={{fontWeight: 600, color: '#2563eb'}}>{entity.properties.unit}</PropertyValue>
                      </PropertyItem>
                    )}
                    {entity.properties.sensor_type_code && (
                      <PropertyItem>
                        <PropertyLabel>Type</PropertyLabel>
                        <PropertyValue>{entity.properties.sensor_type_code}</PropertyValue>
                      </PropertyItem>
                    )}
                    {entity.properties.classification && (
                      <PropertyItem>
                        <PropertyLabel>Classification</PropertyLabel>
                        <PropertyValue>{entity.properties.classification}</PropertyValue>
                      </PropertyItem>
                    )}
                  </>
                )}
                {/* Equipment-specific key info */}
                {entityType === 'Equipment' && (
                  <>
                    {entity.properties.equipment_type && (
                      <PropertyItem>
                        <PropertyLabel>Equipment Type</PropertyLabel>
                        <PropertyValue style={{fontWeight: 600, color: '#dc2626'}}>{entity.properties.equipment_type}</PropertyValue>
                      </PropertyItem>
                    )}
                    {entity.properties.sensor_count && (
                      <PropertyItem>
                        <PropertyLabel>Sensor Count</PropertyLabel>
                        <PropertyValue style={{fontWeight: 600, color: '#059669'}}>{entity.properties.sensor_count}</PropertyValue>
                      </PropertyItem>
                    )}
                  </>
                )}
              </PropertyGrid>
              {/* Source tags for equipment */}
              {entityType === 'Equipment' && entity.properties.source_tags && (
                <div style={{marginTop: '0.75rem'}}>
                  <PropertyLabel>Source Tags</PropertyLabel>
                  <div style={{marginTop: '0.25rem'}}>
                    {entity.properties.source_tags.split(',').map((tag, index) => (
                      <MetaTag key={index} style={{marginRight: '0.5rem', marginBottom: '0.25rem'}}>
                        {tag.trim()}
                      </MetaTag>
                    ))}
                  </div>
                </div>
              )}
            </DetailSection>
          )}
          
          {/* All Entity Properties */}
          {entity.properties && Object.keys(entity.properties).length > 0 && (
            <DetailSection>
              <DetailSectionTitle>
                <Tag size={14} />
                All Properties
              </DetailSectionTitle>
              <PropertyGrid>
                {Object.entries(entity.properties).map(([key, value]) => (
                  <PropertyItem key={key}>
                    <PropertyLabel>{key.replace(/_/g, ' ')}</PropertyLabel>
                    <PropertyValue>{formatPropertyValue(value)}</PropertyValue>
                  </PropertyItem>
                ))}
              </PropertyGrid>
            </DetailSection>
          )}

          {/* Entity Labels */}
          {entity.labels && entity.labels.length > 0 && (
            <DetailSection>
              <DetailSectionTitle>
                <AlertCircle size={14} />
                Labels
              </DetailSectionTitle>
              <MetaTagsContainer>
                {entity.labels.map((label, index) => (
                  <MetaTag key={index}>{label}</MetaTag>
                ))}
              </MetaTagsContainer>
            </DetailSection>
          )}

          {/* Actions */}
          <ActionButtons>
            <ActionButton onClick={handleNavigateClick}>
              View Details
            </ActionButton>
          </ActionButtons>
        </ExpandedContent>
      )}
    </CardContainer>
  );
};

export default ExpandableEntityCard;