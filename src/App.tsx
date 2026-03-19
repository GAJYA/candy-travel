import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowLeft, MoreVertical } from 'lucide-react';
import { BottomNav } from './components/BottomNav';
import { HomeScreen } from './components/HomeScreen';
import { CalendarScreen } from './components/CalendarScreen';
import { AIScreen } from './components/AIScreen';
import { ProfileScreen } from './components/ProfileScreen';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');

  const renderScreen = () => {
    switch (activeTab) {
      case 'home':
        return <HomeScreen />;
      case 'calendar':
        return <CalendarScreen />;
      case 'ai':
        return <AIScreen />;
      case 'profile':
        return <ProfileScreen />;
      default:
        return <HomeScreen />;
    }
  };

  const getTitle = () => {
    switch (activeTab) {
      case 'home': return 'Candy Travel';
      case 'calendar': return '日历';
      case 'ai': return 'AI 助手';
      case 'profile': return '个人中心';
      default: return 'Candy Travel';
    }
  };

  return (
    <div className="min-h-screen bg-background text-zinc-900 selection:bg-primary-fixed">
      {/* Top App Bar */}
      <header className="fixed top-0 w-full z-50 bg-rose-50/80 backdrop-blur-md shadow-[0_4px_16px_rgba(224,64,160,0.15)] flex items-center justify-between px-6 h-16">
        <div className="flex items-center gap-4">
          <button className="bouncy-hover text-primary">
            <ArrowLeft size={24} />
          </button>
          <h1 className="font-sans font-bold text-lg tracking-tight text-primary">
            {getTitle()}
          </h1>
        </div>
        <div className="flex items-center gap-4">
          {activeTab === 'home' && (
            <span className="text-primary font-black italic hidden sm:inline">Candy Travel</span>
          )}
          <button className="bouncy-hover text-primary">
            <MoreVertical size={24} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-20 px-4 max-w-2xl mx-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.2 }}
          >
            {renderScreen()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Bottom Navigation */}
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}
