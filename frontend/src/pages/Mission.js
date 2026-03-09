import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Globe, Layers, LayoutGrid, FileText,
  Flag, Heart, Users, Target, Activity // <--- Kept Activity import for Navbar
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
  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-14 rounded-xl px-8 text-base",
    icon: "h-10 w-10",
  };
  return (
    <button 
      ref={ref} 
      className={cn("inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all disabled:opacity-50", variants[variant], sizes[size], className)} 
      {...props}
    >
      {children}
    </button>
  );
});

const Mission = () => {
  const navigate = useNavigate();
  // Optimization: Removed scroll listeners for background. Using static background for 60FPS.
  
  return (
    <div className="min-h-screen bg-[#030712] text-slate-300 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      
      {/* Optimized Static Background (Prevents scrolling lag) */}
      <div className="fixed inset-0 z-0 pointer-events-none">
         <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-900/10 blur-[120px]" />
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
              <Link key={item.name} to={item.path} className={cn("px-4 py-2 rounded-full text-sm font-medium transition-colors", item.path === '/mission' ? "bg-white/10 text-white" : "text-slate-400 hover:text-white hover:bg-white/5")}>
                {item.name}
              </Link>
            ))}
          </div>
          <Button variant="outline" className="h-10 px-4" onClick={() => navigate('/login')}>Sign In</Button>
        </div>
      </nav>

      <main className="relative z-10 pt-40 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8 }}>
             <h1 className="text-5xl md:text-8xl font-bold text-white mb-8 tracking-tighter leading-tight">
               Digital <br/> Sovereignty
             </h1>
             <p className="text-2xl text-slate-400 leading-relaxed mb-16">
               We are building the digital nervous system for the world's largest democracy. 
               Not to control, but to <span className="text-white font-bold border-b-2 border-blue-500">empower</span>.
             </p>
          </motion.div>

          {/* Manifesto Grid */}
          <div className="grid md:grid-cols-2 gap-4 text-left">
            {[
              { title: "Indigenously Built", text: "Built in India, for India. No foreign dependencies. Data stays on Indian soil.", icon: Flag },
              { title: "Citizen First", text: "Technology is useless if it doesn't solve the hunger of the poor or the safety of the weak.", icon: Heart },
              { title: "Radical Transparency", text: "Bringing data out of dusty files and into the hands of decision makers instantly.", icon: Target },
              { title: "Scale Ready", text: "Engineered to handle 1.4 Billion citizens and millions of concurrent requests.", icon: Users },
            ].map((item, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, y: 20 }} 
                whileInView={{ opacity: 1, y: 0 }} 
                transition={{ delay: i * 0.1 }}
                className="p-8 bg-white/[0.02] border border-white/[0.05] rounded-3xl hover:bg-white/[0.04] transition-colors"
              >
                <item.icon className="w-8 h-8 text-blue-500 mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">{item.title}</h3>
                <p className="text-slate-400">{item.text}</p>
              </motion.div>
            ))}
          </div>

          <div className="mt-24 p-8 border border-white/10 rounded-3xl bg-gradient-to-br from-blue-900/20 to-transparent">
             <h2 className="text-2xl font-bold text-white mb-4">Join the Movement</h2>
             <p className="text-slate-400 mb-8">We are hiring engineers, sociologists, and data scientists.</p>
             <Button variant="glow" size="lg" onClick={() => window.location.href='/careers'}>View Open Roles</Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Mission;