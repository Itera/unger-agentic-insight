import React, { createContext, useContext, useState, useCallback } from 'react';

// Create the navigation context
const NavigationContext = createContext();

// Custom hook to use navigation context
export const useNavigationContext = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigationContext must be used within a NavigationProvider');
  }
  return context;
};

// Navigation context provider component
export const NavigationProvider = ({ children }) => {
  const [currentContext, setCurrentContext] = useState({
    type: null,           // 'Plant', 'AssetArea', 'Equipment', 'Sensor'
    name: null,           // Current node name
    id: null,             // Current node ID
    plant: null,          // Current plant name
    area: null,           // Current area name
    equipment: null,      // Current equipment name (if applicable)
    breadcrumb: [],       // Full navigation path
    connectedEntities: null, // Connected entities data
    scopeDepth: 2         // How many hops to include in context (1-3)
  });

  const [chatMode, setChatMode] = useState('scoped'); // 'scoped' or 'global'

  // Update the current navigation context
  const updateContext = useCallback((contextData) => {
    setCurrentContext(prevContext => ({
      ...prevContext,
      ...contextData,
      // Update timestamp when context changes
      lastUpdated: new Date().toISOString()
    }));
  }, []);

  // Set context for plant level
  const setPlantContext = useCallback((plantName, plantData = null) => {
    updateContext({
      type: 'Plant',
      name: plantName,
      id: plantData?.id || plantName,
      plant: plantName,
      area: null,
      equipment: null,
      breadcrumb: [{ type: 'Plant', name: plantName, path: '/navigate' }],
      connectedEntities: plantData
    });
  }, [updateContext]);

  // Set context for area level
  const setAreaContext = useCallback((areaName, areaData = null, plantName = null) => {
    const plant = plantName || currentContext.plant || 'S-Plant';
    updateContext({
      type: 'AssetArea',
      name: areaName,
      id: areaData?.id || areaName,
      plant,
      area: areaName,
      equipment: null,
      breadcrumb: [
        { type: 'Plant', name: plant, path: '/navigate' },
        { type: 'AssetArea', name: areaName, path: `/navigate/area/${encodeURIComponent(areaName)}` }
      ],
      connectedEntities: areaData
    });
  }, [currentContext.plant, updateContext]);

  // Set context for equipment/sensor level
  const setEntityContext = useCallback((entityType, entityName, entityData = null, areaName = null, plantName = null) => {
    const plant = plantName || currentContext.plant || 'S-Plant';
    const area = areaName || currentContext.area;
    
    const breadcrumb = [
      { type: 'Plant', name: plant, path: '/navigate' }
    ];
    
    if (area) {
      breadcrumb.push({ type: 'AssetArea', name: area, path: `/navigate/area/${encodeURIComponent(area)}` });
    }
    
    breadcrumb.push({ 
      type: entityType, 
      name: entityName, 
      path: `/navigate/entity/${entityType}/${encodeURIComponent(entityName)}` 
    });

    updateContext({
      type: entityType,
      name: entityName,
      id: entityData?.id || entityName,
      plant,
      area,
      equipment: entityType === 'Equipment' ? entityName : currentContext.equipment,
      breadcrumb,
      connectedEntities: entityData
    });
  }, [currentContext.plant, currentContext.area, currentContext.equipment, updateContext]);

  // Clear context (return to global view)
  const clearContext = useCallback(() => {
    updateContext({
      type: null,
      name: null,
      id: null,
      plant: null,
      area: null,
      equipment: null,
      breadcrumb: [],
      connectedEntities: null
    });
  }, [updateContext]);

  // Get context for AI chat
  const getChatContext = useCallback(() => {
    if (chatMode === 'global' || !currentContext.type) {
      return null; // Global mode or no context
    }

    return {
      nodeType: currentContext.type,
      nodeName: currentContext.name,
      nodeId: currentContext.id,
      plant: currentContext.plant,
      area: currentContext.area,
      equipment: currentContext.equipment,
      scopeDepth: currentContext.scopeDepth,
      breadcrumb: currentContext.breadcrumb,
      mode: chatMode
    };
  }, [currentContext, chatMode]);

  // Toggle between scoped and global chat modes
  const toggleChatMode = useCallback(() => {
    setChatMode(prevMode => prevMode === 'scoped' ? 'global' : 'scoped');
  }, []);

  // Set scope depth for context queries
  const setScopeDepth = useCallback((depth) => {
    if (depth >= 1 && depth <= 3) {
      updateContext({ scopeDepth: depth });
    }
  }, [updateContext]);

  // Check if we have an active context
  const hasActiveContext = currentContext.type !== null;

  // Get context summary for display
  const getContextSummary = useCallback(() => {
    if (!hasActiveContext) return 'Global View';
    
    const parts = [];
    if (currentContext.plant) parts.push(currentContext.plant);
    if (currentContext.area) parts.push(currentContext.area);
    if (currentContext.name && currentContext.type !== 'Plant' && currentContext.type !== 'AssetArea') {
      parts.push(`${currentContext.type}: ${currentContext.name}`);
    } else if (currentContext.name && currentContext.type === 'AssetArea') {
      // Already included area name above
    }
    
    return parts.join(' > ') || 'Unknown Context';
  }, [currentContext, hasActiveContext]);

  const contextValue = {
    // Current context state
    currentContext,
    chatMode,
    hasActiveContext,
    
    // Context setters
    setPlantContext,
    setAreaContext,
    setEntityContext,
    clearContext,
    updateContext,
    
    // Chat-related methods
    getChatContext,
    toggleChatMode,
    setChatMode,
    setScopeDepth,
    
    // Utility methods
    getContextSummary
  };

  return (
    <NavigationContext.Provider value={contextValue}>
      {children}
    </NavigationContext.Provider>
  );
};

export default NavigationContext;