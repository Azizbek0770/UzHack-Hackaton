import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Brain } from 'lucide-react';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out backdrop-blur-md ${
        scrolled 
          ? 'py-3 bg-slate-950/80 border-b border-white/10 shadow-lg' 
          : 'py-6 bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between">
        {/* Logo */}
        <div 
          className="flex items-center gap-2 cursor-pointer transition-transform hover:scale-105" 
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <span className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
            <Brain className="w-5 h-5 text-emerald-400" />
          </span>
          <span className="text-xl font-bold text-white tracking-tight">FinTruth</span>
        </div>

        {/* Links (middle) - Optional but good for a navbar */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <button 
            onClick={() => document.getElementById('dedication')?.scrollIntoView({ behavior: 'smooth' })} 
            className="hover:text-emerald-400 transition-colors"
          >
            About
          </button>
          <button 
            onClick={() => document.getElementById('audience')?.scrollIntoView({ behavior: 'smooth' })} 
            className="hover:text-emerald-400 transition-colors"
          >
            Audience
          </button>
          <button 
            onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })} 
            className="hover:text-emerald-400 transition-colors"
          >
            Features
          </button>
        </div>

        {/* Action Button at the End */}
        <div className="flex items-center justify-end">
          <button 
            onClick={() => navigate('/demo')}
            className={`group relative inline-flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold rounded-xl transition-all duration-300 ease-in-out hover:scale-[1.02] shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] active:scale-95 ${
              scrolled ? 'px-5 py-2 text-sm' : 'px-6 py-2.5 text-base'
            }`}
          >
            <span>Try the System Endpoint</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>
    </nav>
  );
}
