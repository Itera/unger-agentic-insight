import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import styled from 'styled-components';
import { NavigationProvider } from './contexts/NavigationContext';
import Navbar from './components/Navbar';
import ImportPage from './pages/ImportPage';
import QueryPage from './pages/QueryPage';
import NavigationPage from './pages/navigation/NavigationPage';

const AppContainer = styled.div`
  min-height: 100vh;
  background: #fafaf9;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
`;

const ContentContainer = styled.div`
  padding-top: 80px;
  min-height: calc(100vh - 80px);
`;

function App() {
  return (
    <NavigationProvider>
      <AppContainer>
        <Router>
          <Navbar />
          <ContentContainer>
            <Routes>
              <Route path="/" element={<Navigate to="/navigate" replace />} />
              <Route path="/import" element={<ImportPage />} />
              <Route path="/query" element={<QueryPage />} />
              <Route path="/navigate/*" element={<NavigationPage />} />
            </Routes>
          </ContentContainer>
        </Router>
      </AppContainer>
    </NavigationProvider>
  );
}

export default App;