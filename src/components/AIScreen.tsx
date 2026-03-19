import React, { useState } from 'react';
import { Sparkles, Image as ImageIcon, Calendar as CalendarIcon, Clock, Plane, Edit3, ListChecks, Save, Trash2 } from 'lucide-react';
import { motion } from 'motion/react';

export const AIScreen: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleExtract = () => {
    setIsExtracting(true);
    setTimeout(() => {
      setIsExtracting(false);
      setShowResults(true);
    }, 1500);
  };

  return (
    <div className="space-y-8 pb-24">
      {/* Welcome Message */}
      <section className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary-container flex items-center justify-center shadow-[0_4px_12px_rgba(224,64,160,0.2)]">
            <Sparkles size={24} className="text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-primary">魔法助手</h2>
            <p className="text-outline text-sm">粘贴行程信息或上传票据图片</p>
          </div>
        </div>
      </section>

      {/* Input Section */}
      <section className="space-y-4">
        <div className="relative group">
          <textarea 
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="w-full min-h-[160px] p-6 rounded-2xl bg-white border-2 border-pink-100 focus:border-primary focus:ring-4 focus:ring-primary/10 shadow-[0_8px_24px_rgba(0,0,0,0.04)] resize-none text-zinc-800 transition-all duration-300" 
            placeholder="在此粘贴行程信息..."
          />
          <div className="absolute bottom-4 right-4 flex gap-2">
            <button className="bg-secondary-fixed text-secondary px-4 py-2 rounded-full font-bold text-sm flex items-center gap-2 bouncy-hover shadow-[0_4px_12px_rgba(124,82,170,0.2)]">
              <ImageIcon size={16} />
              上传票据图片
            </button>
          </div>
        </div>
        
        <button 
          onClick={handleExtract}
          disabled={isExtracting}
          className="w-full py-4 bg-primary text-white rounded-full font-bold text-lg flex items-center justify-center gap-3 shadow-[0_8px_24px_rgba(224,64,160,0.3)] hover:scale-[1.02] active:scale-95 transition-all duration-300 disabled:opacity-70"
        >
          {isExtracting ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
            >
              <Sparkles size={24} />
            </motion.div>
          ) : (
            <Sparkles size={24} />
          )}
          {isExtracting ? '魔法提取中...' : '魔法提取'}
        </button>
      </section>

      {/* Preview Results */}
      {showResults && (
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-zinc-900 px-2">提取详情</h3>
            <span className="text-xs font-bold text-tertiary bg-tertiary-fixed px-3 py-1 rounded-full uppercase tracking-wider">审核中</span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Date Card */}
            <div className="bg-white p-5 rounded-2xl shadow-[0_8px_20px_rgba(224,64,160,0.08)] border border-pink-50 bouncy-hover">
              <div className="flex items-center gap-2 text-primary mb-3">
                <CalendarIcon size={20} />
                <span className="text-xs font-bold uppercase tracking-tight">日期</span>
              </div>
              <p className="text-lg font-bold text-zinc-900">2024年10月1日</p>
              <p className="text-xs text-outline mt-1">周六</p>
            </div>

            {/* Time Card */}
            <div className="bg-white p-5 rounded-2xl shadow-[0_8px_20px_rgba(224,64,160,0.08)] border border-pink-50 bouncy-hover">
              <div className="flex items-center gap-2 text-tertiary mb-3">
                <Clock size={20} />
                <span className="text-xs font-bold uppercase tracking-tight">时间</span>
              </div>
              <p className="text-lg font-bold text-zinc-900">10:00 AM</p>
              <p className="text-xs text-outline mt-1">预计到达: 12:30 PM</p>
            </div>

            {/* Transport Card */}
            <div className="col-span-2 bg-white p-5 rounded-2xl shadow-[0_8px_20px_rgba(224,64,160,0.08)] border border-pink-50 flex items-center justify-between bouncy-hover">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-secondary-container flex items-center justify-center text-secondary">
                  <Plane size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-secondary uppercase tracking-tight">交通</span>
                    <span className="bg-secondary/10 text-secondary text-[10px] px-2 py-0.5 rounded-full font-black">MU5101</span>
                  </div>
                  <p className="text-lg font-bold text-zinc-900">北京 → 上海</p>
                </div>
              </div>
              <Edit3 size={20} className="text-outline" />
            </div>

            {/* Prep List Card */}
            <div className="col-span-2 bg-secondary-fixed/30 p-5 rounded-2xl border-2 border-dashed border-secondary/20">
              <div className="flex items-center gap-2 text-secondary mb-4">
                <ListChecks size={20} />
                <span className="text-xs font-bold uppercase tracking-tight">准备清单</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {['电子身份证', '电子票据', '充电宝', '防晒霜'].map((item, i) => (
                  <label key={i} className="flex items-center gap-3 bg-white/60 p-2 rounded-full cursor-pointer group">
                    <input 
                      type="checkbox" 
                      defaultChecked={i < 2}
                      className="w-5 h-5 rounded-full border-secondary text-secondary focus:ring-secondary/20" 
                    />
                    <span className="text-sm font-medium text-zinc-800">{item}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 pt-4">
            <button className="flex-1 py-4 bg-surface-variant text-zinc-800 font-bold rounded-full hover:bg-outline-variant transition-colors flex items-center justify-center gap-2">
              <Trash2 size={20} />
              放弃
            </button>
            <button className="flex-[2] py-4 bg-tertiary text-white font-bold rounded-full candy-shadow-tertiary bouncy-hover flex items-center justify-center gap-2">
              <Save size={20} />
              确认并保存
            </button>
          </div>
        </motion.section>
      )}
    </div>
  );
};
