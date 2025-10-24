import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Activity, AlertCircle, Zap, Cpu, Thermometer, Gauge, BarChart3, Settings, Database, Play, Box } from 'lucide-react';
import { useNavigationContext } from '../../contexts/NavigationContext';
import Breadcrumb from '../../components/Breadcrumb';
import ExpandableEntityCard from '../../components/ExpandableEntityCard';
import WorkOrdersSection from '../../components/WorkOrdersSection';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';

// All components now use Tailwind and shadcn/ui - no styled-components needed

const getEntityIconBg = (type) => {
  switch(type) {
    case 'Equipment': return 'bg-orange-600'; // Orange for equipment
    case 'Sensor': return 'bg-emerald-700'; // Green for sensors
    case 'Equipment Sensors': return 'bg-emerald-600'; // Green for equipment sensors
    case 'Area Sensors': return 'bg-blue-600'; // Blue for area sensors
    case 'AssetArea': return 'bg-sky-500'; // Light blue for areas
    case 'Tank': return 'bg-cyan-600'; // Cyan for tanks
    case 'ProcessStep': return 'bg-green-600'; // Green for process steps
    default: return 'bg-stone-600'; // Grey default
  }
};

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
      <div className="flex justify-center items-center p-16 text-stone-700 text-lg">
        <Activity className="animate-spin mr-2" size={24} />
        Loading area details...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center p-16 text-stone-700 text-center">
        <AlertCircle className="mb-4" size={48} />
        <h2 className="text-xl font-semibold mb-2">Error Loading Area</h2>
        <p className="text-muted-foreground mb-4">{error}</p>
        <Button onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
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
    <div className="w-full">
      <Breadcrumb items={breadcrumbItems} />
      
      <div className="flex items-center gap-4 mb-8">
        <Button variant="outline" onClick={handleBack} className="gap-2">
          <ArrowLeft size={20} />
          Back to Overview
        </Button>
        <MapPin size={24} className="text-primary" />
        <h1 className="text-3xl font-bold text-stone-900 tracking-tight">
          {areaData?.name || decodeURIComponent(areaId)}
        </h1>
      </div>

      <div className="grid gap-6">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card className="bg-primary/10 border-primary/20">
            <CardContent className="pt-6 text-center">
              <div className="text-3xl font-bold text-primary mb-2">
                {stats.totalEntities || 0}
              </div>
              <div className="text-sm font-medium text-stone-700">
                Total Connected Entities
              </div>
            </CardContent>
          </Card>
          {Object.entries(stats).map(([key, value]) => {
            if (key === 'totalEntities') return null;
            return (
              <Card key={key} className="bg-primary/10 border-primary/20">
                <CardContent className="pt-6 text-center">
                  <div className="text-3xl font-bold text-primary mb-2">
                    {value}
                  </div>
                  <div className="text-sm font-medium text-stone-700">
                    {key}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Connected Entities */}
        {Object.entries(connectedEntities).map(([entityType, entities]) => {
          if (!entities || entities.length === 0) return null;
          
          return (
            <Card key={entityType}>
              <CardHeader className="border-b border-border">
                <div className="flex items-center gap-3">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-lg text-white ${getEntityIconBg(entityType)}`}>
                    {getEntityIcon(entityType)}
                  </div>
                  <CardTitle className="text-xl">
                    {entityType} 
                    <Badge variant="outline" className="ml-2">
                      {entities.length}
                    </Badge>
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {entities.map((entity, index) => (
                    <ExpandableEntityCard
                      key={entity.id || entity.properties?.tag || index}
                      entity={entity}
                      entityType={entityType}
                      onNavigate={handleEntityClick}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
        
        {Object.keys(connectedEntities).length === 0 && (
          <Card>
            <CardHeader className="border-b border-border">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 bg-primary rounded-lg text-white">
                  <Box />
                </div>
                <CardTitle>No Connected Entities</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <p className="text-muted-foreground text-center py-8">
                No connected entities found for this area.
              </p>
            </CardContent>
          </Card>
        )}
        
        {/* Work Orders Section */}
        <WorkOrdersSection 
          entityType="AssetArea" 
          entityName={areaData?.name || decodeURIComponent(areaId)}
          areaName={areaData?.name || decodeURIComponent(areaId)}
        />
      </div>
    </div>
  );
};

export default AreaDetail;