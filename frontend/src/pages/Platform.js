import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight, Shield, Globe, Layers, LayoutGrid, FileText,
  Cpu, Zap, Database, Activity // <--- Activity is kept here
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// --- Utility ---
function cn(...inputs) { return twMerge(clsx(inputs)); }

// --- Components ---
const Button = React.forwardRef(({ className, variant = "default", size = "default", children, ...props }, ref) => {
  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-500/20 border border-blue-500/20",
    outline: "border border-white/10 bg-white/5 text-white hover:bg-white/10 hover:border-white/20 backdrop-blur-sm",
    ghost: "hover:bg-white/5 text-slate-300 hover:text-white",
    glow: "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-[0_0_40px_-10px_rgba(79,70,229,0.5)] border border-white/10"
  };
  const sizes = { default: "h-10 px-4 py-2", lg: "h-14 rounded-xl px-8 text-base" };
  return (
    <button ref={ref} className={cn("inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all disabled:opacity-50", variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  );
});

// --- Animations ---
const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] } } };
const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };

const Platform = () => {
  const navigate = useNavigate();
  // Optimization: Removed useScroll/useTransform to fix slow scrolling. 
  // Using static positioning for background elements instead.

  return (
    <div className="min-h-screen bg-[#030712] text-slate-300 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      
      {/* Optimized Static Background (No Scroll Lag) */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        {/* Top Right Blob */}
        <div className="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-blue-900/10 blur-[150px]" />
        {/* Bottom Left Blob (Added for balance) */}
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-900/10 blur-[150px]" />
        
        {/* Noise Overlay */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,#000_10%,transparent_100%)]" />
      </div>

      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-[#030712]/70 border-b border-white/[0.05]">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="bg-[#0B1120] p-2 rounded-lg border border-white/10"><Globe className="h-5 w-5 text-blue-400" /></div>
            <h1 className="text-xl font-bold text-white tracking-wide">Praja<span className="text-blue-500">.AI</span></h1>
          </div>
          <div className="hidden md:flex items-center space-x-1">
             {[
                { name: 'Platform', path: '/platform', icon: Layers },
                { name: 'Solutions', path: '/solutions', icon: LayoutGrid },
                { name: 'Mission', path: '/mission', icon: Activity },
                { name: 'Resources', path: '/resources', icon: FileText },
              ].map(item => (
              <Link key={item.name} to={item.path} className={cn("px-4 py-2 rounded-full text-sm font-medium transition-colors", item.path === '/platform' ? "bg-white/10 text-white" : "text-slate-400 hover:text-white hover:bg-white/5")}>
                {item.name}
              </Link>
            ))}
          </div>
          <Button variant="outline" onClick={() => navigate('/login')}>Sign In</Button>
        </div>
      </nav>

      <main className="relative z-10 pt-40 pb-20 px-6">
        <motion.div initial="hidden" animate="visible" variants={stagger} className="max-w-7xl mx-auto">
          
          {/* Hero */}
          <div className="text-center mb-24 max-w-4xl mx-auto">
            <motion.div variants={fadeUp} className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-950/30 px-3 py-1 text-xs font-medium text-blue-300">
              <Cpu className="w-3 h-3" /> System Architecture v2.4
            </motion.div>
            <motion.h1 variants={fadeUp} className="text-5xl md:text-7xl font-bold text-white mb-8 tracking-tight">
              The <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">Neural Engine</span> <br/> of Democracy
            </motion.h1>
            <motion.p variants={fadeUp} className="text-xl text-slate-400 leading-relaxed">
              Praja.AI is built on a proprietary stack merging Large Language Models (LLMs) with geospatial graph theory.
            </motion.p>
          </div>

          {/* Architecture Grid */}
          <div className="grid md:grid-cols-3 gap-6 mb-32">
            {[
              { title: "Data Ingestion Layer", icon: Database, desc: "Connects to 50+ government APIs (UIDAI, GSTN, Census) via secure, encrypted pipelines. Normalizes unstructured data into a unified schema.", color: "text-cyan-400" },
              { title: "Sentient-7 AI Core", icon: Cpu, desc: "Our custom transformer model trained on 12 Indian languages. It detects sentiment shifts and civic unrest with 98% accuracy.", color: "text-purple-400" },
              { title: "Response Dispatch", icon: Zap, desc: "Automated workflow engine that triggers alerts to local booth officers and generates work orders for civic agencies.", color: "text-yellow-400" }
            ].map((item, i) => (
              <motion.div key={i} variants={fadeUp} className="p-8 rounded-3xl bg-[#080C16] border border-white/[0.05] hover:border-blue-500/30 transition-all group">
                <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center mb-6 border border-white/5 group-hover:bg-blue-500/10 transition-colors">
                  <item.icon className={cn("w-6 h-6", item.color)} />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
                <p className="text-slate-400 leading-relaxed text-sm">{item.desc}</p>
              </motion.div>
            ))}
          </div>

          {/* Deep Tech Section */}
          <div className="grid md:grid-cols-2 gap-16 items-center mb-32">
            <motion.div variants={fadeUp} className="relative rounded-3xl overflow-hidden border border-white/10 bg-[#0B1120] p-8 h-[400px]">
              <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10"></div>
              <div className="font-mono text-xs text-blue-300 mb-4"> // SYSTEM_LOGS: KNOWLEDGE_GRAPH</div>
              <div className="space-y-2">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-2 bg-white/10 rounded w-full animate-pulse" style={{ width: `${Math.random() * 50 + 40}%`, animationDelay: `${i * 0.1}s` }} />
                ))}
              </div>
              <div className="mt-8 grid grid-cols-2 gap-4">
                <div className="p-4 bg-black/40 rounded-xl border border-white/5">
                  <div className="text-2xl font-bold text-white">2.4ms</div>
                  <div className="text-xs text-slate-500">Query Latency</div>
                </div>
                <div className="p-4 bg-black/40 rounded-xl border border-white/5">
                  <div className="text-2xl font-bold text-green-400">AES-256</div>
                  <div className="text-xs text-slate-500">Encryption</div>
                </div>
              </div>
            </motion.div>
            
            <motion.div variants={fadeUp}>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Security First, Always.</h2>
              <p className="text-slate-400 text-lg mb-8">
                Government data requires military-grade protection. We utilize air-gapped backups, role-based access control (RBAC), and zero-trust architecture.
              </p>
              <ul className="space-y-4">
                {['End-to-End Encryption', 'ISO 27001 Certified', 'Data Sovereignty (Servers in India)'].map((item, i) => (
                  <li key={i} className="flex items-center text-slate-300">
                    <Shield className="w-5 h-5 text-green-400 mr-3" /> {item}
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>

          {/* CTA */}
          <motion.div variants={fadeUp} className="text-center py-12 border-t border-white/10">
            <h2 className="text-2xl font-bold text-white mb-6">Ready to see the specs?</h2>
             <Button variant="glow" onClick={() => window.open('mailto:engineering@praja.ai')}>Contact Engineering Team <ArrowRight className="ml-2 w-4 h-4"/></Button>
          </motion.div>

        </motion.div>
      </main>
    </div>
  );
};

export default Platform;