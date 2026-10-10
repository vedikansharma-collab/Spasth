import React, { useEffect, useState } from 'react';
import { 
  Shield, FileText, ArrowRight, Bot, Calculator, 
  BookOpen, LayoutDashboard, UploadCloud, CheckCircle2 
} from 'lucide-react';

export default function Navbar({ 
  activeTab = 'dashboard', 
  onTabChange, 
  activePolicy = null,
  onUploadClick 
}) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 15);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'assistant', label: 'Policy Assistant', icon: Bot },
    { id: 'estimator', label: 'Cost Estimator', icon: Calculator },
    { id: 'document', label: 'Policy Document', icon: BookOpen },
  ];

  return (
    <header className={`sticky top-0 z-50 bg-white transition-all duration-200 ${scrolled ? 'border-b border-[#E2E8E8] shadow-sm' : 'border-b border-[#F7F7F8]'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Left Brand Identity */}
          <div 
            className="flex items-center space-x-3 cursor-pointer shrink-0" 
            onClick={() => onTabChange && onTabChange('dashboard')}
          >
            <div className="w-10 h-10 rounded-xl bg-[#003339] flex items-center justify-center text-[#73FFFF] shadow-xs">
              <Shield className="w-5 h-5 text-[#73FFFF]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-heading font-black text-xl text-[#003339] tracking-tight">SPASTH</span>
                <span className="px-2 py-0.5 text-[9px] font-bold tracking-wider uppercase bg-[rgba(57,171,173,0.12)] text-[#006668] border border-[#39ABAD]/40 rounded-md">
                  Insurance Intelligence
                </span>
              </div>
              <p className="text-[11px] text-[#4A5859] font-medium hidden sm:block">
                Policy Understanding &amp; Treatment Cost Intelligence
              </p>
            </div>
          </div>

          {/* Center Navigation Tabs */}
          <nav className="hidden lg:flex items-center space-x-1 p-1 bg-[#F7F7F8] rounded-xl border border-[#E2E8E8]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange && onTabChange(item.id)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#006668] text-white shadow-2xs'
                      : 'text-[#4A5859] hover:text-[#003339] hover:bg-white'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-[#4A5859]'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Action & Active Policy Indicator */}
          <div className="flex items-center space-x-3">
            {/* Active Policy Pill */}
            {activePolicy ? (
              <div 
                onClick={() => onTabChange && onTabChange('document')}
                className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-[rgba(57,171,173,0.08)] border border-[#39ABAD]/40 text-[#006668] hover:bg-[rgba(57,171,173,0.15)] transition-all cursor-pointer text-xs"
                title="Click to view full policy document"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-[#006668] shrink-0" />
                <span className="font-semibold truncate max-w-[140px] md:max-w-[200px]">
                  {activePolicy.original_filename}
                </span>
                <span className="text-[10px] font-mono text-[#006668]/70">
                  ({activePolicy.page_count}p)
                </span>
              </div>
            ) : (
              <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#F7F7F8] border border-[#E2E8E8] text-[#4A5859] text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-slate-300"></span>
                <span>No Policy Active</span>
              </div>
            )}

            {/* Upload Button */}
            <button
              onClick={onUploadClick}
              className="btn-primary px-3.5 py-2 text-xs sm:text-sm font-semibold flex items-center space-x-1.5 cursor-pointer shadow-xs shrink-0"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload Policy</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Sub-Bar */}
        <div className="lg:hidden flex items-center space-x-1 py-2 overflow-x-auto border-t border-[#F7F7F8]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange && onTabChange(item.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 shrink-0 transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#006668] text-white shadow-2xs'
                    : 'text-[#4A5859] hover:text-[#003339] bg-[#F7F7F8]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-[#4A5859]'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
