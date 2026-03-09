import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  motion, 
  useScroll, 
  useTransform, 
  useInView, 
  useSpring, 
  useMotionValue 
} from 'framer-motion';
import {
  ArrowRight, BrainCircuit, Activity, Zap, Users,
  LayoutGrid, Layers, FileText,
  // --- ADDED MISSING IMPORTS HERE: ---
  MessageSquare, GitGraph 
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// --- Utility: Class Merger ---
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// --- Utility: Animated Counter Component ---
const Counter = ({ value, suffix = "" }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, { damping: 30, stiffness: 100 });
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    if (isInView) {
      motionValue.set(value);
    }
  }, [isInView, value, motionValue]);

  useEffect(() => {
    return springValue.on("change", (latest) => {
      setDisplayValue(Math.floor(latest));
    });
  }, [springValue]);

  return (
    <span ref={ref} className="tabular-nums">
      {displayValue.toLocaleString()}{suffix}
    </span>
  );
};

// --- Component: Custom Button ---
const Button = React.forwardRef(({ className, variant = "default", size = "default", children, ...props }, ref) => {
  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-500 shadow-[0_0_20px_-5px_rgba(37,99,235,0.4)] border border-blue-500/20",
    outline: "border border-white/10 bg-white/5 text-white hover:bg-white/10 hover:border-white/20 backdrop-blur-sm",
    ghost: "hover:bg-white/5 text-slate-300 hover:text-white",
    glow: "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-[0_0_40px_-10px_rgba(79,70,229,0.5)] hover:shadow-[0_0_60px_-10px_rgba(79,70,229,0.6)] border border-white/10"
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
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
});
Button.displayName = "Button";

// --- Animation Variants ---
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.1 }
  }
};

