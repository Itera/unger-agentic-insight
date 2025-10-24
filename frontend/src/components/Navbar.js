import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Upload, Search, Database, Network } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/navigate') {
      return location.pathname.startsWith('/navigate');
    }
    return location.pathname === path;
  };

  return (
    <nav className="fixed top-0 left-0 right-0 bg-stone-800 backdrop-blur-md px-8 py-4 flex justify-between items-center shadow-lg z-[1000] border-b border-emerald-700/20">
      <div className="flex items-center gap-2 text-2xl font-bold text-white tracking-tight">
        <Database size={24} />
        Agentic Insight
      </div>
      <div className="flex gap-8">
        <Link 
          to="/import" 
          className={`flex items-center gap-2 px-6 py-3 rounded-lg no-underline font-semibold transition-all ${
            isActive('/import')
              ? 'text-white bg-emerald-700 hover:bg-emerald-800'
              : 'text-stone-300 bg-transparent hover:bg-emerald-700/15 hover:text-emerald-500 hover:-translate-y-0.5'
          }`}
        >
          <Upload size={18} />
          Import Data
        </Link>
        <Link 
          to="/query" 
          className={`flex items-center gap-2 px-6 py-3 rounded-lg no-underline font-semibold transition-all ${
            isActive('/query')
              ? 'text-white bg-emerald-700 hover:bg-emerald-800'
              : 'text-stone-300 bg-transparent hover:bg-emerald-700/15 hover:text-emerald-500 hover:-translate-y-0.5'
          }`}
        >
          <Search size={18} />
          Query Data
        </Link>
        <Link 
          to="/navigate" 
          className={`flex items-center gap-2 px-6 py-3 rounded-lg no-underline font-semibold transition-all ${
            isActive('/navigate')
              ? 'text-white bg-emerald-700 hover:bg-emerald-800'
              : 'text-stone-300 bg-transparent hover:bg-emerald-700/15 hover:text-emerald-500 hover:-translate-y-0.5'
          }`}
        >
          <Network size={18} />
          Navigate
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;
