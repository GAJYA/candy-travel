import React from 'react';
import { Plane, Train, Map, ChevronRight, Plus } from 'lucide-react';
import { motion } from 'motion/react';

export const HomeScreen: React.FC = () => {
  return (
    <div className="space-y-6 pb-24">
      {/* Countdown Widget */}
      <section className="relative overflow-hidden rounded-3xl bg-primary text-white p-6 candy-shadow-primary group">
        <div className="absolute -right-8 -top-8 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
        <div className="absolute -left-4 -bottom-4 w-24 h-24 bg-secondary/20 rounded-full blur-xl"></div>
        
        <div className="relative z-10 flex flex-col items-center">
          <span className="text-xs font-bold uppercase tracking-widest opacity-80 mb-2">下一次冒险开始于</span>
          <div className="flex gap-4 items-center">
            <div className="flex flex-col items-center">
              <span className="text-4xl font-black">12</span>
              <span className="text-[10px] font-medium opacity-90">天</span>
            </div>
            <span className="text-2xl font-light opacity-40">:</span>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-black">08</span>
              <span className="text-[10px] font-medium opacity-90">时</span>
            </div>
            <span className="text-2xl font-light opacity-40">:</span>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-black">45</span>
              <span className="text-[10px] font-medium opacity-90">分</span>
            </div>
          </div>
          <button className="mt-4 px-6 py-2 bg-white/20 rounded-full flex items-center gap-2 backdrop-blur-sm hover:bg-white/30 transition-all bouncy-hover">
            <Plane size={14} />
            <span className="text-sm font-bold">前往 日本东京</span>
          </button>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="grid grid-cols-2 gap-4">
        <div className="col-span-2 bg-white rounded-2xl p-5 shadow-[0_4px_16px_rgba(124,82,170,0.1)] border border-pink-50 flex items-center justify-between">
          <div>
            <p className="text-outline text-sm font-medium">2024 年度旅程</p>
            <p className="text-2xl font-black text-secondary">缤纷世界</p>
          </div>
          <div className="w-12 h-12 rounded-full bg-secondary-container flex items-center justify-center text-secondary">
            <Sparkles size={24} />
          </div>
        </div>
        
        <div className="bg-primary-fixed/30 rounded-2xl p-4 flex flex-col items-center text-center border border-pink-100 bouncy-hover">
          <span className="text-3xl font-black text-primary">14</span>
          <span className="text-xs font-bold text-outline uppercase mt-1">计划城市</span>
        </div>
        
        <div className="bg-tertiary-fixed/30 rounded-2xl p-4 flex flex-col items-center text-center border border-pink-100 bouncy-hover">
          <span className="text-3xl font-black text-tertiary">08</span>
          <span className="text-xs font-bold text-outline uppercase mt-1">旅行次数</span>
        </div>

        <div className="col-span-2 bg-tertiary text-white rounded-2xl p-5 candy-shadow-tertiary flex items-center justify-between overflow-hidden relative">
          <div className="absolute -right-4 -bottom-4 opacity-10">
            <Map size={96} />
          </div>
          <div>
            <p className="text-xs font-bold opacity-80 uppercase tracking-tighter">行程距离</p>
            <p className="text-3xl font-black">24,530 <span className="text-sm font-medium">km</span></p>
          </div>
          <div className="flex -space-x-2">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-md border border-white/30">
              <Plane size={16} />
            </div>
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-md border border-white/30">
              <Train size={16} />
            </div>
          </div>
        </div>
      </section>

      {/* Footprint Map Placeholder */}
      <section className="bg-white rounded-2xl shadow-[0_4px_16px_rgba(224,64,160,0.1)] overflow-hidden border border-pink-50">
        <div className="p-4 flex items-center justify-between border-b border-pink-50">
          <h2 className="font-bold text-secondary flex items-center gap-2">
            <Map size={18} className="text-primary" />
            我的足迹
          </h2>
          <span className="text-[10px] font-black bg-primary-fixed text-primary px-3 py-1 rounded-full uppercase">全球视图</span>
        </div>
        <div className="h-48 w-full bg-slate-50 relative overflow-hidden flex items-center justify-center">
          <img 
            src="https://picsum.photos/seed/travel-map/600/300" 
            alt="Map" 
            className="w-full h-full object-cover opacity-40"
            referrerPolicy="no-referrer"
          />
          <div className="absolute inset-0 flex items-center justify-center">
             <div className="relative w-full h-full">
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 200">
                  <path d="M50,100 Q200,20 350,100" fill="none" stroke="#e040a0" strokeDasharray="4,4" strokeWidth="2" />
                  <circle cx="50" cy="100" fill="#e040a0" r="4" />
                  <circle cx="350" cy="100" fill="#e040a0" r="4" />
                </svg>
             </div>
          </div>
          <div className="absolute bottom-4 left-4 bg-white/70 backdrop-blur-md px-3 py-2 rounded-xl flex items-center gap-3 shadow-sm border border-white/50">
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-primary"></span>
              <span className="text-[10px] font-bold">当前</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-secondary"></span>
              <span className="text-[10px] font-bold">已计划</span>
            </div>
          </div>
        </div>
      </section>

      {/* Upcoming Trips */}
      <section className="space-y-4">
        <h2 className="font-black text-lg text-zinc-900 px-2">即将到来的行程</h2>
        <div className="space-y-3">
          {[
            { city: '日本京都', date: '2024年11月24日 - 11月28日', status: '已确认', color: 'secondary', icon: Train },
            { city: '韩国首尔', date: '2024年12月15日 - 12月22日', status: '计划中', color: 'primary', icon: Plane },
          ].map((trip, i) => (
            <motion.div 
              key={i}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              className="bg-white rounded-2xl p-4 flex items-center gap-4 shadow-[0_4px_16px_rgba(0,0,0,0.05)] border border-pink-50 cursor-pointer group"
            >
              <div className={`w-14 h-14 rounded-xl bg-${trip.color}-fixed flex items-center justify-center text-${trip.color} group-hover:bg-${trip.color} group-hover:text-white transition-colors duration-300`}>
                <trip.icon size={24} />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-zinc-900">{trip.city}</h3>
                <p className="text-xs text-outline">{trip.date}</p>
              </div>
              <div className="text-right">
                <span className={`block text-[10px] font-black ${trip.status === '已确认' ? 'text-tertiary bg-tertiary-fixed' : 'text-secondary bg-secondary-fixed'} px-2 py-0.5 rounded-full mb-1`}>
                  {trip.status}
                </span>
                <ChevronRight size={16} className="text-pink-200 group-hover:text-primary transition-colors ml-auto" />
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* FAB */}
      <button className="fixed right-6 bottom-24 w-14 h-14 rounded-full bg-primary text-white shadow-[0_8px_24px_rgba(224,64,160,0.4)] flex items-center justify-center bouncy-hover z-40">
        <Plus size={30} />
      </button>
    </div>
  );
};

interface SparklesProps {
  size?: number;
}
const Sparkles: React.FC<SparklesProps> = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
    <path d="M5 3v4"/><path d="M3 5h4"/><path d="M21 17v4"/><path d="M19 19h4"/>
  </svg>
);
