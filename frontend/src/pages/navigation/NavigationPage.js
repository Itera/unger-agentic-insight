import React from 'react';
import { Routes, Route } from 'react-router-dom';
import styled from 'styled-components';
import PlantOverview from './PlantOverview';
import AreaDetail from './AreaDetail';
import EntityDetail from './EntityDetail';

const NavigationContainer = styled.div`
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
`;

const NavigationPage = () => {
  return (
    <NavigationContainer>
      <Routes>
        <Route path="/" element={<PlantOverview />} />
        <Route path="/area/:areaId" element={<AreaDetail />} />
        <Route path="/entity/:entityType/:entityId" element={<EntityDetail />} />
      </Routes>
    </NavigationContainer>
  );
};

export default NavigationPage;