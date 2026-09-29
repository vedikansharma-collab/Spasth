import React, { useEffect, useState } from 'react';
import { Shield, ArrowRight, MessageSquare } from 'lucide-react';

export default function Navbar({ onOpenChat }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className={`sticky top-0 z-50 bg-white transition-all duration-200 ${scrolled ? 'border-b border-[#E2E8E8] shadow-sm' : 'border-b border-[#F7F7F8]'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Left Brand Identity */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-10 h-10 rounded-xl bg-[#003339] flex items-center justify-center text-[#73FFFF] shadow-sm">
              <Shield className="w-5 h-5 text-[#73FFFF]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-heading font-black text-xl text-[#003339] tracking-tight">Spasth</span>
                <span className="px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase bg-[rgba(57,171,173,0.12)] text-[#006668] border border-[#39ABAD]/40 rounded-md">
                  Insurance Intelligence
                </span>
              </div>
              <p className="text-[11px] text-[#4A5859] font-medium hidden sm:block">
                Policy Intelligence &amp; Treatment Cost Estimator
              </p>
            </div>
          </div>

          {/* Center Navigation Links */}
          <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-[#003339]">
            <button onClick={() => scrollToSection('how-it-works')} className="hover:text-[#006668] transition-colors cursor-pointer">
              How It Works
            </button>
            <button onClick={() => scrollToSection('estimator')} className="hover:text-[#006668] transition-colors cursor-pointer">
              Estimator
            </button>
            <button onClick={() => scrollToSection('evidence')} className="hover:text-[#006668] transition-colors cursor-pointer">
              Evidence
            </button>
            <button onClick={() => scrollToSection('why-spasth')} className="hover:text-[#006668] transition-colors cursor-pointer">
              Why Spasth
            </button>
          </nav>

          {/* Right Action */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenChat}
              className="btn-secondary px-3.5 py-2 text-xs sm:text-sm font-semibold flex items-center space-x-1.5 cursor-pointer border-[#39ABAD]/40 text-[#006668] hover:bg-[#39ABAD]/10 transition-all shadow-2xs rounded-xl"
            >
              <MessageSquare className="w-4 h-4 text-[#006668]" />
              <span>Ask AI Query</span>
            </button>

            <button
              onClick={() => scrollToSection('estimator')}
              className="btn-primary px-4 py-2 text-xs sm:text-sm font-semibold flex items-center space-x-1.5 cursor-pointer shadow-sm"
            >
              <span>Analyze My Policy</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
