import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, BarChart3, Network, Home } from 'lucide-react';
import { Button } from '../components/ui/button';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      {/* Top Navigation */}
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-white">ICIOS Dashboard</h1>
            <div className="flex items-center space-x-4">
              <Button
                data-testid="nav-dashboard-btn"
                variant="ghost"
                className="text-white"
                onClick={() => navigate('/dashboard')}
              >
                <Home className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
              <Button
                data-testid="nav-analytics-btn"
                variant="ghost"
                className="text-gray-400 hover:text-white"
                onClick={() => navigate('/analytics')}
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Analytics
              </Button>
              <Button
                data-testid="nav-network-btn"
                variant="ghost"
                className="text-gray-400 hover:text-white"
                onClick={() => navigate('/network')}
              >
                <Network className="h-4 w-4 mr-2" />
                Network Graph
              </Button>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-white font-medium">{user?.name}</p>
              <p className="text-sm text-blue-400">{user?.role}</p>
            </div>
            <Button
              data-testid="logout-btn"
              variant="outline"
              size="sm"
              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Command Center</h2>
          <p className="text-gray-400">National civic intelligence overview</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[
            { label: 'Total Citizens', value: '10,000', change: '+5.2%', positive: true },
            { label: 'Active Booths', value: '200', change: '+2.1%', positive: true },
            { label: 'Civic Works', value: '150', change: '+8.4%', positive: true },
            { label: 'Avg Health Score', value: '72.5', change: '-1.2%', positive: false },
          ].map((kpi, idx) => (
            <div
              key={idx}
              className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm"
              data-testid={`kpi-card-${idx}`}
            >
              <p className="text-gray-400 text-sm mb-2">{kpi.label}</p>
              <div className="flex items-end justify-between">
                <h3 className="text-3xl font-bold text-white">{kpi.value}</h3>
                <span className={`text-sm font-medium ${kpi.positive ? 'text-green-400' : 'text-red-400'}`}>
                  {kpi.change}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Placeholder for charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-8 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm h-80 flex items-center justify-center">
            <p className="text-gray-400">Sentiment Trend Chart (Coming Soon)</p>
          </div>
          <div className="p-8 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm h-80 flex items-center justify-center">
            <p className="text-gray-400">Booth Health Heatmap (Coming Soon)</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;