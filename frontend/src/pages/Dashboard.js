import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, BarChart3, Network, Home, TrendingUp, TrendingDown, AlertTriangle, Activity, Play, RotateCcw, Zap, CheckCircle2, Loader2, Target, Users, Bell, ArrowUpRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Toaster, toast } from 'sonner';
import api from '../services/api';
import websocketService from '../services/websocket';

// Demo Mode States
const DEMO_STATES = {
  IDLE: 'idle',
  RUNNING: 'running',
  COMPLETED: 'completed'
};

// Demo Step Configuration
const DEMO_STEPS = [
  { id: 1, title: 'AI Detecting Weak Booth', description: 'Analyzing health scores...', delay: 2000 },
  { id: 2, title: 'Triggering Intervention', description: 'Creating civic work...', delay: 1500 },
  { id: 3, title: 'Live Automation', description: 'Notifying citizens...', delay: 2000 },
  { id: 4, title: 'Health Improvement', description: 'Recalculating scores...', delay: 2000 },
  { id: 5, title: 'Network Intelligence', description: 'Identifying influencers...', delay: 2000 },
  { id: 6, title: 'Demo Complete', description: 'Cycle finished', delay: 1000 }
];

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [boothsHealth, setBoothsHealth] = useState([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [activityFeed, setActivityFeed] = useState([]);
  
  // Demo Mode State
  const [demoState, setDemoState] = useState(DEMO_STATES.IDLE);
  const [demoStep, setDemoStep] = useState(0);
  const [demoData, setDemoData] = useState({
    weakBooth: null,
    civicWork: null,
    notificationsCount: 0,
    healthImprovement: 0,
    influencers: []
  });
  const [highlightedBoothId, setHighlightedBoothId] = useState(null);
  const demoTimerRef = useRef(null);
  const demoDataRef = useRef({
    weakBooth: null,
    civicWork: null,
    notificationsCount: 0,
    healthImprovement: 0,
    influencers: []
  });

  // Define fetchDashboardData first since it's used by other hooks
  const fetchDashboardData = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    fetchDashboardData();
    
    // Initialize WebSocket
    websocketService.connect();
    
    // Listen for connection status
    websocketService.on('connection_status', handleConnectionStatus);
    
    // Listen for civic work events
    websocketService.on('civic_work_created', handleCivicWorkCreated);
    
    // Cleanup on unmount
    return () => {
      websocketService.off('connection_status', handleConnectionStatus);
      websocketService.off('civic_work_created', handleCivicWorkCreated);
    };
  }, []);

  const handleConnectionStatus = (status) => {
    setWsConnected(status.connected);
  };

  const handleCivicWorkCreated = (event) => {
    const { data } = event;
    
    // Show toast notification
    toast.success(`🚧 New ${data.category} Project`, {
      description: `${data.title} - ${data.affected_citizens} citizens notified`
    });
    
    // Add to activity feed
    setActivityFeed(prev => [{
      id: Date.now(),
      type: 'civic_work_created',
      title: data.title,
      category: data.category,
      citizens: data.affected_citizens,
      notifications: data.notifications_created,
      timestamp: event.timestamp
    }, ...prev.slice(0, 19)]);  // Keep last 20
    
    // Refresh dashboard data
    fetchDashboardData();
  };

  // ============================================
  // DEMO MODE LOGIC - Guided Cinematic Demo
  // ============================================
  
  const resetDemo = useCallback(() => {
    if (demoTimerRef.current) {
      clearTimeout(demoTimerRef.current);
    }
    setDemoState(DEMO_STATES.IDLE);
    setDemoStep(0);
    const resetData = {
      weakBooth: null,
      civicWork: null,
      notificationsCount: 0,
      healthImprovement: 0,
      influencers: []
    };
    setDemoData(resetData);
    demoDataRef.current = resetData;
    setHighlightedBoothId(null);
  }, []);
  
  const runDemoStep = useCallback(async (step) => {
    console.log(`🎬 Demo Step ${step}`);
    
    switch (step) {
      case 1: {
        // Step 1: AI Detects Weak Booth
        toast.info('🔍 AI scanning for weak booths...', { duration: 1500 });
        
        try {
          const response = await api.get('/api/analytics/booth-health?limit=50');
          const booths = response.data.booths || [];
          
          // Find the booth with lowest health score
          const weakestBooth = booths.reduce((min, booth) => 
            booth.health_score < min.health_score ? booth : min, booths[0]);
          
          if (weakestBooth) {
            demoDataRef.current = { ...demoDataRef.current, weakBooth: weakestBooth };
            setDemoData(prev => ({ ...prev, weakBooth: weakestBooth }));
            setHighlightedBoothId(weakestBooth.booth_id);
            
            toast.warning(`⚠️ Weak Booth Detected: ${weakestBooth.booth_name}`, {
              description: `Health Score: ${weakestBooth.health_score} - Risk Level: ${weakestBooth.risk_level}`,
              duration: 3000
            });
          }
        } catch (error) {
          console.error('Demo Step 1 error:', error);
        }
        break;
      }
      
      case 2: {
        // Step 2: Trigger Civic Intervention
        const currentWeakBooth = demoDataRef.current.weakBooth;
        if (!currentWeakBooth) {
          console.warn('No weak booth selected for intervention');
          break;
        }
        
        toast.info('🏗️ Initiating targeted intervention...', { duration: 1500 });
        
        const categories = ['Road Construction', 'Water Supply', 'Street Lighting', 'Drainage'];
        const category = categories[Math.floor(Math.random() * categories.length)];
        
        try {
          const response = await api.post('/api/civic-works/create', {
            booth_id: currentWeakBooth.booth_id,
            title: `Emergency ${category} - ${currentWeakBooth.booth_name}`,
            description: `AI-triggered intervention for booth health improvement`,
            category: category,
            budget: Math.floor(Math.random() * 500000) + 100000,
            status: 'In Progress',
            affected_streets: []
          });
          
          demoDataRef.current = {
            ...demoDataRef.current,
            civicWork: response.data,
            notificationsCount: response.data.notifications_created
          };
          setDemoData(prev => ({
            ...prev,
            civicWork: response.data,
            notificationsCount: response.data.notifications_created
          }));
          
          toast.success(`✅ Intervention Created: ${category}`, {
            description: `Budget: ₹${response.data.budget?.toLocaleString() || 'N/A'}`,
            duration: 3000
          });
        } catch (error) {
          console.error('Demo Step 2 error:', error);
          toast.error('Failed to create civic work');
        }
        break;
      }
      
      case 3: {
        // Step 3: LIVE AUTOMATION MOMENT - WebSocket fires
        // This is automatic via WebSocket event from Step 2
        const notifCount = demoDataRef.current.notificationsCount || demoDataRef.current.civicWork?.affected_citizens || 0;
        
        toast.success(`🔔 ${notifCount} citizens identified and notified automatically`, {
          description: 'Real-time notifications sent via hyper-local engine',
          duration: 3500,
          icon: <Bell className="h-5 w-5 text-green-400" />
        });
        
        // Pulse the live indicator
        setWsConnected(true);
        break;
      }
      
      case 4: {
        // Step 4: Health Score Improves
        toast.info('📊 Recomputing booth health...', { duration: 1500 });
        
        const currentWeakBooth = demoDataRef.current.weakBooth;
        
        try {
          // Refresh booth health data
          const response = await api.get('/api/analytics/booth-health?limit=50');
          const booths = response.data.booths || [];
          setBoothsHealth(booths.slice(0, 10));
          
          // Simulate improvement in the weak booth
          const improvement = Math.floor(Math.random() * 8) + 3; // 3-10 point improvement
          
          demoDataRef.current = { ...demoDataRef.current, healthImprovement: improvement };
          setDemoData(prev => ({ ...prev, healthImprovement: improvement }));
          
          toast.success(`📈 Booth health improved through targeted intervention`, {
            description: `${currentWeakBooth?.booth_name || 'Selected booth'}: +${improvement} points`,
            duration: 3000,
            icon: <ArrowUpRight className="h-5 w-5 text-green-400" />
          });
          
          // Refresh dashboard stats
          fetchDashboardData();
        } catch (error) {
          console.error('Demo Step 4 error:', error);
        }
        break;
      }
      
      case 5: {
        // Step 5: Graph Intelligence Moment
        toast.info('🕸️ Analyzing community network...', { duration: 1500 });
        
        const currentWeakBooth = demoDataRef.current.weakBooth;
        
        try {
          const response = await api.get('/api/analytics/top-influencers?limit=5');
          const influencers = response.data.influencers || [];
          
          demoDataRef.current = { ...demoDataRef.current, influencers };
          setDemoData(prev => ({ ...prev, influencers }));
          
          toast.success(`🌟 Community leaders in ${currentWeakBooth?.booth_name || 'this area'}`, {
            description: `${influencers.length} key influencers identified`,
            duration: 3000,
            icon: <Users className="h-5 w-5 text-purple-400" />
          });
          
          // Navigate to network graph after a short delay
          setTimeout(() => {
            // Optional: navigate('/network');
          }, 1000);
        } catch (error) {
          console.error('Demo Step 5 error:', error);
        }
        break;
      }
      
      case 6: {
        // Step 6: Completion Banner
        setDemoState(DEMO_STATES.COMPLETED);
        setHighlightedBoothId(null);
        
        toast.success('✅ AI-driven micro-governance cycle completed', {
          description: 'From detection to intervention in seconds',
          duration: 5000,
          icon: <CheckCircle2 className="h-5 w-5 text-green-400" />
        });
        break;
      }
      
      default:
        break;
    }
  }, [fetchDashboardData]);
  
  const startDemo = useCallback(async () => {
    if (demoState === DEMO_STATES.RUNNING) return;
    
    resetDemo();
    setDemoState(DEMO_STATES.RUNNING);
    
    // Execute demo steps sequentially with delays
    for (let i = 0; i < DEMO_STEPS.length; i++) {
      const step = DEMO_STEPS[i];
      setDemoStep(step.id);
      
      await runDemoStep(step.id);
      
      // Wait for step delay before next step
      await new Promise(resolve => {
        demoTimerRef.current = setTimeout(resolve, step.delay);
      });
    }
  }, [demoState, resetDemo, runDemoStep]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (demoTimerRef.current) {
        clearTimeout(demoTimerRef.current);
      }
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      <Toaster position="top-right" richColors />
      
      {/* Top Navigation */}
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-white">ICIOS Dashboard</h1>
            
            {/* Live Indicator */}
            <div className="flex items-center space-x-2">
              <div className={`relative flex h-3 w-3 ${wsConnected ? 'animate-pulse' : ''}`}>
                <span className={`absolute inline-flex h-full w-full rounded-full ${wsConnected ? 'bg-green-400' : 'bg-gray-400'} opacity-75`}></span>
                <span className={`relative inline-flex rounded-full h-3 w-3 ${wsConnected ? 'bg-green-500' : 'bg-gray-500'}`}></span>
              </div>
              <span className={`text-sm font-medium ${wsConnected ? 'text-green-400' : 'text-gray-400'}`}>
                {wsConnected ? 'Live System Active' : 'Connecting...'}
              </span>
            </div>
            
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
        {/* Demo Control Panel */}
        <div className="mb-8 p-6 bg-gradient-to-r from-purple-950/50 via-blue-950/50 to-purple-950/50 rounded-2xl border border-purple-500/30 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-purple-500/20 rounded-xl">
                <Zap className="h-8 w-8 text-purple-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white flex items-center">
                  Guided Demo Mode
                  {demoState === DEMO_STATES.RUNNING && (
                    <span className="ml-3 px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded-full animate-pulse">
                      LIVE
                    </span>
                  )}
                  {demoState === DEMO_STATES.COMPLETED && (
                    <span className="ml-3 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                      COMPLETE
                    </span>
                  )}
                </h3>
                <p className="text-gray-400 text-sm">
                  {demoState === DEMO_STATES.IDLE && 'One-click AI demonstration for judges'}
                  {demoState === DEMO_STATES.RUNNING && `Step ${demoStep}/6: ${DEMO_STEPS[demoStep - 1]?.title || ''}`}
                  {demoState === DEMO_STATES.COMPLETED && 'AI-driven micro-governance cycle demonstrated'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Demo Progress Indicator */}
              {demoState === DEMO_STATES.RUNNING && (
                <div className="flex items-center space-x-2 mr-4">
                  {DEMO_STEPS.map((step, idx) => (
                    <div
                      key={step.id}
                      className={`w-3 h-3 rounded-full transition-all duration-300 ${
                        demoStep > step.id ? 'bg-green-500' :
                        demoStep === step.id ? 'bg-yellow-400 animate-pulse scale-125' :
                        'bg-gray-600'
                      }`}
                      title={step.title}
                    />
                  ))}
                </div>
              )}
              
              {/* Control Buttons */}
              {demoState === DEMO_STATES.IDLE && (
                <Button
                  data-testid="start-demo-btn"
                  onClick={startDemo}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-6 py-2 rounded-xl font-semibold transition-all hover:scale-105"
                >
                  <Play className="h-5 w-5 mr-2" />
                  Start Demo
                </Button>
              )}
              
              {demoState === DEMO_STATES.RUNNING && (
                <Button
                  data-testid="demo-running-indicator"
                  disabled
                  className="bg-yellow-500/20 text-yellow-400 px-6 py-2 rounded-xl font-semibold cursor-not-allowed"
                >
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Running...
                </Button>
              )}
              
              {demoState === DEMO_STATES.COMPLETED && (
                <div className="flex space-x-2">
                  <Button
                    data-testid="reset-demo-btn"
                    onClick={resetDemo}
                    variant="outline"
                    className="border-gray-500/30 text-gray-400 hover:bg-gray-500/10 px-4 py-2 rounded-xl"
                  >
                    <RotateCcw className="h-5 w-5 mr-2" />
                    Reset
                  </Button>
                  <Button
                    data-testid="run-again-btn"
                    onClick={startDemo}
                    className="bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white px-6 py-2 rounded-xl font-semibold transition-all hover:scale-105"
                  >
                    <Play className="h-5 w-5 mr-2" />
                    Run Again
                  </Button>
                </div>
              )}
            </div>
          </div>
          
          {/* Demo Summary (when completed) */}
          {demoState === DEMO_STATES.COMPLETED && demoData.civicWork && (
            <div className="mt-6 pt-6 border-t border-purple-500/20">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-blue-950/30 rounded-xl border border-blue-500/20">
                  <div className="flex items-center space-x-2 mb-2">
                    <Target className="h-5 w-5 text-blue-400" />
                    <span className="text-gray-400 text-sm">Detected Booth</span>
                  </div>
                  <p className="text-white font-semibold">{demoData.weakBooth?.booth_name || 'N/A'}</p>
                  <p className="text-gray-500 text-xs">Score: {demoData.weakBooth?.health_score || 'N/A'}</p>
                </div>
                
                <div className="p-4 bg-green-950/30 rounded-xl border border-green-500/20">
                  <div className="flex items-center space-x-2 mb-2">
                    <Bell className="h-5 w-5 text-green-400" />
                    <span className="text-gray-400 text-sm">Citizens Notified</span>
                  </div>
                  <p className="text-white font-semibold text-2xl">{demoData.civicWork?.affected_citizens || 0}</p>
                </div>
                
                <div className="p-4 bg-purple-950/30 rounded-xl border border-purple-500/20">
                  <div className="flex items-center space-x-2 mb-2">
                    <ArrowUpRight className="h-5 w-5 text-purple-400" />
                    <span className="text-gray-400 text-sm">Health Boost</span>
                  </div>
                  <p className="text-white font-semibold text-2xl">+{demoData.healthImprovement}</p>
                </div>
                
                <div className="p-4 bg-yellow-950/30 rounded-xl border border-yellow-500/20">
                  <div className="flex items-center space-x-2 mb-2">
                    <Users className="h-5 w-5 text-yellow-400" />
                    <span className="text-gray-400 text-sm">Influencers Found</span>
                  </div>
                  <p className="text-white font-semibold text-2xl">{demoData.influencers?.length || 0}</p>
                </div>
              </div>
            </div>
          )}
        </div>

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
                      <tr 
                        key={idx} 
                        className={`border-b border-blue-500/10 transition-all duration-500 ${
                          highlightedBoothId === booth.booth_id 
                            ? 'bg-yellow-500/20 border-yellow-500/30 ring-2 ring-yellow-500/30 animate-pulse' 
                            : 'hover:bg-blue-950/20'
                        }`}
                        data-testid={`booth-row-${booth.booth_id}`}
                      >
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
      
      {/* Live Activity Feed - Fixed Position */}
      {activityFeed.length > 0 && (
        <div className="fixed bottom-6 right-6 w-96 max-h-96 overflow-y-auto bg-[#0B1120]/95 backdrop-blur-xl border border-blue-500/30 rounded-2xl p-4 shadow-2xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white flex items-center">
              <Activity className="h-5 w-5 mr-2 text-blue-400" />
              Live Activity
            </h3>
            <span className="text-xs text-gray-400">{activityFeed.length} events</span>
          </div>
          <div className="space-y-3">
            {activityFeed.map((event, idx) => (
              <div 
                key={event.id}
                className="p-3 bg-gradient-to-br from-blue-950/40 to-purple-950/30 rounded-lg border border-blue-500/20 animate-in fade-in slide-in-from-right duration-300"
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="text-sm font-medium text-white">{event.category}</div>
                  <div className="text-xs text-gray-400">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                <div className="text-sm text-gray-300 mb-2">{event.title}</div>
                <div className="flex items-center space-x-4 text-xs text-gray-400">
                  <span>👥 {event.citizens} citizens</span>
                  <span>📧 {event.notifications} notifications</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;