import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight, Globe, Layers, LayoutGrid, FileText,
  Download, Shield, Lock, Activity // <--- Activity is now imported for the Navbar
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

const Resources = () => {
  const navigate = useNavigate();
  // Note: Removed useScroll/useTransform to fix the lag/slow scrolling issue.
  // Using static background elements instead for 60FPS performance.
  const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.8 } } };

  return (
    <div className="min-h-screen bg-[#030712] text-slate-300 font-sans selection:bg-indigo-500/30 overflow-hidden relative">
      {/* Optimized Static Background (No Scroll Lag) */}
      <div className="fixed inset-0 z-0 pointer-events-none">
         <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-900/10 blur-[120px]" />
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
                { name: 'Mission', path: '/mission', icon: Activity }, // Activity icon used here
                { name: 'Resources', path: '/resources', icon: FileText },
              ].map(item => (
              <Link key={item.name} to={item.path} className={cn("px-4 py-2 rounded-full text-sm font-medium transition-colors", item.path === '/resources' ? "bg-white/10 text-white" : "text-slate-400 hover:text-white hover:bg-white/5")}>
                {item.name}
              </Link>
            ))}
          </div>
          <Button variant="outline" className="h-10 px-4" onClick={() => navigate('/login')}>Sign In</Button>
        </div>
      </nav>

      <main className="relative z-10 pt-40 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          
          <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-16">
            <div className="inline-flex p-4 bg-blue-500/10 rounded-2xl mb-6 border border-blue-500/20">
              <FileText className="w-12 h-12 text-blue-500" />
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">Resources & Docs</h1>
            <p className="max-w-xl mx-auto text-slate-400 text-lg">
              Access technical whitepapers, API integration guides, and security compliance reports.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            transition={{ delay: 0.2 }}
            className="grid gap-4"
          >
            {[
              { name: 'Praja System Architecture v2.4.pdf', size: '2.4 MB', type: 'Technical' },
              { name: 'API Integration Guide (REST/GraphQL).pdf', size: '1.1 MB', type: 'Developer' },
              { name: 'Security & Compliance Report (ISO 27001).pdf', size: '3.8 MB', type: 'Security' },
              { name: 'Civic Data Schema Definitions.json', size: '0.4 MB', type: 'Data' },
            ].map((file, i) => (
              <motion.div 
                key={i} 
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: i * 0.1 + 0.3 }}
                className="group flex items-center justify-between p-5 bg-[#0B1120] border border-white/10 rounded-2xl hover:border-blue-500/30 hover:bg-blue-900/5 cursor-pointer transition-all duration-300"
              >
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-white/5 rounded-lg group-hover:bg-blue-500/20 transition-colors">
                    <FileText className="w-5 h-5 text-slate-400 group-hover:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-white font-medium group-hover:text-blue-300 transition-colors">{file.name}</h3>
                    <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                      <span>{file.size}</span>
                      <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                      <span className="uppercase tracking-wider">{file.type}</span>
                    </div>
                  </div>
                </div>
                <div className="p-2 rounded-full border border-white/5 hover:bg-blue-500 hover:text-white text-slate-500 transition-all">
                  <Download className="w-4 h-4" />
                </div>
              </motion.div>
            ))}
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mt-12 p-6 rounded-2xl bg-blue-900/10 border border-blue-500/20 flex flex-col sm:flex-row items-center gap-4 text-center sm:text-left"
          >
            <div className="p-3 bg-blue-500/20 rounded-full shrink-0">
               <Shield className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h4 className="text-white font-bold text-sm">Restricted Access</h4>
              <p className="text-slate-400 text-xs mt-1">Full database schemas and sensitive government reports require Officer-level authentication.</p>
            </div>
            <button onClick={() => navigate('/login')} className="sm:ml-auto px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors whitespace-nowrap">
              Login to Access
            </button>
          </motion.div>

        </div>
      </main>
    </div>
  );
};

export default Resources;