
import { motion } from 'framer-motion';
import { Database, Brain, ArrowRight } from 'lucide-react';

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden w-full pt-20">
      {/* Royal Background glow effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60vw] h-[60vw] max-w-4xl max-h-4xl bg-gradient-to-tr from-emerald-900/30 via-indigo-900/40 to-yellow-900/30 rounded-full blur-[120px] opacity-60 pointer-events-none" />
      <div className="absolute top-[-10%] right-[-5%] w-[40vw] h-[40vw] bg-purple-900/20 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-10 w-full grid lg:grid-cols-2 gap-16 items-center">
        
        {/* Left Column: Text Content */}
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex flex-col gap-8 text-left"
        >
          <div className="inline-flex items-center gap-2 pl-2 pr-4 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm w-fit">
            <span className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </span>
            <span className="text-sm font-medium text-slate-300">UzHack 2026 Hackathon Finalist</span>
          </div>

          <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-white leading-[1.1]">
            Financial Truth, <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-indigo-400 to-yellow-400 pb-2 inline-block">
              Extracted.
            </span>
          </h1>

          <p className="text-lg text-slate-400 max-w-xl leading-relaxed">
            A production-grade, multilingual Retrieval-Augmented Generation (RAG) intelligence platform built to parse thousands of complex NSBU/MSFO financial reports across Uzbekistan with zero hallucinations.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <button 
              onClick={() => document.getElementById('dedication')?.scrollIntoView({ behavior: 'smooth' })}
              className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold rounded-2xl transition-all duration-300 ease-in-out hover:scale-[1.02] shadow-[0_0_40px_rgba(16,185,129,0.3)] hover:shadow-[0_0_60px_rgba(16,185,129,0.5)] active:scale-95"
            >
              <span>Learn More</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </motion.div>

        {/* Right Column: Visual Elements */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
          className="relative lg:h-[600px] w-full flex items-center justify-center hidden lg:flex"
        >
          {/* Mock floating system UI snippet */}
          <div className="relative w-full max-w-lg aspect-square">
            <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-white/0 rounded-[2rem] border border-white/10 backdrop-blur-xl shadow-2xl p-8 flex flex-col gap-6 transform rotate-3 hover:rotate-0 transition-all duration-700 ease-out group">
              
              <div className="flex items-center gap-4 border-b border-white/5 pb-6">
                <div className="p-3 bg-indigo-500/20 rounded-xl">
                  <Brain className="w-8 h-8 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-white font-medium text-lg">Hybrid Search Engine</h3>
                  <p className="text-slate-400 text-sm">FAISS Dense + BM25</p>
                </div>
              </div>

              <div className="flex-1 rounded-xl bg-slate-950/50 border border-slate-800/50 p-6 flex flex-col gap-4">
                <div className="flex items-center gap-3 text-sm text-slate-300">
                  <Database className="w-4 h-4 text-emerald-400" />
                  Processing query over 1,000+ reports...
                </div>
                <div className="w-3/4 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: "0%" }}
                    animate={{ width: "100%" }}
                    transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
                    className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400"
                  />
                </div>
                <div className="flex flex-col gap-2 mt-auto">
                  <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm py-2 px-4 rounded-lg w-fit">
                    "Чистая прибыль составила 120.5 млрд сум"
                  </div>
                  <div className="text-xs text-slate-500 ml-2">
                    Source: Xalq_Banki_2025_NSBU.pdf (Page 14)
                  </div>
                </div>
              </div>

            </div>
          </div>
        </motion.div>

      </div>
    </section>
  );
}
