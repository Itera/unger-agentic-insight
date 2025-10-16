import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import styled from 'styled-components';
import Navbar from './components/Navbar';
import ImportPage from './pages/ImportPage';
import QueryPage from './pages/QueryPage';
import NavigationPage from './pages/navigation/NavigationPage';

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Arial', sans-serif;
`;

const ContentContainer = styled.div`
  padding-top: 80px;
  min-height: calc(100vh - 80px);
`;

function App() {
  return (
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
  );
}

export default App;