const Landing = () => {
  const navigate = useNavigate();
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, -50]);

  return (
    <div className="min-h-screen bg-[#030712] text-slate-300 font-sans selection:bg-indigo-500/30 selection:text-indigo-200 overflow-hidden relative">
      
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <motion.div 
          style={{ y }}
          className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-blue-900/10 blur-[150px]" 
        />
        <motion.div 
          style={{ y: useTransform(scrollYProgress, [0, 1], [0, 50]) }}
          className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-900/10 blur-[150px]" 
        />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay"></div>
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,#000_10%,transparent_100%)]" />
      </div>

      {/* --- NAVBAR --- */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-[#030712]/70 border-b border-white/[0.05] shadow-2xl shadow-black/20">
        <div className="max-w-7xl mx-auto px-6 h-20"> 
          <div className="flex items-center justify-between h-full">
            
            {/* 1. Left: Logo Section (NAVBAR LOGO) */}
            <div 
              className="flex items-center space-x-3 group cursor-pointer" 
              onClick={() => navigate('/')}
            >
              <div className="relative h-10 w-10 flex items-center justify-center">
                 <div className="absolute inset-0 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl opacity-20 group-hover:opacity-100 transition-opacity duration-300 blur-lg"></div>
                 <div className="relative bg-[#0B1120] p-1.5 rounded-lg border border-white/10 group-hover:border-white/20 transition-colors h-10 w-10 flex items-center justify-center">
                   {/* IMAGE LOGO ADDED HERE */}
                   <img src="/logo.png" alt="Praja.AI Logo" className="h-full w-full object-contain" />
                 </div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-wide font-display">
                  Praja<span className="text-blue-500">.AI</span>
                </h1>
              </div>
            </div>

            {/* 2. Center: Main Navigation */}
            <div className="hidden md:flex items-center justify-center space-x-1">
              {[
                { name: 'Platform', path: '/platform', icon: Layers },
                { name: 'Solutions', path: '/solutions', icon: LayoutGrid },
                { name: 'Mission', path: '/mission', icon: Activity },
                { name: 'Resources', path: '/resources', icon: FileText },
              ].map((item) => (
                <Link 
                  key={item.name}
                  to={item.path} 
                  className="group relative px-4 py-2 rounded-full hover:bg-white/5 transition-all duration-200 flex items-center space-x-2"
                >
                  <span className="text-sm font-medium text-slate-400 group-hover:text-white transition-colors">
                    {item.name}
                  </span>
                </Link>
              ))}
            </div>

            {/* 3. Right: Action Buttons */}
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                className="hidden lg:flex text-slate-400 hover:text-white"
                onClick={() => navigate('/public')}
              >
                Public Data
              </Button>
              <Button
                variant="outline"
                className="border-blue-500/20 text-blue-400 hover:bg-blue-500/10 hover:text-blue-300"
                onClick={() => navigate('/login')}
              >
                Sign In
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="relative z-10">
        {/* Hero Section */}
        <section className="pt-48 pb-32 px-6 min-h-[90vh] flex flex-col justify-center relative overflow-hidden">
           <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-blue-500/20 blur-[120px] rounded-full opacity-50 pointer-events-none mix-blend-screen" />

          <motion.div 
            initial="hidden" 
            animate="visible" 
            variants={staggerContainer}
            className="max-w-6xl mx-auto text-center relative z-10"
          >
            <motion.div variants={fadeUp} className="mb-8 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-950/30 px-4 py-1.5 text-sm font-medium text-blue-300 backdrop-blur-md hover:bg-blue-900/40 transition-colors cursor-default">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              Operating System for New India
            </motion.div>
            
            <motion.h1 variants={fadeUp} className="text-6xl md:text-7xl lg:text-9xl font-bold text-white mb-8 tracking-tighter leading-[1] font-display">
              <span className="block text-slate-400 text-4xl md:text-6xl lg:text-7xl mb-2 font-medium tracking-normal">The Future of</span>
              <span className="text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-blue-300 drop-shadow-2xl">
                Governance
              </span>
            </motion.h1>
            
            <motion.p variants={fadeUp} className="text-lg md:text-2xl text-slate-400 mb-12 max-w-3xl mx-auto leading-relaxed">
              Praja.AI transforms fragmented civic data into 
              <span className="text-white font-medium"> hyper-local intelligence</span>. 
              Real-time sentiment, predictive resource allocation, and booth-level analytics.
            </motion.p>
            
            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center justify-center gap-5">
              <Button
                variant="glow"
                size="lg"
                className="w-full sm:w-auto h-16 px-10 text-lg shadow-[0_0_50px_-12px_rgba(59,130,246,0.6)]"
                onClick={() => navigate('/dashboard')}
              >
                Launch Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="w-full sm:w-auto h-16 px-10 text-lg bg-transparent border-white/20 hover:bg-white/5"
                onClick={() => navigate('/public')}
              >
                Explore Public Data
              </Button>
            </motion.div>
          </motion.div>
        </section>

        {/* Stats Section */}
        <section className="py-24 border-y border-white/[0.05] bg-white/[0.01]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-12 text-center divide-x divide-white/[0.05]">
              {[
                { value: 12000000, suffix: '+', label: 'Citizens Analyzed', icon: Users },
                { value: 4500, suffix: '', label: 'Booths Monitored', icon: Activity },
                { value: 98, suffix: '%', label: 'Sentiment Accuracy', icon: BrainCircuit },
                { value: 24, suffix: '/7', label: 'Real-time Updates', icon: Zap },
              ].map((stat, idx) => (
                <div key={idx} className="flex flex-col items-center">
                  <div className="mb-4 p-3 bg-blue-500/10 rounded-2xl text-blue-400 ring-1 ring-blue-500/20">
                    <stat.icon size={24} />
                  </div>
                  <div className="text-4xl md:text-5xl font-bold text-white mb-2 tabular-nums tracking-tight">
                    <Counter value={stat.value} suffix={stat.suffix} />
                  </div>
                  <div className="text-sm text-slate-500 uppercase tracking-widest font-semibold">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Preview */}
        <section className="py-32 px-6 relative">
          <motion.div 
            initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="max-w-7xl mx-auto"
          >
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-20">
              <motion.div variants={fadeUp} className="md:w-1/2">
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">Omniscient Intelligence</h2>
                <p className="text-slate-400 text-xl leading-relaxed">
                  Our proprietary AI models process millions of data points to generate a composite "Health Score" for every booth.
                </p>
              </motion.div>
              <motion.div variants={fadeUp} className="hidden md:block">
                <Button variant="outline" onClick={() => navigate('/platform')}>View Platform Specs <ArrowRight className="ml-2 w-4 h-4"/></Button>
              </motion.div>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: BrainCircuit, title: 'Neural Health Scoring', desc: 'Composite 0-100 score combining sentiment, scheme saturation, and local demands.', gradient: 'from-blue-500 to-cyan-500' },
                { icon: MessageSquare, title: 'Linguistic AI', desc: 'Offline transformer models processing Hindi, Marathi, & English sentiment in real-time.', gradient: 'from-violet-500 to-purple-500' },
                { icon: GitGraph, title: 'Influence Mapping', desc: 'Graph theory analysis to identify key influencers and community nodes within booths.', gradient: 'from-pink-500 to-rose-500' },
              ].map((feature, idx) => (
                <motion.div 
                  key={idx} 
                  variants={fadeUp} 
                  className="group relative p-8 rounded-3xl bg-[#080C16] border border-white/[0.05] hover:border-white/[0.1] transition-all duration-500 overflow-hidden hover:-translate-y-1"
                >
                  <div className={`absolute top-0 right-0 w-[300px] h-[300px] bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 blur-[80px] rounded-full transition-opacity duration-700`} />
                  
                  <div className="relative z-10">
                    <div className={`inline-flex p-3 rounded-xl mb-6 bg-gradient-to-br ${feature.gradient} bg-opacity-10 ring-1 ring-white/10`}>
                      <feature.icon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3 tracking-wide">{feature.title}</h3>
                    <p className="text-slate-400 text-sm leading-7">{feature.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
            
            <motion.div variants={fadeUp} className="mt-12 text-center md:hidden">
                <Button variant="outline" className="w-full" onClick={() => navigate('/platform')}>View Platform Specs</Button>
            </motion.div>
          </motion.div>
        </section>

        {/* CTA */}
        <section className="py-32 px-6 relative">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="max-w-5xl mx-auto rounded-[2.5rem] bg-gradient-to-b from-blue-900/20 to-indigo-900/20 border border-blue-500/30 p-12 md:p-24 text-center relative overflow-hidden"
          >
             <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10"></div>
             
             <div className="relative z-10">
              <h2 className="text-4xl md:text-6xl font-bold text-white mb-8 tracking-tight">Ready to Deploy?</h2>
              <p className="text-slate-300 text-xl mb-12 max-w-2xl mx-auto">
                Join the network of modern administrators using Praja.AI to build responsive, resilient communities.
              </p>
              
              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <Button
                  variant="default"
                  size="lg"
                  className="bg-white text-black hover:bg-slate-200 border-none h-14 px-8 text-lg font-bold"
                  onClick={() => navigate('/register')}
                >
                  Request Access
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  className="h-14 px-8 text-lg"
                  onClick={() => window.open('mailto:sales@praja.ai')}
                >
                  Contact Sales
                </Button>
              </div>
            </div>
          </motion.div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/[0.05] bg-[#020408] pt-20 pb-10 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-start gap-10 mb-16">
            <div>
              <div className="flex items-center space-x-2 mb-6">
                <div className="h-10 w-10 p-1.5 bg-blue-600 rounded-lg flex items-center justify-center">
                   {/* FOOTER LOGO ADDED HERE */}
                   <img src="/logo.png" alt="Praja.AI Logo" className="h-full w-full object-contain filter brightness-0 invert" />
                </div>
                <span className="text-2xl font-bold text-white tracking-wide">Praja.AI</span>
              </div>
              <p className="text-slate-500 max-w-xs">
                The operating system for next-generation civic intelligence and governance.
              </p>
            </div>
            
            <div className="flex gap-16 text-sm">
              <div className="flex flex-col gap-4">
                <h4 className="font-bold text-white">Platform</h4>
                <Link to="/platform" className="text-slate-500 hover:text-blue-400 transition-colors">Intelligence</Link>
                <Link to="/solutions" className="text-slate-500 hover:text-blue-400 transition-colors">Data Lake</Link>
                <Link to="/resources" className="text-slate-500 hover:text-blue-400 transition-colors">Security</Link>
              </div>
              <div className="flex flex-col gap-4">
                <h4 className="font-bold text-white">Company</h4>
                <Link to="/mission" className="text-slate-500 hover:text-blue-400 transition-colors">Mission</Link>
                <a href="#" className="text-slate-500 hover:text-blue-400 transition-colors">Careers</a>
                <a href="#" className="text-slate-500 hover:text-blue-400 transition-colors">Contact</a>
              </div>
            </div>
          </div>
          
          <div className="pt-8 border-t border-white/[0.05] flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-slate-600">
            <div>© {new Date().getFullYear()} Praja.AI Systems Inc. All rights reserved.</div>
            <div className="flex gap-6">
              <a href="#" className="hover:text-slate-400">Privacy Policy</a>
              <a href="#" className="hover:text-slate-400">Terms of Service</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;