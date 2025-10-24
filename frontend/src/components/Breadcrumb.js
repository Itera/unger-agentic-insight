import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const Breadcrumb = ({ items = [] }) => {
  const navigate = useNavigate();

  const handleItemClick = (item) => {
    if (item.path && !item.isActive) {
      navigate(item.path);
    }
  };

  // Always start with home
  const allItems = [
    {
      label: 'Plants',
      path: '/navigate',
      icon: <Home className="w-4 h-4 mr-1" />,
      isActive: false
    },
    ...items
  ];

  return (
    <div className="flex items-center gap-2 py-4 mb-4 text-sm">
      {allItems.map((item, index) => (
        <React.Fragment key={index}>
          <button
            className={`flex items-center gap-1 bg-transparent border-none px-3 py-2 rounded-md transition-all no-underline text-sm ${
              item.isActive 
                ? 'text-stone-900 cursor-default font-semibold' 
                : 'text-stone-600 cursor-pointer hover:bg-stone-100 hover:text-stone-900'
            }`}
            disabled={item.isActive}
            onClick={() => handleItemClick(item)}
          >
            {item.icon}
            {item.label}
          </button>
          
          {index < allItems.length - 1 && <ChevronRight className="text-stone-400 w-4 h-4" />}
        </React.Fragment>
      ))}
    </div>
  );
};

export default Breadcrumb;
