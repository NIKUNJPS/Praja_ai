import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Globe, Layers, LayoutGrid, FileText,
  Droplets, Construction, Siren, Megaphone,
  Activity // <--- Activity is imported here for the Navbar
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// --- Utility & Components ---
function cn(...inputs) { return twMerge(clsx(inputs)); }

const Button = React.forwardRef(({ className, variant = "default", size = "default", children, ...props }, ref) => {
  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-500/20 border border-blue-500/20",
    outline: "border border-white/10 bg-white/5 text-white hover:bg-white/10 hover:border-white/20 backdrop-blur-sm",
    glow: "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-[0_0_40px_-10px_rgba(79,70,229,0.5)] border border-white/10"
  };
  return <button ref={ref} className={cn("inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all disabled:opacity-50", variants[variant], className)} {...props}>{children}</button>;
});

const Solutions = () => {
  const navigate = useNavigate();
  // Optimization: Removed useScroll/useTransform to fix the "slow scroll" issue.
  // Using static background elements instead for 60FPS performance.
  const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.8 } } };

  return (
    <div className="min-h-screen bg-[#030712] text-slate-300 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      
      {/* Optimized Static Background (No Scroll Lag) */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-900/10 blur-[120px]" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
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
              <Link key={item.name} to={item.path} className={cn("px-4 py-2 rounded-full text-sm font-medium transition-colors", item.path === '/solutions' ? "bg-white/10 text-white" : "text-slate-400 hover:text-white hover:bg-white/5")}>
                {item.name}
              </Link>
            ))}
          </div>
          <Button variant="outline" className="h-10 px-4" onClick={() => navigate('/login')}>Sign In</Button>
        </div>
      </nav>

      <main className="relative z-10 pt-40 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-20">
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">Real Problems. <br/><span className="text-blue-500">Solved at Speed.</span></h1>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">From predicting water shortages to managing election logistics, Praja.AI is the operating system for field action.</p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                title: "Civic Infrastructure",
                problem: "Potholes and broken lights often take months to fix due to lack of reporting.",
                solution: "Praja aggregates social media complaints + IoT sensor data to auto-generate work orders.",
                icon: Construction,
                stat: "40% Faster Repair Time",
                gradient: "from-orange-500 to-red-500"
              },
              {
                title: "Water Management",
                problem: "Unequal water distribution leads to protests and tanker mafia dominance.",
                solution: "Predictive demand modeling ensures tankers are dispatched *before* shortages occur.",
                icon: Droplets,
                stat: "Zero Dry Days in Pilots",
                gradient: "from-blue-500 to-cyan-500"
              },
              {
                title: "Law & Order",
                problem: "Police are often reactive, arriving after incidents escalate.",
                solution: "Sentiment analysis of local chat groups alerts authorities to potential unrest vectors.",
                icon: Siren,
                stat: "2hr Early Warning System",
                gradient: "from-red-500 to-rose-600"
              },
              {
                title: "Public Grievance",
                problem: "Citizens feel unheard as petitions disappear into black holes.",
                solution: "Automated ticket tracking with WhatsApp updates keeps the citizen in the loop.",
                icon: Megaphone,
                stat: "92% Citizen Satisfaction",
                gradient: "from-emerald-500 to-green-500"
              }
            ].map((card, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="group relative p-8 rounded-[2rem] bg-[#080C16] border border-white/[0.05] overflow-hidden hover:border-white/20 transition-all"
              >
                <div className={`absolute top-0 right-0 w-64 h-64 bg-gradient-to-br ${card.gradient} opacity-5 group-hover:opacity-10 blur-[60px] rounded-full transition-opacity`} />
                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-6">
                    <div className="p-3 bg-white/5 rounded-xl border border-white/5"><card.icon className="w-8 h-8 text-white"/></div>
                    <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-bold text-white">{card.stat}</span>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4">{card.title}</h3>
                  <div className="space-y-4">
                    <div className="pl-4 border-l-2 border-red-500/30">
                      <p className="text-xs text-red-400 uppercase font-bold mb-1">The Problem</p>
                      <p className="text-slate-400 text-sm">{card.problem}</p>
                    </div>
                    <div className="pl-4 border-l-2 border-green-500/30">
                      <p className="text-xs text-green-400 uppercase font-bold mb-1">The Praja Solution</p>
                      <p className="text-slate-300 text-sm">{card.solution}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Solutions;