import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BarChart3, Network, TrendingUp, Users, MapPin, Shield } from 'lucide-react';
import { Button } from '../components/ui/button';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-[#0B1120]/80 border-b border-blue-500/20">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-blue-500" />
              <div>
                <h1 className="text-xl font-bold text-white">ICIOS</h1>
                <p className="text-xs text-blue-400">India Civic Intelligence OS</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                data-testid="nav-public-portal-btn"
                variant="ghost"
                className="text-white hover:text-blue-400"
                onClick={() => navigate('/public')}
              >
                Public Portal
              </Button>
              <Button
                data-testid="nav-login-btn"
                variant="outline"
                className="border-blue-500 text-blue-400 hover:bg-blue-500/10"
                onClick={() => navigate('/login')}
              >
                Sign In
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <div className="mb-6 inline-block">
            <span className="px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400 text-sm font-medium">
              National Digital Infrastructure
            </span>
          </div>
          <h1 className="text-6xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Micro-Governance
            <br />
            <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Intelligence Layer
            </span>
          </h1>
          <p className="text-xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
            AI-powered civic intelligence platform enabling hyper-local governance, 
            real-time sentiment analysis, and data-driven decision making at booth level.
          </p>
          <div className="flex items-center justify-center space-x-4">
            <Button
              data-testid="hero-dashboard-btn"
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg rounded-xl shadow-lg shadow-blue-500/30"
              onClick={() => navigate('/dashboard')}
            >
              Launch Dashboard
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button
              data-testid="hero-explore-btn"
              size="lg"
              variant="outline"
              className="border-2 border-blue-500 text-blue-400 hover:bg-blue-500/10 px-8 py-6 text-lg rounded-xl"
              onClick={() => navigate('/public')}
            >
              Explore Public Data
            </Button>
          </div>
        </div>
      </section>

      {/* Problem Statement */}
      <section className="py-20 px-6 bg-gradient-to-b from-transparent to-blue-950/20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">The Challenge</h2>
            <p className="text-gray-400 text-lg max-w-3xl mx-auto">
              India lacks hyper-local civic intelligence systems that help administrators 
              understand booth-level citizen needs, detect dissatisfaction early, and 
              prioritize micro-areas needing attention.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: MapPin, title: 'Fragmented Data', description: 'Scattered civic information across multiple systems' },
              { icon: TrendingUp, title: 'Slow Governance', description: 'Delayed response to local issues and concerns' },
              { icon: Users, title: 'Low Trust', description: 'Citizens disconnected from development initiatives' },
            ].map((item, idx) => (
              <div
                key={idx}
                className="p-6 bg-gradient-to-br from-blue-950/30 to-purple-950/20 rounded-2xl border border-blue-500/20 backdrop-blur-sm"
              >
                <item.icon className="h-12 w-12 text-blue-400 mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Core Capabilities</h2>
            <p className="text-gray-400 text-lg">AI-powered intelligence for next-generation governance</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                icon: Network,
                title: 'Knowledge Graph Intelligence',
                description: 'PostgreSQL-based relationship mapping across citizens, booths, schemes, and civic works',
                gradient: 'from-blue-500 to-cyan-500'
              },
              {
                icon: BarChart3,
                title: 'AI Citizen Segmentation',
                description: 'Hybrid demographic and ML-based clustering for targeted interventions',
                gradient: 'from-purple-500 to-pink-500'
              },
              {
                icon: TrendingUp,
                title: 'Sentiment Intelligence',
                description: 'Multilingual sentiment analysis across English, Hindi, and Marathi',
                gradient: 'from-cyan-500 to-blue-500'
              },
              {
                icon: Users,
                title: 'Influence Scoring',
                description: 'Key citizen identification using network analysis and engagement metrics',
                gradient: 'from-pink-500 to-purple-500'
              },
            ].map((feature, idx) => (
              <div
                key={idx}
                className="group p-8 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 hover:border-blue-500/50 transition-all duration-300 backdrop-blur-sm"
              >
                <div className={`inline-block p-3 bg-gradient-to-br ${feature.gradient} rounded-xl mb-4`}>
                  <feature.icon className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 px-6 bg-gradient-to-b from-blue-950/20 to-transparent">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { value: '10,000+', label: 'Citizens' },
              { value: '200', label: 'Booths' },
              { value: '5', label: 'States' },
              { value: 'Real-time', label: 'Intelligence' },
            ].map((stat, idx) => (
              <div key={idx} className="text-center">
                <div className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-2">
                  {stat.value}
                </div>
                <div className="text-gray-400 text-lg">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="p-12 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-3xl border border-blue-500/30 backdrop-blur-xl">
            <h2 className="text-4xl font-bold text-white mb-6">Ready to Transform Governance?</h2>
            <p className="text-gray-300 text-lg mb-8">Join the national civic intelligence revolution</p>
            <Button
              data-testid="cta-get-started-btn"
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-10 py-6 text-lg rounded-xl shadow-xl"
              onClick={() => navigate('/register')}
            >
              Get Started
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-blue-500/20">
        <div className="max-w-6xl mx-auto text-center text-gray-500">
          <p className="mb-2">© 2026 India Civic Intelligence OS. Built for national-scale governance.</p>
          <p className="text-sm">Powered by AI • PostgreSQL • Open Source</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;