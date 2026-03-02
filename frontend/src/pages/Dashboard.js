import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, BarChart3, Network, Home, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import api from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [boothsHealth, setBoothsHealth] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, boothsRes] = await Promise.all([
        api.get('/api/analytics/dashboard-stats'),
        api.get('/api/analytics/booth-health?limit=10')
      ]);
      setStats(statsRes.data);
      setBoothsHealth(boothsRes.data.booths);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

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

        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading intelligence data...</p>
          </div>
        ) : (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[
                { 
                  label: 'Total Citizens', 
                  value: stats?.total_citizens?.toLocaleString() || '0',
                  change: '+5.2%', 
                  positive: true,
                  icon: TrendingUp
                },
                { 
                  label: 'Active Booths', 
                  value: stats?.total_booths || '0',
                  change: '+2.1%', 
                  positive: true,
                  icon: TrendingUp
                },
                { 
                  label: 'Civic Works', 
                  value: stats?.total_civic_works || '0',
                  change: '+8.4%', 
                  positive: true,
                  icon: TrendingUp
                },
                { 
                  label: 'Avg Health Score', 
                  value: stats?.avg_health_score?.toFixed(1) || '0',
                  change: stats?.avg_health_score >= 70 ? '+2.3%' : '-1.2%',
                  positive: stats?.avg_health_score >= 70,
                  icon: stats?.avg_health_score >= 70 ? TrendingUp : TrendingDown
                },
              ].map((kpi, idx) => (
                <div
                  key={idx}
                  className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm transition-all hover:border-blue-500/40"
                  data-testid={`kpi-card-${idx}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-gray-400 text-sm">{kpi.label}</p>
                    <kpi.icon className={`h-4 w-4 ${kpi.positive ? 'text-green-400' : 'text-red-400'}`} />
                  </div>
                  <div className="flex items-end justify-between">
                    <h3 className="text-3xl font-bold text-white">{kpi.value}</h3>
                    <span className={`text-sm font-medium ${kpi.positive ? 'text-green-400' : 'text-red-400'}`}>
                      {kpi.change}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Additional Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm">
                <p className="text-gray-400 text-sm mb-2">Scheme Coverage</p>
                <h3 className="text-3xl font-bold text-white mb-2">{stats?.scheme_coverage_pct?.toFixed(1)}%</h3>
                <p className="text-sm text-gray-500">{stats?.active_beneficiaries?.toLocaleString()} active beneficiaries</p>
              </div>
              
              <div className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm">
                <p className="text-gray-400 text-sm mb-2">Open Issues</p>
                <h3 className="text-3xl font-bold text-white mb-2">{stats?.open_issues || 0}</h3>
                <p className="text-sm text-gray-500">Requiring attention</p>
              </div>
              
              <div className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm">
                <p className="text-gray-400 text-sm mb-2">Sentiment Trend</p>
                <h3 className="text-3xl font-bold text-white mb-2">
                  {stats?.sentiment_trend >= 0 ? '+' : ''}{(stats?.sentiment_trend * 100)?.toFixed(1)}%
                </h3>
                <p className="text-sm text-gray-500">
                  {stats?.sentiment_trend >= 0 ? 'Positive momentum' : 'Needs attention'}
                </p>
              </div>
            </div>

            {/* Booth Health Table */}
            <div className="bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-2xl border border-blue-500/20 backdrop-blur-sm p-6">
              <h3 className="text-xl font-bold text-white mb-6">Booth Health Intelligence</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-blue-500/20">
                      <th className="pb-3 text-gray-400 font-medium">Booth</th>
                      <th className="pb-3 text-gray-400 font-medium">Health Score</th>
                      <th className="pb-3 text-gray-400 font-medium">Risk Level</th>
                      <th className="pb-3 text-gray-400 font-medium">Citizens</th>
                      <th className="pb-3 text-gray-400 font-medium">Coverage</th>
                      <th className="pb-3 text-gray-400 font-medium">Issues</th>
                    </tr>
                  </thead>
                  <tbody>
                    {boothsHealth.map((booth, idx) => (
                      <tr key={idx} className="border-b border-blue-500/10 hover:bg-blue-950/20 transition-colors">
                        <td className="py-4 text-white font-medium">
                          {booth.booth_name}
                          <div className="text-xs text-gray-500">{booth.booth_code}</div>
                        </td>
                        <td className="py-4">
                          <div className="flex items-center">
                            <div className="text-2xl font-bold text-white mr-2">{booth.health_score}</div>
                            <div className="text-xs text-gray-400">/100</div>
                          </div>
                        </td>
                        <td className="py-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            booth.risk_level === 'Low' ? 'bg-green-500/20 text-green-400' :
                            booth.risk_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-red-500/20 text-red-400'
                          }`}>
                            {booth.risk_level === 'High' && <AlertTriangle className="inline h-3 w-3 mr-1" />}
                            {booth.risk_level}
                          </span>
                        </td>
                        <td className="py-4 text-gray-300">{booth.citizens_count}</td>
                        <td className="py-4 text-gray-300">{booth.scheme_coverage?.toFixed(1)}%</td>
                        <td className="py-4 text-gray-300">{booth.top_issues?.length || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;