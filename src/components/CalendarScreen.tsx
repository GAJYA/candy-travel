import React from 'react';
import { ChevronLeft, ChevronRight, Plane, Train, Utensils, Landmark, MapPin, Ticket, Plus } from 'lucide-react';
import { motion } from 'motion/react';

export const CalendarScreen: React.FC = () => {
  const days = ['日', '一', '二', '三', '四', '五', '六'];
  const dates = Array.from({ length: 31 }, (_, i) => i + 1);
  const offset = 2; // Oct 2024 starts on Tuesday

  return (
    <div className="space-y-6 pb-24">
      {/* Calendar Widget */}
      <section className="bg-white rounded-3xl shadow-[0_8px_24px_rgba(224,64,160,0.1)] p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-primary">2024年10月</h2>
          <div className="flex gap-2">
            <button className="w-10 h-10 flex items-center justify-center rounded-full bg-primary-fixed hover:bg-primary-container transition-colors bouncy-hover">
              <ChevronLeft size={20} className="text-primary" />
            </button>
            <button className="w-10 h-10 flex items-center justify-center rounded-full bg-primary-fixed hover:bg-primary-container transition-colors bouncy-hover">
              <ChevronRight size={20} className="text-primary" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-7 text-center mb-2">
          {days.map(day => (
            <span key={day} className="text-[12px] font-bold text-outline uppercase tracking-widest">{day}</span>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-y-2">
          {/* Previous month days */}
          <div className="h-12 flex items-center justify-center text-outline-variant">29</div>
          <div className="h-12 flex items-center justify-center text-outline-variant">30</div>
          
          {dates.map(date => {
            const isTripStart = date === 4;
            const isTripDay = date >= 5 && date <= 7;
            const isSelected = date === 13;
            const hasEvent = date === 16;

            return (
              <div key={date} className="h-12 flex items-center justify-center relative group cursor-pointer">
                {isTripStart && (
                  <div className="absolute inset-1 bg-tertiary rounded-full shadow-[0_4px_12px_rgba(0,150,204,0.3)] flex items-center justify-center">
                    <span className="text-white font-bold">{date}</span>
                    <Plane size={10} className="absolute -top-1 -right-1 text-tertiary bg-white rounded-full p-0.5 shadow-sm" />
                  </div>
                )}
                {isTripDay && (
                  <div className="absolute inset-1 bg-tertiary-fixed-dim rounded-full flex items-center justify-center">
                    <span className="text-on-tertiary-container font-bold">{date}</span>
                    {date === 7 && <Train size={10} className="absolute -top-1 -right-1 text-secondary bg-white rounded-full p-0.5 shadow-sm" />}
                  </div>
                )}
                {isSelected && (
                  <div className="absolute inset-1 bg-primary border-4 border-primary-fixed rounded-full candy-shadow-primary flex items-center justify-center scale-110 z-10">
                    <span className="text-white font-bold">{date}</span>
                  </div>
                )}
                {!isTripStart && !isTripDay && !isSelected && (
                  <>
                    <span className="z-10 font-bold text-zinc-800">{date}</span>
                    <div className="absolute inset-0 bg-secondary-fixed rounded-full scale-0 group-hover:scale-90 transition-transform"></div>
                    {hasEvent && <div className="absolute bottom-1 w-1.5 h-1.5 bg-secondary rounded-full"></div>}
                  </>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Trip Details */}
      <section className="space-y-4">
        <div className="flex justify-between items-end mb-2">
          <div>
            <h3 className="text-lg font-bold text-zinc-900">10月13日 星期日</h3>
            <p className="text-sm text-outline">您已计划了 2 项活动</p>
          </div>
          <button className="px-4 py-2 bg-secondary text-white rounded-full text-sm font-bold shadow-[0_4px_12px_rgba(124,82,170,0.3)] bouncy-hover">
            添加活动
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {/* Activity 1 */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white p-5 rounded-2xl shadow-[0_8px_24px_rgba(0,0,0,0.05)] border-l-8 border-tertiary flex gap-4 transition-all hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)] cursor-pointer group"
          >
            <div className="flex items-center justify-center w-12 h-12 bg-tertiary-fixed rounded-full text-tertiary">
              <Utensils size={24} />
            </div>
            <div className="flex-1">
              <div className="flex justify-between">
                <h4 className="font-bold text-zinc-900">在樱屋吃午餐</h4>
                <span className="text-[12px] font-bold text-tertiary bg-tertiary-fixed px-2 py-0.5 rounded-full">12:30 PM</span>
              </div>
              <p className="text-sm text-outline mt-1">美食寿司和拉面吧</p>
              <div className="flex items-center gap-1 mt-2 text-[12px] text-outline">
                <MapPin size={14} />
                <span>东京区</span>
              </div>
            </div>
          </motion.div>

          {/* Activity 2 */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white p-5 rounded-2xl shadow-[0_8px_24px_rgba(0,0,0,0.05)] border-l-8 border-secondary flex gap-4 transition-all hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)] cursor-pointer group"
          >
            <div className="flex items-center justify-center w-12 h-12 bg-secondary-fixed rounded-full text-secondary">
              <Landmark size={24} />
            </div>
            <div className="flex-1">
              <div className="flex justify-between">
                <h4 className="font-bold text-zinc-900">数字艺术馆</h4>
                <span className="text-[12px] font-bold text-secondary bg-secondary-fixed px-2 py-0.5 rounded-full">3:00 PM</span>
              </div>
              <p className="text-sm text-outline mt-1">沉浸式 teamLab 无界展</p>
              <div className="flex items-center gap-1 mt-2 text-[12px] text-outline">
                <Ticket size={14} />
                <span>门票已确认</span>
              </div>
            </div>
          </motion.div>

          {/* Next Day Preview */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-r from-primary-fixed to-secondary-fixed p-6 rounded-2xl shadow-sm flex items-center justify-between group cursor-pointer hover:shadow-md transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full overflow-hidden border-2 border-white shadow-sm">
                <img 
                  className="w-full h-full object-cover" 
                  src="https://picsum.photos/seed/kyoto/100/100" 
                  alt="Kyoto" 
                  referrerPolicy="no-referrer"
                />
              </div>
              <div>
                <p className="text-[12px] font-bold text-primary uppercase tracking-tighter">明日预告</p>
                <h4 className="font-bold text-zinc-800">前往京都的新干线</h4>
              </div>
            </div>
            <ChevronRight size={20} className="text-zinc-800 transition-transform group-hover:translate-x-1" />
          </motion.div>
        </div>
      </section>

      {/* FAB */}
      <button className="fixed right-6 bottom-24 w-16 h-16 bg-primary text-white rounded-full shadow-[0_8px_24px_rgba(224,64,160,0.4)] flex items-center justify-center bouncy-hover z-40 group">
        <Plus size={32} className="transition-transform duration-300 group-hover:rotate-90" />
      </button>
    </div>
  );
};
