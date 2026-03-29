
import { motion } from 'framer-motion';
import { MessageSquare, ArrowRight } from 'lucide-react';

const examples = [
  {
    query: "What was the total net profit of ALSK in the 3rd Quarter of 2025?",
    result: "The net profit for ALSK in Q3 2025 was 42.5 Billion UZS.",
    source: "MSFO_quarter_ALSK.xlsx (Sheet 3)",
    color: "from-emerald-500/20 to-emerald-900/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400"
  },
  {
    query: "Назовите текущего председателя правления Xalq Banki?",
    result: "Согласно существенному факту от 12 января, председателем правления является Абдуллаев А.А.",
    source: "fact_12_XalqBanki.pdf (Page 1)",
    color: "from-indigo-500/20 to-indigo-900/10",
    border: "border-indigo-500/30",
    text: "text-indigo-400"
  },
  {
    query: "Is there any mention of dividend payouts for UZBAT in 2024?",
    result: "Yes, UZBAT announced a dividend payout of 5,000 UZS per share for the fiscal year 2024.",
    source: "NSBU_annual_UZBAT.pdf (Page 8)",
    color: "from-yellow-500/20 to-yellow-900/10",
    border: "border-yellow-500/30",
    text: "text-yellow-400"
  }
];

export default function UsageExamplesSection() {
  return (
    <section className="py-24 bg-slate-950 relative overflow-hidden">
      <div className="absolute top-1/2 right-0 w-[500px] h-[500px] bg-indigo-900/20 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Real Queries. Real Time.</h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            See how the system maps complex bilingual questions seamlessly directly to verifiable sources inside the raw dataset.
          </p>
        </div>

        <div className="space-y-6 max-w-4xl mx-auto">
          {examples.map((ex, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2 }}
              className={`bg-gradient-to-r ${ex.color} border ${ex.border} rounded-3xl p-6 md:p-8 backdrop-blur-sm`}
            >
              <div className="flex flex-col gap-6">
                <div className="flex items-start gap-4">
                  <div className="mt-1 p-2 bg-slate-950/50 rounded-lg">
                    <MessageSquare className={`w-5 h-5 ${ex.text}`} />
                  </div>
                  <div>
                    <h4 className="text-slate-300 font-medium text-sm mb-1">User Ask</h4>
                    <p className="text-white text-lg font-medium">"{ex.query}"</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-slate-500 pl-4 md:pl-8">
                  <ArrowRight className="w-5 h-5" />
                  <div className="flex-1 bg-slate-950/40 border border-slate-800 rounded-xl p-5">
                    <p className="text-slate-200 leading-relaxed mb-4">{ex.result}</p>
                    <div className="inline-flex items-center px-3 py-1 bg-slate-950 rounded-md border border-slate-800 text-xs font-mono text-slate-400">
                      Cited: {ex.source}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
