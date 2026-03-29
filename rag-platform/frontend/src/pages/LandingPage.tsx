import { useEffect, useRef, useState } from 'react'
import { motion, useInView, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  Zap, Shield, Brain, Search, FileText, Table2,
  BarChart3, ChevronRight, Database, Cpu, Network,
  ArrowRight, Sparkles, Globe, Lock, TrendingUp,
  BookOpen, AlertCircle, CheckCircle2
} from 'lucide-react'
import { FinBotAvatar } from '../components/ui/FinBotAvatar'
import { api } from '../services/api'

// ── Animated Counter ─────────────────────────────────────────────────────────

function AnimatedCounter({ target, suffix = '', prefix = '' }: { target: number; suffix?: string; prefix?: string }) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-50px' })

  useEffect(() => {
    if (!inView) return
    const duration = 1800
    const steps = 60
    const increment = target / steps
    let current = 0
    const timer = setInterval(() => {
      current = Math.min(current + increment, target)
      setCount(Math.floor(current))
      if (current >= target) clearInterval(timer)
    }, duration / steps)
    return () => clearInterval(timer)
  }, [inView, target])

  return (
    <span ref={ref}>
      {prefix}{count.toLocaleString()}{suffix}
    </span>
  )
}

// ── Floating Particle ────────────────────────────────────────────────────────

function FloatingOrb({ x, y, size, delay }: { x: string; y: string; size: number; delay: number }) {
  return (
    <motion.div
      className="absolute rounded-full pointer-events-none"
      style={{
        left: x, top: y, width: size, height: size,
        background: 'radial-gradient(circle, rgba(201,168,76,0.15) 0%, transparent 70%)',
      }}
      animate={{ y: [0, -20, 0], opacity: [0.3, 0.7, 0.3] }}
      transition={{ duration: 5 + delay, delay, repeat: Infinity, ease: 'easeInOut' }}
    />
  )
}

// ── Section Wrapper ──────────────────────────────────────────────────────────

function Section({ children, className = '', id }: { children: React.ReactNode; className?: string; id?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <motion.section id={id} ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.section>
  )
}

// ── Main Landing Page ────────────────────────────────────────────────────────

