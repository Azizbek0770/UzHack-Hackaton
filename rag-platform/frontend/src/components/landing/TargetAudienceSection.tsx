
import { motion } from 'framer-motion';
import { Briefcase, LineChart, Landmark } from 'lucide-react';

const targets = [
  {
    title: "Financial Analysts",
    desc: "Lightning-fast metric extraction across 500+ reports without manual Ctrl+F searches.",
    icon: <LineChart className="w-8 h-8 text-emerald-500" />
  },
  {
    title: "Corporate Auditors",
    desc: "Verify disclosures and factual consistencies automatically with hard-cited page references.",
    icon: <Briefcase className="w-8 h-8 text-indigo-500" />
  },
  {
    title: "Investment Banks",
    desc: "Instantly aggregate corporate events and essential facts before executing major market moves.",
    icon: <Landmark className="w-8 h-8 text-yellow-500" />
  }
];

export default function TargetAudienceSection() {
  return (
    <section className="py-24 bg-slate-900 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-end mb-16 gap-8">
          <div className="max-w-2xl">
            <motion.h2 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="text-4xl font-bold text-white mb-4"
            >
              Who Needs This Intelligence?
            </motion.h2>
            <p className="text-slate-400 text-lg">
              Designed explicitly for high-stakes financial environments where speed and accuracy dictate capital allocation.
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {targets.map((target, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              className="bg-slate-950 p-8 rounded-3xl border border-slate-800 hover:border-indigo-500/50 transition-all duration-300 shadow-2xl"
            >
              <div className="mb-6 p-4 bg-slate-900 rounded-2xl w-fit">
                {target.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-2">{target.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                {target.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
