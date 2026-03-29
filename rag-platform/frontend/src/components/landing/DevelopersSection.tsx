import { motion } from 'framer-motion';
import { Code2, Github, LayoutTemplate, Sparkles } from 'lucide-react';

export default function DevelopersSection() {
  return (
    <section className="relative py-28 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 border-t border-slate-800 overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-20 items-center">

          {/* Left Side */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <div className="inline-flex items-center gap-2 text-xs text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full mb-6">
              <Sparkles className="w-3 h-3" /> Built by Engineers
            </div>

            <h2 className="text-4xl md:text-5xl font-semibold text-white mb-6 tracking-tight">
              The Architects Behind the System
            </h2>

            <p className="text-slate-400 text-lg leading-relaxed mb-10 max-w-xl">
              Crafted with precision for the NBU RAG Challenge, this platform is the result of deep expertise in AI systems, backend engineering, and frontend performance. Every component is designed to be auditable, scalable, and production-ready.
            </p>

            <div className="space-y-4">
              <div className="group flex items-center gap-4 bg-slate-900/60 backdrop-blur border border-slate-800 hover:border-emerald-500/40 transition-all p-5 rounded-2xl">
                <Code2 className="w-6 h-6 text-emerald-400 group-hover:scale-110 transition-transform" />
                <div className="text-slate-200 font-medium">
                  Python · FastAPI · Semantic Retrieval
                </div>
              </div>

              <div className="group flex items-center gap-4 bg-slate-900/60 backdrop-blur border border-slate-800 hover:border-indigo-500/40 transition-all p-5 rounded-2xl">
                <LayoutTemplate className="w-6 h-6 text-indigo-400 group-hover:scale-110 transition-transform" />
                <div className="text-slate-200 font-medium">
                  React · Tailwind · Motion Architecture
                </div>
              </div>
            </div>

            <div className="mt-12">
              <button className="group inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 transition-all font-medium">
                <Github className="w-5 h-5 group-hover:rotate-6 transition-transform" />
                View System Architecture
              </button>
            </div>
          </motion.div>

          {/* Right Side */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-[28px] p-8 md:p-10 shadow-[0_20px_80px_rgba(0,0,0,0.6)] overflow-hidden">

              {/* Glow inside card */}
              <div className="absolute -top-20 -right-20 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl" />

              <h3 className="text-2xl font-semibold text-white mb-2">
                Built to Scale Effortlessly
              </h3>
              <p className="text-slate-400 mb-8">
                Engineered with modular architecture, ready to expand across institutions and datasets with minimal friction.
              </p>

              {/* Code block */}
              <div className="relative rounded-xl border border-slate-800/60 bg-slate-950/80 p-6 font-mono text-sm text-slate-300 overflow-hidden">
                <div className="absolute top-3 left-4 flex gap-2">
                  <span className="w-2.5 h-2.5 bg-red-500 rounded-full" />
                  <span className="w-2.5 h-2.5 bg-yellow-500 rounded-full" />
                  <span className="w-2.5 h-2.5 bg-green-500 rounded-full" />
                </div>

                <div className="mt-6 space-y-2">
                  <div className="text-slate-500"># Start full system</div>
                  <div>
                    <span className="text-indigo-400">npm</span> run dev
                  </div>
                  <div>
                    <span className="text-emerald-400">uvicorn</span> main:app --reload
                  </div>
                </div>
              </div>

            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
