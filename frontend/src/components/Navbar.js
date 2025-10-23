import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { Upload, Search, Database, Network } from 'lucide-react';

const NavContainer = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: #292524;
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  border-bottom: 1px solid rgba(4, 120, 87, 0.2);
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.025em;
`;

const NavLinks = styled.div`
  display: flex;
  gap: 2rem;
`;

const NavLink = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  text-decoration: none;
  color: ${props => props.active ? '#ffffff' : '#d6d3d1'};
  background: ${props => props.active ? '#047857' : 'transparent'};
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;

  &:hover {
    background: ${props => props.active ? '#065f46' : 'rgba(4, 120, 87, 0.15)'};
    color: ${props => props.active ? '#ffffff' : '#10b981'};
    transform: translateY(-1px);
  }
`;

const Navbar = () => {
  const location = useLocation();

  return (
    <NavContainer>
      <Logo>
        <Database size={24} />
        Agentic Insight
      </Logo>
      <NavLinks>
        <NavLink 
          to="/import" 
          active={location.pathname === '/import' ? 1 : 0}
        >
          <Upload size={18} />
          Import Data
        </NavLink>
        <NavLink 
          to="/query" 
          active={location.pathname === '/query' ? 1 : 0}
        >
          <Search size={18} />
          Query Data
        </NavLink>
        <NavLink 
          to="/navigate" 
          active={location.pathname.startsWith('/navigate') ? 1 : 0}
        >
          <Network size={18} />
          Navigate
        </NavLink>
      </NavLinks>
    </NavContainer>
  );
};

export default Navbar;