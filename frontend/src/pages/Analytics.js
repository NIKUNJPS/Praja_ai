import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home } from 'lucide-react';
import { Button } from '../components/ui/button';

const Analytics = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <Button variant="ghost" onClick={() => navigate('/dashboard')}>
            <Home className="h-4 w-4 mr-2 text-white" />
            <span className="text-white">Back to Dashboard</span>
          </Button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <h2 className="text-3xl font-bold text-white mb-8">Advanced Analytics</h2>
        <div className="p-12 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm flex items-center justify-center">
          <p className="text-gray-400 text-xl">Analytics Dashboard (Coming Soon)</p>
        </div>
      </div>
    </div>
  );
};

export default Analytics;