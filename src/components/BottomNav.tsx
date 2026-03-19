import React from 'react';
import { Home, Calendar, Sparkles, User } from 'lucide-react';
import { motion } from 'motion/react';

interface BottomNavProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'home', label: '首页', icon: Home },
    { id: 'calendar', label: '日历', icon: Calendar },
    { id: 'ai', label: 'AI 助手', icon: Sparkles },
    { id: 'profile', label: '个人中心', icon: User },
  ];

  return (
    <nav className="fixed bottom-0 left-0 w-full h-20 bg-white/90 backdrop-blur-lg border-t border-pink-100 flex justify-around items-center px-4 pb-safe z-50 rounded-t-[32px] shadow-[0_-8px_24px_rgba(224,64,160,0.1)]">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;

        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex flex-col items-center justify-center transition-all duration-300 relative ${
              isActive 
                ? 'bg-primary-fixed text-primary rounded-full px-5 py-2 scale-110' 
                : 'text-slate-400 px-4 py-2 hover:text-primary'
            }`}
          >
            <Icon size={isActive ? 24 : 20} strokeWidth={isActive ? 2.5 : 2} />
            <span className="font-sans font-medium text-[11px] mt-0.5">{tab.label}</span>
            {isActive && (
              <motion.div
                layoutId="nav-pill"
                className="absolute inset-0 bg-primary/10 rounded-full -z-10"
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}
          </button>
        );
      })}
    </nav>
  );
};
