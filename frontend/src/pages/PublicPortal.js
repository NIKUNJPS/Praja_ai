import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, MapPin, TrendingUp, Wrench, Users, Heart, AlertTriangle, Clock } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';

const PublicPortal = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalCitizens: 12450,
    totalBooths: 47,
    activeProjects: 156,
    resolvedIssues: 342,
    schemeCoverage: 78,
    avgHealthScore: 68.5,
  });

  // Demo data – in production, fetch from public API
  const recentWorks = [
    { id: 1, title: 'Road Construction - Sector 12', booth: 'Booth A', status: 'In Progress', date: '2026-02-15' },
    { id: 2, title: 'Water Supply Upgrade', booth: 'Booth B', status: 'Completed', date: '2026-02-10' },
    { id: 3, title: 'Street Lighting - Main Road', booth: 'Booth C', status: 'Planned', date: '2026-02-05' },
    { id: 4, title: 'Park Development', booth: 'Booth A', status: 'In Progress', date: '2026-02-01' },
    { id: 5, title: 'Drainage Repair', booth: 'Booth D', status: 'Completed', date: '2026-01-28' },
  ];

  const boothHealth = [
    { name: 'Booth A', health: 82, risk: 'Low' },
    { name: 'Booth B', health: 67, risk: 'Medium' },
    { name: 'Booth C', health: 45, risk: 'High' },
    { name: 'Booth D', health: 91, risk: 'Low' },
    { name: 'Booth E', health: 58, risk: 'Medium' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      {/* Navigation */}
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Public Transparency Portal</h1>
            <p className="text-sm text-blue-400">Open data from India Civic Intelligence OS</p>
          </div>
          <Button variant="ghost" onClick={() => navigate('/')}>
            <Home className="h-4 w-4 mr-2 text-white" />
            <span className="text-white">Back to Home</span>
          </Button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Civic Transparency Dashboard</h2>
          <p className="text-gray-400">Real‑time data on development works, scheme coverage, and booth health</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Citizens</p>
                <p className="text-3xl font-bold text-white">{stats.totalCitizens.toLocaleString()}</p>
              </div>
              <Users className="h-10 w-10 text-blue-400" />
            </div>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Booths</p>
                <p className="text-3xl font-bold text-white">{stats.totalBooths}</p>
              </div>
              <MapPin className="h-10 w-10 text-green-400" />
            </div>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Active Projects</p>
                <p className="text-3xl font-bold text-white">{stats.activeProjects}</p>
              </div>
              <Wrench className="h-10 w-10 text-yellow-400" />
            </div>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Avg Health Score</p>
                <p className="text-3xl font-bold text-white">{stats.avgHealthScore}</p>
              </div>
              <Heart className="h-10 w-10 text-red-400" />
            </div>
          </Card>
        </div>

        {/* Two‑column layout: Recent Works & Booth Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Civic Works */}
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <Clock className="h-5 w-5 mr-2 text-blue-400" />
              Recent Civic Works
            </h3>
            <div className="space-y-3">
              {recentWorks.map((work) => (
                <div key={work.id} className="flex items-center justify-between p-3 bg-[#1E293B] rounded-lg">
                  <div>
                    <p className="text-white font-medium">{work.title}</p>
                    <p className="text-xs text-gray-400">{work.booth} • {work.date}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    work.status === 'Completed' ? 'bg-green-500/20 text-green-400' :
                    work.status === 'In Progress' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>
                    {work.status}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Booth Health Summary */}
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <Heart className="h-5 w-5 mr-2 text-red-400" />
              Booth Health Summary
            </h3>
            <div className="space-y-3">
              {boothHealth.map((booth, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-[#1E293B] rounded-lg">
                  <span className="text-white font-medium">{booth.name}</span>
                  <div className="flex items-center space-x-3">
                    <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${
                          booth.health >= 70 ? 'bg-green-500' :
                          booth.health >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${booth.health}%` }}
                      />
                    </div>
                    <span className="text-white font-mono text-sm">{booth.health}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      booth.risk === 'Low' ? 'bg-green-500/20 text-green-400' :
                      booth.risk === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {booth.risk}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Additional Public Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30 text-center">
            <div className="mb-3 inline-block p-3 bg-blue-500/20 rounded-full">
              <TrendingUp className="h-6 w-6 text-blue-400" />
            </div>
            <p className="text-gray-400 text-sm">Scheme Coverage</p>
            <p className="text-4xl font-bold text-white">{stats.schemeCoverage}%</p>
            <p className="text-xs text-gray-500 mt-2">of eligible citizens enrolled</p>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30 text-center">
            <div className="mb-3 inline-block p-3 bg-green-500/20 rounded-full">
              <AlertTriangle className="h-6 w-6 text-green-400" />
            </div>
            <p className="text-gray-400 text-sm">Resolved Issues</p>
            <p className="text-4xl font-bold text-white">{stats.resolvedIssues}</p>
            <p className="text-xs text-gray-500 mt-2">in the last 30 days</p>
          </Card>
          <Card className="p-6 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/30 text-center">
            <div className="mb-3 inline-block p-3 bg-purple-500/20 rounded-full">
              <Users className="h-6 w-6 text-purple-400" />
            </div>
            <p className="text-gray-400 text-sm">Active Beneficiaries</p>
            <p className="text-4xl font-bold text-white">8,234</p>
            <p className="text-xs text-gray-500 mt-2">across all schemes</p>
          </Card>
        </div>

        {/* Note about data update */}
        <div className="text-center text-gray-500 text-sm border-t border-blue-500/20 pt-6">
          Data updates every 24 hours. For real‑time access, please log in.
        </div>
      </div>
    </div>
  );
};

export default PublicPortal;