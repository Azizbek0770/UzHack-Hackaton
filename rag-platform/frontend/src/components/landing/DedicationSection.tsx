
import { motion } from 'framer-motion';
import { FileText, Cpu, Search } from 'lucide-react';

const features = [
  {
    icon: <FileText className="w-6 h-6 text-indigo-400" />,
    title: "Multi-Format Processing",
    description: "Seamlessly parses scanned PDFs via PaddleOCR alongside nested multi-sheet Excel financial reports effortlessly."
  },
  {
    icon: <Search className="w-6 h-6 text-emerald-400" />,
    title: "Hybrid Information Retrieval",
    description: "Combines FAISS vector semantic similarity with BM25 keyword matching for unparalleled financial accuracy."
  },
  {
    icon: <Cpu className="w-6 h-6 text-yellow-400" />,
    title: "Zero-Hallucination Guardrails",
    description: "Strict reasoning prompts constrain the LLM exclusively to context-bound data, ensuring absolute trustworthiness."
  }
];

export default function DedicationSection() {
  return (
    <section id="dedication" className="relative py-24 w-full bg-slate-950 border-t border-slate-900 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-10">
        
        <div className="text-center max-w-3xl mx-auto mb-20">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl md:text-5xl font-bold text-white mb-6"
          >
            Built for the NBU Challenge
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-slate-400 text-lg"
          >
            Navigating un-structured JSON, blurry scans, and complex National and International accounting standards across 35 companies simultaneously. 
          </motion.p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className="bg-slate-900/50 backdrop-blur-md border border-slate-800 p-8 rounded-3xl hover:bg-slate-800/50 transition-colors group"
            >
              <div className="w-14 h-14 bg-slate-800 rounded-2xl flex items-center justify-center mb-6 border border-slate-700 group-hover:border-slate-600 transition-colors">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
              <p className="text-slate-400 leading-relaxed text-sm">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}
