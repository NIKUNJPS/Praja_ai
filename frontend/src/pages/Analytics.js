import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, Users, MapPin, Wrench, TrendingUp, AlertTriangle, Heart, Award } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import api from '../services/api';
import { useToast } from '../hooks/use-toast';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['#3B82F6', '#EC4899', '#F59E0B', '#10B981', '#A855F7', '#EF4444'];

const Analytics = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [boothHealth, setBoothHealth] = useState([]);
  const [sentimentTrends, setSentimentTrends] = useState(null);
  const [topInfluencers, setTopInfluencers] = useState([]);
  const [segmentDistribution, setSegmentDistribution] = useState([]);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, boothRes, sentimentRes, influencersRes, segmentsRes] = await Promise.all([
        api.get('/analytics/dashboard-stats'),
        api.get('/analytics/booth-health?limit=10'),
        api.get('/analytics/sentiment-trends?days=30'),
        api.get('/analytics/top-influencers?limit=10'),
        api.get('/analytics/segments-distribution'),
      ]);

      setDashboardStats(statsRes.data);
      setBoothHealth(boothRes.data.booths || []);
      setSentimentTrends(sentimentRes.data);
      setTopInfluencers(influencersRes.data.influencers || []);
      setSegmentDistribution(segmentsRes.data.segments || []);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setError('Failed to load analytics data. Please try again later.');
      toast({
        title: 'Error',
        description: 'Could not fetch analytics data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-300 text-lg">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B] flex items-center justify-center">
        <Card className="p-8 bg-red-950/40 border-red-500/30 text-center">
          <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <p className="text-red-400 text-lg mb-4">{error}</p>
          <Button onClick={fetchAllData}>Retry</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
          <Button variant="ghost" onClick={() => navigate('/dashboard')}>
            <Home className="h-4 w-4 mr-2 text-white" />
            <span className="text-white">Back to Dashboard</span>
          </Button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Summary Cards */}
        {dashboardStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Citizens</p>
                  <p className="text-3xl font-bold text-white">{dashboardStats.total_citizens.toLocaleString()}</p>
                </div>
                <Users className="h-10 w-10 text-blue-400" />
              </div>
            </Card>
            <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Booths</p>
                  <p className="text-3xl font-bold text-white">{dashboardStats.total_booths.toLocaleString()}</p>
                </div>
                <MapPin className="h-10 w-10 text-green-400" />
              </div>
            </Card>
            <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Civic Works</p>
                  <p className="text-3xl font-bold text-white">{dashboardStats.total_civic_works.toLocaleString()}</p>
                </div>
                <Wrench className="h-10 w-10 text-yellow-400" />
              </div>
            </Card>
            <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Avg Health Score</p>
                  <p className="text-3xl font-bold text-white">{dashboardStats.avg_health_score.toFixed(1)}</p>
                </div>
                <Heart className="h-10 w-10 text-red-400" />
              </div>
            </Card>
          </div>
        )}

        {/* Booth Health Chart */}
        <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
          <h2 className="text-xl font-bold text-white mb-4">Booth Health Scores (Top 10)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={boothHealth}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="booth_name" tick={{ fill: '#9CA3AF' }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#9CA3AF' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1E293B', borderColor: '#3B82F6' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="health_score" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Two-column layout: Sentiment trends & Segment distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sentiment Trends */}
          {sentimentTrends && (
            <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
              <h2 className="text-xl font-bold text-white mb-4">Sentiment Trends (Last 30 Days)</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Total Logs</span>
                  <span className="text-white font-bold">{sentimentTrends.total_logs}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Average Score</span>
                  <span className="text-white font-bold">{sentimentTrends.avg_sentiment_score?.toFixed(3)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Momentum</span>
                  <span className={`font-bold ${
                    sentimentTrends.momentum === 'positive' ? 'text-green-400' :
                    sentimentTrends.momentum === 'negative' ? 'text-red-400' : 'text-yellow-400'
                  }`}>
                    {sentimentTrends.momentum?.toUpperCase()}
                  </span>
                </div>
                {sentimentTrends.sentiment_counts && (
                  <div className="grid grid-cols-3 gap-2 mt-4">
                    <div className="text-center p-2 bg-green-500/10 rounded">
                      <div className="text-green-400 text-lg font-bold">{sentimentTrends.sentiment_counts.Positive || 0}</div>
                      <div className="text-gray-400 text-xs">Positive</div>
                    </div>
                    <div className="text-center p-2 bg-yellow-500/10 rounded">
                      <div className="text-yellow-400 text-lg font-bold">{sentimentTrends.sentiment_counts.Neutral || 0}</div>
                      <div className="text-gray-400 text-xs">Neutral</div>
                    </div>
                    <div className="text-center p-2 bg-red-500/10 rounded">
                      <div className="text-red-400 text-lg font-bold">{sentimentTrends.sentiment_counts.Negative || 0}</div>
                      <div className="text-gray-400 text-xs">Negative</div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Segment Distribution */}
          {segmentDistribution.length > 0 && (
            <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
              <h2 className="text-xl font-bold text-white mb-4">Citizen Segments</h2>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={segmentDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {segmentDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1E293B', borderColor: '#3B82F6' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>

        {/* Top Influencers Table */}
        {topInfluencers.length > 0 && (
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
            <h2 className="text-xl font-bold text-white mb-4">Top Influencers</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-blue-500/20">
                    <th className="pb-3 text-gray-400 font-medium">Name</th>
                    <th className="pb-3 text-gray-400 font-medium">Booth</th>
                    <th className="pb-3 text-gray-400 font-medium">Score</th>
                    <th className="pb-3 text-gray-400 font-medium">Rank</th>
                    <th className="pb-3 text-gray-400 font-medium">Occupation</th>
                  </tr>
                </thead>
                <tbody>
                  {topInfluencers.map((inf) => (
                    <tr key={inf.citizen_id} className="border-b border-blue-500/10">
                      <td className="py-3 text-white">{inf.name}</td>
                      <td className="py-3 text-gray-300">{inf.booth_name}</td>
                      <td className="py-3 text-white font-mono">{inf.influence_score.toFixed(2)}</td>
                      <td className="py-3 text-white">#{inf.influence_rank}</td>
                      <td className="py-3 text-gray-300">{inf.occupation || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Analytics;