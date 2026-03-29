
import { Database } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-950 border-t border-slate-900 py-12">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
        
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-900/40 border border-emerald-500/20 flex items-center justify-center">
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <span className="text-white font-bold text-lg tracking-tight">NBU RAG Intelligence</span>
        </div>

        <div className="text-slate-500 text-sm">
          &copy; {new Date().getFullYear()} NBU RAG Platform. Developed for UzHack 2026.
        </div>

        <div className="flex gap-6">
          <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm font-medium">Twitter</a>
          <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm font-medium">GitHub</a>
          <a href="https://uzse.uz" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-white transition-colors text-sm font-medium">Dataset Source</a>
        </div>
      </div>
    </footer>
  );
}