export function LandingPage() {
  const navigate = useNavigate()
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)

  useEffect(() => {
    api.getStatus()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false))
  }, [])

  return (
    <div className="min-h-screen bg-obsidian-950 overflow-x-hidden">

      {/* ── Navigation ─────────────────────────────────────────────────────── */}
      <motion.nav
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="fixed top-0 left-0 right-0 z-50 glass border-b border-obsidian-700"
      >
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FinBotAvatar size={30} />
            <div>
              <span className="font-display text-xl tracking-wider text-gray-100">FINBOT</span>
              <span className="ml-2 text-[10px] text-obsidian-400 font-mono uppercase tracking-widest">AI Platform</span>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-8">
            {[
              { label: "Imkoniyatlar", href: "#features" },
              { label: "Qanday ishlaydi", href: "#how" },
              { label: "Texnologiya", href: "#tech" },
            ].map(link => (
              <a key={link.label} href={link.href}
                className="text-sm text-obsidian-400 hover:text-gold-400 transition-colors duration-200"
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <motion.div
                animate={{ scale: backendOnline ? [1, 1.4, 1] : 1 }}
                transition={{ repeat: Infinity, duration: 2 }}
                className={`w-1.5 h-1.5 rounded-full ${backendOnline === null ? 'bg-obsidian-500' : backendOnline ? 'bg-jade-500' : 'bg-crimson-500'}`}
              />
              <span className="text-xs text-obsidian-400">
                {backendOnline === null ? 'Tekshirilmoqda...' : backendOnline ? 'Tizim tayyor' : 'Offline'}
              </span>
            </div>
            <motion.button
              onClick={() => navigate('/app')}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-500 text-obsidian-950 text-sm font-semibold hover:bg-gold-400 transition-colors shadow-[0_0_20px_rgba(201,168,76,0.3)]"
            >
              <Sparkles size={13} />
              Boshlash
            </motion.button>
          </div>
        </div>
      </motion.nav>

      {/* ── Hero Section ───────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center grid-bg pt-20 pb-32 overflow-hidden">

        {/* Background orbs */}
        <FloatingOrb x="10%" y="20%" size={300} delay={0} />
        <FloatingOrb x="75%" y="10%" size={200} delay={1.5} />
        <FloatingOrb x="60%" y="65%" size={250} delay={0.8} />
        <div className="orb-jade absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] opacity-20" />

        {/* UzHack badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="mb-8 flex items-center gap-2 px-4 py-2 rounded-full border border-gold-500/25 bg-gold-500/8 backdrop-blur-sm"
        >
          <Sparkles size={12} className="text-gold-400" />
          <span className="text-xs font-mono text-gold-400 tracking-widest uppercase">
            UzHack 2026 · NBU RAG Challenge
          </span>
          <div className="w-1 h-1 rounded-full bg-jade-500 animate-glow-pulse" />
        </motion.div>

        {/* Main heading — letter by letter */}
        <div className="text-center relative z-10 px-6">
          <HeroTitle />

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.7 }}
            className="mt-6 text-base text-obsidian-400 max-w-xl mx-auto leading-relaxed"
          >
            O'zbekiston Milliy Banki va moliya sektori hujjatlarini sun'iy intellekt yordamida
            bir zumda tahlil qiluvchi professional tizim.
          </motion.p>

          {/* Feature pills */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5, duration: 0.5 }}
            className="flex flex-wrap items-center justify-center gap-2 mt-5"
          >
            {['O\'zbek tili', 'Rus tili', 'PDF', 'XLSX', 'Real-vaqt', 'NBU'].map(tag => (
              <span key={tag} className="tech-badge">{tag}</span>
            ))}
          </motion.div>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.7, duration: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10"
          >
            <motion.button
              onClick={() => navigate('/app')}
              whileHover={{ scale: 1.04, boxShadow: '0 0 40px rgba(201,168,76,0.4)' }}
              whileTap={{ scale: 0.97 }}
              className="group flex items-center gap-3 px-8 py-4 rounded-2xl bg-gold-500 text-obsidian-950 font-semibold text-base transition-all shadow-[0_0_30px_rgba(201,168,76,0.25)]"
            >
              <Brain size={18} />
              FinBot bilan suhbat boshlash
              <motion.span
                animate={{ x: [0, 4, 0] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                <ArrowRight size={16} />
              </motion.span>
            </motion.button>

            <a href="#how"
              className="flex items-center gap-2 px-6 py-4 rounded-2xl border border-obsidian-600 text-obsidian-300 text-sm hover:border-gold-500/30 hover:text-gold-400 transition-all"
            >
              <BookOpen size={16} />
              Qanday ishlaydi?
            </a>
          </motion.div>
        </div>

        {/* Floating UI preview card */}
        <motion.div
          initial={{ opacity: 0, y: 60, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ delay: 2.0, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="relative mt-20 max-w-2xl w-full mx-auto px-6"
        >
          <PreviewCard />
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="text-[10px] text-obsidian-500 uppercase tracking-widest">Pastga aylantiring</span>
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            className="w-5 h-8 rounded-full border border-obsidian-600 flex items-start justify-center pt-1.5"
          >
            <div className="w-1 h-1.5 rounded-full bg-gold-500" />
          </motion.div>
        </motion.div>
      </section>

      {/* ── Stats Section ──────────────────────────────────────────────────── */}
      <Section className="py-20 border-y border-obsidian-800 relative overflow-hidden">
        <div className="absolute inset-0 grid-bg opacity-50" />
        <div className="max-w-6xl mx-auto px-6 relative">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: 98, suffix: '%', label: 'Aniqlik darajasi', icon: CheckCircle2 },
              { value: 1200, suffix: '+', label: 'Tahlil qilingan hujjat', icon: FileText },
              { value: 3, suffix: 's', label: "O'rtacha javob vaqti", icon: Zap, prefix: '<' },
              { value: 3, suffix: ' til', label: 'Qo\'llab-quvvatlangan til', icon: Globe },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
                className="text-center"
              >
                <div className="flex justify-center mb-3">
                  <div className="p-2.5 rounded-xl bg-gold-500/10 border border-gold-500/15">
                    <stat.icon size={18} className="text-gold-400" />
                  </div>
                </div>
                <div className="font-display text-4xl text-gold-400 tracking-wider mb-1">
                  <AnimatedCounter target={stat.value} suffix={stat.suffix} prefix={stat.prefix} />
                </div>
                <p className="text-xs text-obsidian-400">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ── How It Works ───────────────────────────────────────────────────── */}
      <Section id="how" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <SectionHeader
            badge="Algoritm"
            title="Qanday ishlaydi?"
            subtitle="4 bosqichli RAG pipeline hujjatlardan eng aniq ma'lumotni topib beradi"
          />

          <div className="grid md:grid-cols-4 gap-0 mt-16 relative">
            {/* Connector line */}
            <div className="hidden md:block absolute top-10 left-[12.5%] right-[12.5%] h-px pipeline-connector" />

            {[
              {
                step: '01',
                icon: FileText,
                title: 'Hujjat yuklash',
                desc: 'PDF va XLSX hujjatlari avtomatik ravishda parchalanadi va OCR orqali o\'qiladi',
                color: 'gold',
              },
              {
                step: '02',
                icon: Cpu,
                title: 'Vektorlashtirish',
                desc: 'bge-m3 modeli hujjat parchalarini 1024 o\'lchamli vektorlarga aylantiradi',
                color: 'jade',
              },
              {
                step: '03',
                icon: Search,
                title: 'Gibrid qidiruv',
                desc: 'FAISS va BM25 birgalikda eng mos kontekstni tezda topadi',
                color: 'gold',
              },
              {
                step: '04',
                icon: Brain,
                title: 'AI tahlil',
                desc: 'Gemini LLM faqat topilgan kontekst asosida aniq javob tuzadi',
                color: 'jade',
              },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
                className="flex flex-col items-center text-center px-4"
              >
                <div className={`relative z-10 w-20 h-20 rounded-2xl flex items-center justify-center mb-5 border ${
                  item.color === 'gold'
                    ? 'bg-gold-500/10 border-gold-500/25 shadow-[0_0_30px_rgba(201,168,76,0.1)]'
                    : 'bg-jade-500/10 border-jade-500/25 shadow-[0_0_30px_rgba(45,212,191,0.1)]'
                }`}>
                  <item.icon size={28} className={item.color === 'gold' ? 'text-gold-400' : 'text-jade-400'} />
                  <span className={`absolute -top-2 -right-2 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-lg ${
                    item.color === 'gold' ? 'bg-gold-500/20 text-gold-400' : 'bg-jade-500/20 text-jade-400'
                  }`}>{item.step}</span>
                </div>
                <h3 className="font-semibold text-gray-200 mb-2">{item.title}</h3>
                <p className="text-xs text-obsidian-400 leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Features Section ───────────────────────────────────────────────── */}
      <Section id="features" className="py-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 grid-bg opacity-40" />
        <div className="orb-gold absolute right-0 top-20 w-80 h-80 opacity-30" />

        <div className="max-w-6xl mx-auto relative">
          <SectionHeader
            badge="Imkoniyatlar"
            title="Nima qila oladi?"
            subtitle="Professional moliya tahlili uchun zarur bo'lgan barcha vositalar"
          />

          <div className="grid md:grid-cols-3 gap-5 mt-14">
            {[
              {
                icon: Shield,
                title: 'Gallyusinatsiyasiz',
                desc: 'Faqat hujjatlardagi ma\'lumotlarga asoslanadi. Hech qachon o\'ylab topilgan javob bermaydi.',
                color: 'jade',
              },
              {
                icon: Zap,
                title: 'Tezkor tahlil',
                desc: "O'rtacha 3 soniya ichida javob. FAISS vektori va BM25 gibrid tizimi bilan.",
                color: 'gold',
              },
              {
                icon: Globe,
                title: "Ko'p tilli",
                desc: "O'zbek, rus va ingliz tillarida savollarni tushunadi. Javoblar har doim o'zbek tilida.",
                color: 'jade',
              },
              {
                icon: Table2,
                title: 'Jadval tahlili',
                desc: 'XLSX jadvallardan aniq raqamlarni, yillik hisobotlardan moliyaviy ko\'rsatkichlarni chiqaradi.',
                color: 'gold',
              },
              {
                icon: BarChart3,
                title: 'Ishonch darajasi',
                desc: "Har bir javob uchun 0-100% ishonch ko'rsatkichi va manba iqtiboslari taqdim etiladi.",
                color: 'jade',
              },
              {
                icon: Lock,
                title: 'Xavfsiz',
                desc: "Ma'lumotlar lokal serverda ishlaydi. Tashqi API'larga hujjatlar uzatilmaydi.",
                color: 'gold',
              },
              {
                icon: Network,
                title: 'Ko\'p bosqichli',
                desc: "Murakkab taqqoslash va ko'p-manbali savollarni zanjirli tahlil orqali hal qiladi.",
                color: 'jade',
              },
              {
                icon: Search,
                title: 'Smart qidiruv',
                desc: "Semantik va kalit so'z qidiruvini birlashtirgan gibrid algoritm. Hech narsa o'tkazib yuborilmaydi.",
                color: 'gold',
              },
              {
                icon: TrendingUp,
                title: 'Kesh tizimi',
                desc: "Bir xil savollarga cache orqali darhol javob. Server yuklamasi minimal darajada saqlanadi.",
                color: 'jade',
              },
            ].map((feat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07, duration: 0.5 }}
                className={`feature-card p-6 rounded-2xl border border-obsidian-700 bg-obsidian-900/60 backdrop-blur-sm`}
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${
                  feat.color === 'gold'
                    ? 'bg-gold-500/10 border border-gold-500/20'
                    : 'bg-jade-500/10 border border-jade-500/20'
                }`}>
                  <feat.icon size={18} className={feat.color === 'gold' ? 'text-gold-400' : 'text-jade-400'} />
                </div>
                <h3 className="font-semibold text-gray-200 mb-2 text-sm">{feat.title}</h3>
                <p className="text-xs text-obsidian-400 leading-relaxed">{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Tech Stack ─────────────────────────────────────────────────────── */}
      <Section id="tech" className="py-20 border-t border-obsidian-800 px-6">
        <div className="max-w-5xl mx-auto">
          <SectionHeader
            badge="Stack"
            title="Texnologiya asosi"
            subtitle="Eng zamonaviy ochiq manba va tijorat vositalari"
          />

          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'BAAI/bge-m3', role: 'Embedding Modeli', color: 'gold', desc: '1024-dim ko\'p tilli' },
              { name: 'FAISS', role: 'Vektor Indeks', color: 'jade', desc: 'Facebook AI tezkor qidiruv' },
              { name: 'BM25', role: 'Kalit So\'z', color: 'gold', desc: 'Gibrid retrieval uchun' },
              { name: 'Gemini Flash', role: 'LLM', color: 'jade', desc: 'Google — Uzbekcha javob' },
              { name: 'FastAPI', role: 'Backend', color: 'gold', desc: 'Python async REST API' },
              { name: 'React + Vite', role: 'Frontend', color: 'jade', desc: 'TypeScript + Tailwind' },
              { name: 'Structlog', role: 'Logging', color: 'gold', desc: 'JSON tuzilgan loglar' },
              { name: 'PaddleOCR', role: 'OCR', color: 'jade', desc: 'Skanerlangan PDF uchun' },
            ].map((tech, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06, duration: 0.4 }}
                whileHover={{ y: -3 }}
                className={`p-4 rounded-xl border bg-obsidian-900/80 transition-all cursor-default ${
                  tech.color === 'gold'
                    ? 'border-gold-500/15 hover:border-gold-500/35'
                    : 'border-jade-500/15 hover:border-jade-500/35'
                }`}
              >
                <div className={`text-xs font-mono font-bold mb-1 ${tech.color === 'gold' ? 'text-gold-400' : 'text-jade-400'}`}>
                  {tech.name}
                </div>
                <div className="text-[11px] text-gray-400 font-medium mb-1">{tech.role}</div>
                <div className="text-[10px] text-obsidian-500">{tech.desc}</div>
              </motion.div>
            ))}
          </div>

          {/* Architecture diagram */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="mt-10 p-6 rounded-2xl border border-obsidian-700 bg-obsidian-900/60 font-mono text-xs text-obsidian-400"
          >
            <div className="text-[10px] uppercase tracking-widest text-gold-500/60 mb-4">Pipeline arxitekturasi</div>
            <div className="space-y-2 overflow-x-auto">
              <div className="flex flex-wrap items-center gap-2 text-[11px]">
                <span className="text-gold-400/80">Savol</span>
                <ChevronRight size={10} className="text-obsidian-600" />
                <span className="px-2 py-0.5 rounded bg-obsidian-800 border border-obsidian-700">QueryClassifier</span>
                <ChevronRight size={10} className="text-obsidian-600" />
                <span className="px-2 py-0.5 rounded bg-obsidian-800 border border-obsidian-700">bge-m3 Embed</span>
                <ChevronRight size={10} className="text-obsidian-600" />
                <span className="px-2 py-0.5 rounded bg-jade-500/10 border border-jade-500/20 text-jade-400">FAISS + BM25</span>
                <ChevronRight size={10} className="text-obsidian-600" />
                <span className="px-2 py-0.5 rounded bg-obsidian-800 border border-obsidian-700">Reranker</span>
                <ChevronRight size={10} className="text-obsidian-600" />
                <span className="px-2 py-0.5 rounded bg-gold-500/10 border border-gold-500/20 text-gold-400">Gemini LLM</span>
                <ChevronRight size={10} className="text-obsidian-600" />
                <span className="text-jade-400">Javob ✓</span>
              </div>
            </div>
          </motion.div>
        </div>
      </Section>

      {/* ── CTA Section ────────────────────────────────────────────────────── */}
      <Section className="py-28 px-6 relative overflow-hidden">
        <FloatingOrb x="20%" y="20%" size={400} delay={0} />
        <FloatingOrb x="65%" y="50%" size={300} delay={1} />

        <div className="max-w-3xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="mb-8 flex justify-center"
          >
            <FinBotAvatar size={64} />
          </motion.div>

          <h2 className="font-display text-5xl md:text-6xl text-gray-100 tracking-wider mb-5">
            MOLIYAVIY <span className="gold-gradient">HUJJATLARNI</span><br />
            INTELLIGENTLASH
          </h2>
          <p className="text-sm text-obsidian-400 mb-10 max-w-lg mx-auto leading-relaxed">
            UzHack 2026 uchun ishlab chiqilgan FinBot sizning moliyaviy tahlil jarayoningizni
            bir necha daqiqadan bir necha soniyaga tushiradi.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <motion.button
              onClick={() => navigate('/app')}
              whileHover={{ scale: 1.04, boxShadow: '0 0 60px rgba(201,168,76,0.5)' }}
              whileTap={{ scale: 0.97 }}
              className="flex items-center justify-center gap-3 px-10 py-5 rounded-2xl bg-gold-500 text-obsidian-950 font-bold text-base shadow-[0_0_40px_rgba(201,168,76,0.3)] transition-all"
            >
              <Sparkles size={18} />
              FinBot-ni ishga tushirish
              <ArrowRight size={16} />
            </motion.button>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-obsidian-500">
            {['Bepul', 'Ro\'yxatdan o\'tish shart emas', 'O\'zbek tilida', 'NBU hujjatlari uchun'].map(t => (
              <span key={t} className="flex items-center gap-1.5">
                <CheckCircle2 size={11} className="text-jade-500" />
                {t}
              </span>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className="border-t border-obsidian-800 py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <FinBotAvatar size={22} />
            <span className="font-display text-sm tracking-wider text-obsidian-500">FINBOT</span>
          </div>
          <div className="text-center">
            <p className="text-xs text-obsidian-600">
              UzHack 2026 · NBU RAG Challenge · O'zbekiston
            </p>
          </div>
          <span className="text-xs text-obsidian-700 font-mono">
            bge-m3 · FAISS · BM25 · Gemini
          </span>
        </div>
      </footer>

    </div>
  )
}

// ── Hero Title — animated letter reveal ─────────────────────────────────────

function HeroTitle() {
  const line1 = "MOLIYAVIY"
  const line2 = "INTELLEKT"

  return (
    <div className="font-display tracking-wider leading-none">
      {/* Line 1 */}
      <div className="flex justify-center flex-wrap">
        {line1.split('').map((char, i) => (
          <motion.span
            key={i}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.04, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="text-5xl md:text-7xl lg:text-8xl text-gray-100"
          >
            {char === ' ' ? '\u00A0' : char}
          </motion.span>
        ))}
      </div>
      {/* Line 2 — gold animated */}
      <div className="flex justify-center flex-wrap mt-1">
        {line2.split('').map((char, i) => (
          <motion.span
            key={i}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 + i * 0.05, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="text-5xl md:text-7xl lg:text-8xl gold-gradient"
          >
            {char === ' ' ? '\u00A0' : char}
          </motion.span>
        ))}
      </div>
    </div>
  )
}

// ── Section Header ───────────────────────────────────────────────────────────

function SectionHeader({ badge, title, subtitle }: { badge: string; title: string; subtitle: string }) {
  return (
    <div className="text-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-gold-500/20 bg-gold-500/6 mb-5"
      >
        <div className="w-1 h-1 rounded-full bg-gold-500 animate-glow-pulse" />
        <span className="text-[10px] font-mono text-gold-400 uppercase tracking-widest">{badge}</span>
      </motion.div>
      <h2 className="font-display text-4xl md:text-5xl text-gray-100 tracking-wider mb-4">{title}</h2>
      <p className="text-sm text-obsidian-400 max-w-lg mx-auto">{subtitle}</p>
    </div>
  )
}

// ── Preview Card — floating UI demo ─────────────────────────────────────────

function PreviewCard() {
  const [activeIdx, setActiveIdx] = useState(0)
  const demos = [
    {
      q: "2023-yildagi sof foyda qancha bo'lgan?",
      a: "2023-yil moliyaviy hisobotiga ko'ra, sof foyda 4,821,350,000 so'm tashkil etdi, bu o'tgan yilga nisbatan 18.3% o'sishni bildiradi.",
      conf: 94, source: "annual_report_2023.pdf · p.47"
    },
    {
      q: "Tijorat banklarining umumiy aktivlari?",
      a: "2023-yil yakuni bo'yicha tijorat banklarining jami aktivlari 287 trillion so'mni tashkil qildi.",
      conf: 88, source: "nbu_stats_2023.xlsx · Jadval 3"
    },
  ]

  useEffect(() => {
    const t = setInterval(() => setActiveIdx(v => (v + 1) % demos.length), 4000)
    return () => clearInterval(t)
  }, [])

  const demo = demos[activeIdx]

  return (
    <div className="rounded-2xl border border-obsidian-700 bg-obsidian-900/95 overflow-hidden shadow-[0_40px_120px_rgba(0,0,0,0.6)] backdrop-blur-xl">
      {/* Header */}
      <div className="px-4 py-3 border-b border-obsidian-700 flex items-center gap-2">
        <div className="flex gap-1.5">
          {[0,1].map(i => <div key={i} className={`w-1.5 h-1.5 rounded-full ${i === activeIdx ? 'bg-gold-500' : 'bg-obsidian-600'} transition-all`} />)}
        </div>
        <span className="text-[10px] font-mono text-obsidian-500 ml-2">finbot · demo</span>
        <div className="ml-auto flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-jade-500 animate-pulse" />
          <span className="text-[10px] text-jade-400">Tayyor</span>
        </div>
      </div>

      {/* Query */}
      <div className="px-5 pt-4 pb-2">
        <div className="flex items-start gap-2.5">
          <Search size={13} className="text-obsidian-500 mt-0.5 shrink-0" />
          <AnimatePresence mode="wait">
            <motion.p
              key={activeIdx}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="text-sm text-gray-200"
            >
              {demo.q}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-5 h-px bg-obsidian-700" />

      {/* Answer */}
      <div className="px-5 py-4">
        <div className="flex items-center gap-2 mb-2">
          <FinBotAvatar size={16} />
          <span className="text-[10px] font-mono text-gold-400/70 uppercase tracking-wider">FinBot javobi</span>
        </div>
        <AnimatePresence mode="wait">
          <motion.p
            key={activeIdx}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-sm text-gray-300 leading-relaxed"
          >
            {demo.a}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="px-5 pb-4 flex items-center justify-between">
        <span className="text-[10px] font-mono text-obsidian-500 truncate">{demo.source}</span>
        <div className="flex items-center gap-1.5 shrink-0">
          <div className="w-16 h-1 bg-obsidian-700 rounded-full overflow-hidden">
            <motion.div
              key={activeIdx}
              initial={{ width: 0 }}
              animate={{ width: `${demo.conf}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className="h-full bg-jade-500 rounded-full"
            />
          </div>
          <span className="text-[10px] font-mono text-jade-400">{demo.conf}%</span>
        </div>
      </div>
    </div>
  )
}
