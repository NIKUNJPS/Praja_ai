import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, MapPin, TrendingUp } from 'lucide-react';
import { Button } from '../components/ui/button';

const PublicPortal = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">Public Transparency Portal</h1>
          <Button variant="ghost" onClick={() => navigate('/')}>
            <Home className="h-4 w-4 mr-2 text-white" />
            <span className="text-white">Back to Home</span>
          </Button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Civic Transparency Dashboard</h2>
          <p className="text-gray-400">View local development works, scheme coverage, and ward health</p>
        </div>

        {/* Public KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            { icon: MapPin, label: 'Active Projects', value: '150', color: 'blue' },
            { icon: TrendingUp, label: 'Scheme Coverage', value: '78%', color: 'purple' },
            { icon: MapPin, label: 'Issues Resolved', value: '342', color: 'cyan' },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm"
              data-testid={`public-kpi-${idx}`}
            >
              <item.icon className={`h-10 w-10 text-${item.color}-400 mb-4`} />
              <p className="text-gray-400 text-sm mb-2">{item.label}</p>
              <h3 className="text-3xl font-bold text-white">{item.value}</h3>
            </div>
          ))}
        </div>

        <div className="p-12 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm flex items-center justify-center h-96">
          <p className="text-gray-400 text-xl">Public Data Visualization (Coming Soon)</p>
        </div>
      </div>
    </div>
  );
};

export default PublicPortal;