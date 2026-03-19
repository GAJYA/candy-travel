import React from 'react';
import { MapPin, Plane, Train, Bus, Car, Clock, Timer, Bed, ListChecks, Edit3, Save, Camera, Smartphone, BookOpen, Coffee, Pill } from 'lucide-react';
import { motion } from 'motion/react';

export const ProfileScreen: React.FC = () => {
  return (
    <div className="space-y-6 pb-24">
      {/* Hero Input: Destination */}
      <section className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary to-secondary rounded-2xl blur opacity-10 group-hover:opacity-20 transition duration-1000"></div>
        <div className="relative bg-white rounded-2xl p-6 shadow-[0_8px_32px_rgba(224,64,160,0.08)]">
          <label className="block text-primary font-bold text-sm mb-2 px-1">下一站去哪？</label>
          <div className="flex items-center gap-3 bg-surface-variant/50 rounded-full px-5 py-3 border-2 border-transparent focus-within:border-primary transition-all">
            <MapPin size={20} className="text-tertiary" />
            <input 
              className="bg-transparent border-none focus:ring-0 w-full font-bold text-zinc-900 placeholder:text-outline-variant" 
              placeholder="梦想目的地" 
              type="text" 
              defaultValue="京都樱花之旅"
            />
          </div>
        </div>
      </section>

      {/* Transportation Selection */}
      <section className="space-y-3">
        <h2 className="text-zinc-900 font-bold text-lg px-2 flex items-center gap-2">
          <Plane size={20} className="text-secondary" />
          如何抵达？
        </h2>
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: '飞机', icon: Plane, active: true, color: 'primary' },
            { label: '火车', icon: Train, active: false, color: 'secondary' },
            { label: '巴士', icon: Bus, active: false, color: 'tertiary' },
            { label: '自驾', icon: Car, active: false, color: 'primary-container' },
          ].map((mode, i) => (
            <button 
              key={i}
              className={`flex flex-col items-center gap-2 p-4 rounded-2xl transition-all bouncy-hover ${
                mode.active 
                  ? `bg-primary-fixed border-2 border-primary shadow-[0_4px_12px_rgba(224,64,160,0.15)] scale-105` 
                  : 'bg-white shadow-[0_4px_12px_rgba(0,0,0,0.05)]'
              }`}
            >
              <mode.icon size={28} className={mode.active ? 'text-primary' : 'text-outline'} />
              <span className={`text-[10px] font-bold uppercase tracking-wider ${mode.active ? 'text-primary' : 'text-outline'}`}>
                {mode.label}
              </span>
            </button>
          ))}
        </div>
      </section>

      {/* Time Pickers */}
      <section className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl p-4 shadow-[0_4px_12px_rgba(0,0,0,0.05)]">
          <label className="block text-secondary font-bold text-[11px] mb-2 uppercase tracking-widest">出发</label>
          <div className="flex items-center gap-2 text-zinc-900">
            <Clock size={16} className="text-secondary" />
            <input className="border-none p-0 focus:ring-0 font-bold bg-transparent w-full" type="time" defaultValue="09:30"/>
          </div>
        </div>
        <div className="bg-white rounded-2xl p-4 shadow-[0_4px_12px_rgba(0,0,0,0.05)]">
          <label className="block text-tertiary font-bold text-[11px] mb-2 uppercase tracking-widest">到达</label>
          <div className="flex items-center gap-2 text-zinc-900">
            <Timer size={16} className="text-tertiary" />
            <input className="border-none p-0 focus:ring-0 font-bold bg-transparent w-full" type="time" defaultValue="14:15"/>
          </div>
        </div>
      </section>

      {/* Accommodation */}
      <section className="bg-secondary-container rounded-2xl p-6 shadow-[0_8px_24px_rgba(124,82,170,0.1)]">
        <h2 className="text-secondary font-bold text-sm mb-4 flex items-center gap-2">
          <Bed size={18} />
          入住酒店
        </h2>
        <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-4 border border-white">
          <input 
            className="w-full bg-transparent border-none focus:ring-0 font-medium placeholder:text-secondary-fixed-dim text-zinc-800" 
            placeholder="酒店名称或地址..." 
            type="text" 
            defaultValue="樱花皇宫大酒店"
          />
        </div>
      </section>

      {/* Packing Checklist */}
      <section className="space-y-3">
        <h2 className="text-zinc-900 font-bold text-lg px-2 flex items-center gap-2">
          <ListChecks size={20} className="text-primary" />
          准备好了吗？
        </h2>
        <div className="grid grid-cols-12 gap-3">
          <div className="col-span-7 bg-white rounded-2xl p-4 shadow-[0_4px_16px_rgba(0,0,0,0.04)]">
            <div className="space-y-3">
              {[
                { label: '相机与镜头', checked: true },
                { label: '便携式充电器', checked: false },
                { label: '护照', checked: true },
              ].map((item, i) => (
                <label key={i} className="flex items-center gap-3 cursor-pointer group">
                  <input 
                    type="checkbox" 
                    defaultChecked={item.checked}
                    className="rounded-full text-primary focus:ring-primary h-5 w-5 transition-all" 
                  />
                  <span className="text-sm font-medium group-hover:text-primary transition-colors text-zinc-800">{item.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="col-span-5 flex flex-col gap-3">
            <div className="flex-1 bg-tertiary-fixed rounded-2xl p-4 flex flex-col items-center justify-center text-center bouncy-hover">
              <Coffee size={20} className="text-tertiary mb-1" />
              <span className="text-[10px] font-bold text-tertiary uppercase">零食</span>
            </div>
            <div className="flex-1 bg-primary-fixed rounded-2xl p-4 flex flex-col items-center justify-center text-center bouncy-hover">
              <Pill size={20} className="text-primary mb-1" />
              <span className="text-[10px] font-bold text-primary uppercase">药品</span>
            </div>
          </div>
        </div>
      </section>

      {/* Memo Section */}
      <section className="bg-white rounded-2xl p-6 shadow-[0_8px_32px_rgba(0,0,0,0.04)]">
        <label className="flex items-center gap-2 text-outline font-bold text-sm mb-3">
          <Edit3 size={14} />
          旅行笔记
        </label>
        <textarea 
          className="w-full bg-surface-variant/50 rounded-2xl border-none focus:ring-2 focus:ring-primary/20 text-sm font-medium p-4 resize-none text-zinc-800" 
          placeholder="别忘了带雨伞，预约代码是 #12345..." 
          rows={3}
        />
      </section>

      {/* Save Button */}
      <div className="pt-4 pb-8">
        <button className="w-full py-5 bg-primary rounded-full candy-shadow-primary bouncy-hover flex items-center justify-center gap-3 text-white font-black text-lg">
          <Save size={24} />
          保存计划
        </button>
      </div>
    </div>
  );
};
