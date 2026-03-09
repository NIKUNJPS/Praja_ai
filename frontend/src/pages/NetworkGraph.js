import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
  Handle,
  Position
} from 'reactflow';
import * as d3 from 'd3-force';
import { useDebounce } from 'react-use';
import { groupBy } from 'lodash';
import 'reactflow/dist/style.css';
import {
  Home,
  Users,
  Filter,
  Search,
  Target,
  RefreshCw,
  Layers,
  BarChart2,
  Globe,
  MapPin,
  Award,
  TrendingUp,
  X,
  ZoomIn,
  ZoomOut,
  Move,
  Network
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Slider } from '../components/ui/slider';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

// Helper to compute node size based on influence
const getNodeSize = (influence) => 15 + influence * 0.6; // influence 0-100 -> size 15-75

// Color mapping for segments
const SEGMENT_COLORS = {
  Youth: '#3B82F6',
  Women: '#EC4899',
  'Senior Citizen': '#F59E0B',
  Business: '#A855F7',
  Farmer: '#10B981',
  'Urban Poor': '#EF4444',
  'Community Leader': '#8B5CF6',
  default: '#6B7280'
};

// Relationship colors
const RELATIONSHIP_COLORS = {
  RESIDES_IN: '#3B82F6',
  BELONGS_TO: '#A855F7',
  INFLUENCES: '#F59E0B',
  PARTICIPATES_IN: '#10B981',
  default: '#6B7280'
};

// Edge type mapping
const RELATIONSHIP_TYPES = {
  same_street: 'RESIDES_IN',
  same_booth: 'BELONGS_TO',
  shared_scheme: 'PARTICIPATES_IN',
  shared_activity: 'PARTICIPATES_IN',
  influence: 'INFLUENCES'
};

const NetworkGraph = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [citizenDetail, setCitizenDetail] = useState(null);
  const [filters, setFilters] = useState({
    segment: '',
    boothId: '',
    minInfluence: 0,
    searchQuery: ''
  });
  const [meta, setMeta] = useState(null);
  const [mode, setMode] = useState('full'); // 'full', 'influence', 'community', 'booth'
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [highlightedNode, setHighlightedNode] = useState(null);
  const [searchResult, setSearchResult] = useState(null);
  const [graphStats, setGraphStats] = useState({
    totalNodes: 0,
    totalEdges: 0,
    topInfluencer: null,
    avgInfluence: 0,
    communities: 0
  });

  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const simulationRef = useRef(null);

  // Custom force to cluster nodes by segment (memoized)
  const groupForce = useCallback((nodes) => {
    const groups = groupBy(nodes, n => n.data.primary_segment);
    const centers = {};
    Object.keys(groups).forEach(segment => {
      // Place group centers around the canvas
      centers[segment] = { x: 200 + Math.random() * 800, y: 100 + Math.random() * 400 };
    });
    return (alpha) => {
      nodes.forEach(node => {
        const target = centers[node.data.primary_segment];
        if (target) {
          node.vx += (target.x - node.x) * 0.02 * alpha;
          node.vy += (target.y - node.y) * 0.02 * alpha;
        }
      });
    };
  }, []);

  // Run force‑directed layout (memoized)
  const runForceLayout = useCallback((nodes, edges) => {
    // Create d3 simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(600, 300))
      .force('collision', d3.forceCollide().radius(d => d.data.size / 2 + 10))
      .force('group', groupForce(nodes)) // custom force to cluster by segment
      .on('tick', () => {
        // Update node positions in React state (throttle for performance)
        setNodes(prevNodes =>
          prevNodes.map(node => {
            const updated = nodes.find(n => n.id === node.id);
            return updated ? { ...node, position: { x: updated.x, y: updated.y } } : node;
          })
        );
      })
      .on('end', () => {
        simulation.stop();
      });

    simulationRef.current = simulation;
  }, [groupForce, setNodes]);

  // Fetch graph data
  const fetchGraphData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', '500'); // Increased for richer graph
      if (filters.boothId) params.append('booth_id', filters.boothId);
      if (filters.minInfluence > 0) params.append('min_influence', filters.minInfluence);
      if (filters.segment) params.append('segment', filters.segment);

      const response = await api.get(`/graph/network?${params.toString()}`);
      const { nodes: apiNodes, edges: apiEdges, meta: apiMeta } = response.data;

      // Build nodes with enhanced data
      const newNodes = apiNodes.map(node => {
        const size = getNodeSize(node.data.influence_score);
        return {
          id: node.id,
          type: 'custom', // We'll define a custom node type
          data: {
            ...node.data,
            label: node.data.name,
            size,
            color: SEGMENT_COLORS[node.data.primary_segment] || SEGMENT_COLORS.default
          },
          position: node.position || { x: Math.random() * 1000, y: Math.random() * 1000 }, // initial random
          style: {
            width: size,
            height: size,
            backgroundColor: SEGMENT_COLORS[node.data.primary_segment] || SEGMENT_COLORS.default,
            border: node.data.is_top_influencer ? '3px solid #FBBF24' : '2px solid #374151',
            borderRadius: '50%',
            boxShadow: node.data.is_top_influencer
              ? '0 0 20px rgba(251, 191, 36, 0.6), 0 0 40px rgba(251, 191, 36, 0.3)'
              : '0 2px 8px rgba(0,0,0,0.3)',
            transition: 'all 0.3s ease',
            cursor: 'pointer'
          }
        };
      });

      // Build edges with relationship types
      const newEdges = apiEdges.map((edge, index) => ({
        id: `e-${index}`,
        source: edge.source,
        target: edge.target,
        label: RELATIONSHIP_TYPES[edge.relationship] || edge.relationship || 'CONNECTED',
        type: 'smoothstep',
        animated: false,
        style: {
          stroke: RELATIONSHIP_COLORS[RELATIONSHIP_TYPES[edge.relationship]] || RELATIONSHIP_COLORS.default,
          strokeWidth: 1 + (edge.weight || 0) * 2,
          opacity: 0.8
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: RELATIONSHIP_COLORS[RELATIONSHIP_TYPES[edge.relationship]] || RELATIONSHIP_COLORS.default
        },
        labelStyle: { fill: '#9CA3AF', fontSize: 10 },
        labelBgStyle: { fill: '#1F2937', fillOpacity: 0.8 }
      }));

      setNodes(newNodes);
      setEdges(newEdges);
      setMeta(apiMeta);

      // Update graph stats
      const influenceScores = newNodes.map(n => n.data.influence_score);
      const avg = influenceScores.reduce((a, b) => a + b, 0) / influenceScores.length;
      const top = newNodes.reduce((best, node) => (node.data.influence_score > best?.data?.influence_score ? node : best), null);
      // Simple community count: number of distinct segments (or we can compute later)
      const communities = new Set(newNodes.map(n => n.data.primary_segment)).size;
      setGraphStats({
        totalNodes: newNodes.length,
        totalEdges: newEdges.length,
        topInfluencer: top ? { name: top.data.name, score: top.data.influence_score } : null,
        avgInfluence: avg.toFixed(2),
        communities
      });

      // After nodes are set, run force layout
      if (newNodes.length > 0) {
        runForceLayout(newNodes, newEdges);
      }
    } catch (error) {
      console.error('Failed to fetch graph data:', error);
      toast({ title: 'Error', description: 'Could not load graph data', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  }, [filters, toast, setNodes, setEdges, runForceLayout]);

  useEffect(() => {
    fetchGraphData();
    return () => {
      if (simulationRef.current) simulationRef.current.stop();
    };
  }, [fetchGraphData]);

  // Debounced search
  const [searchTerm, setSearchTerm] = useState('');
  useDebounce(() => {
    if (searchTerm) {
      const found = nodes.find(n => n.data.name.toLowerCase().includes(searchTerm.toLowerCase()));
      if (found && reactFlowInstance) {
        reactFlowInstance.fitView({ nodes: [found], duration: 800, padding: 0.2 });
        setHighlightedNode(found.id);
        setSearchResult(found);
        setTimeout(() => setHighlightedNode(null), 2000);
      }
    } else {
      setSearchResult(null);
    }
  }, 500, [searchTerm, nodes, reactFlowInstance]);

  // Node click handler
  const onNodeClick = useCallback(async (event, node) => {
    setSelectedNode(node);
    setCitizenDetail(null);
    // Highlight influence network
    const connectedEdges = edges.filter(e => e.source === node.id || e.target === node.id);
    const connectedNodeIds = new Set();
    connectedEdges.forEach(e => {
      connectedNodeIds.add(e.source);
      connectedNodeIds.add(e.target);
    });
    setNodes(prevNodes =>
      prevNodes.map(n => ({
        ...n,
        style: {
          ...n.style,
          opacity: connectedNodeIds.has(n.id) || n.id === node.id ? 1 : 0.2,
          transform: n.id === node.id ? 'scale(1.2)' : 'scale(1)'
        }
      }))
    );
    setEdges(prevEdges =>
      prevEdges.map(e => ({
        ...e,
        animated: e.source === node.id || e.target === node.id,
        style: { ...e.style, opacity: e.source === node.id || e.target === node.id ? 1 : 0.2 }
      }))
    );
    // Fetch details
    try {
      const response = await api.get(`/graph/citizen/${node.id}`);
      setCitizenDetail(response.data);
    } catch (error) {
      console.error('Failed to fetch citizen detail:', error);
      toast({ title: 'Error', description: 'Could not load citizen details', variant: 'destructive' });
    }
  }, [edges, toast, setNodes, setEdges]);

  // Clear highlight
  const clearHighlight = useCallback(() => {
    setNodes(prevNodes => prevNodes.map(n => ({ ...n, style: { ...n.style, opacity: 1, transform: 'scale(1)' } })));
    setEdges(prevEdges => prevEdges.map(e => ({ ...e, animated: false, style: { ...e.style, opacity: 0.8 } })));
    setSelectedNode(null);
    setCitizenDetail(null);
  }, [setNodes, setEdges]);

  // Mode switching
  const switchMode = useCallback((newMode) => {
    setMode(newMode);
    // Filter edges based on mode
    let filteredEdges = edges;
    if (newMode === 'influence') {
      filteredEdges = edges.filter(e => e.label === 'INFLUENCES' || e.label === 'INFLUENCES' || e.weight > 0.5);
    } else if (newMode === 'community') {
      // For community, we already have clustering via force layout
    } else if (newMode === 'booth') {
      filteredEdges = edges.filter(e => e.label === 'BELONGS_TO');
    }
    setEdges(filteredEdges);
  }, [edges, setEdges]);

  // Custom node component with zoom‑based labels
  const CustomNode = useMemo(() => {
    const NodeComponent = ({ data }) => {
      const showLabel = zoomLevel > 0.5; // adjust threshold as needed
      const showDetail = zoomLevel > 1.2;
      return (
        <div
          style={{
            width: data.size,
            height: data.size,
            backgroundColor: data.color,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: showLabel ? (data.size > 40 ? 12 : 10) : 0,
            fontWeight: 'bold',
            boxShadow: data.is_top_influencer ? '0 0 20px #FBBF24' : 'none',
            transition: 'all 0.2s',
            cursor: 'pointer'
          }}
          onMouseEnter={() => setHoveredNode(data)}
          onMouseLeave={() => setHoveredNode(null)}
        >
          {showLabel && data.name.substring(0, 2)}
          {showDetail && (
            <div style={{ position: 'absolute', top: '100%', background: '#1F2937', padding: '4px', borderRadius: '4px', fontSize: 10, whiteSpace: 'nowrap' }}>
              {data.name} ({data.influence_score})
            </div>
          )}
        </div>
      );
    };
    return NodeComponent;
  }, [zoomLevel]);

  const nodeTypes = useMemo(() => ({ custom: CustomNode }), [CustomNode]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      {/* Top Navigation */}
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')} className="text-white hover:text-blue-400">
              <Home className="h-4 w-4 mr-1" />
              Dashboard
            </Button>
            <div className="h-5 w-px bg-blue-500/30" />
            <h1 className="text-xl font-bold text-white">Knowledge Graph</h1>
            {meta && (
              <span className="hidden md:inline text-sm text-gray-400">
                {meta.total_nodes} nodes • {meta.total_edges} edges • Avg Influence {meta.avg_influence}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button size="sm" variant="ghost" onClick={fetchGraphData} className="text-gray-400 hover:text-white">
              <RefreshCw className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
            <Button size="sm" onClick={() => setShowAnalytics(!showAnalytics)} className="bg-blue-600 hover:bg-blue-700 text-white">
              <BarChart2 className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Analytics</span>
            </Button>
          </div>
        </div>
      </nav>

      <div className="flex h-[calc(100vh-4rem)]">
        {/* Filter Panel */}
        <aside className="w-80 bg-[#0B1120]/90 backdrop-blur-xl border-r border-blue-500/20 p-5 overflow-y-auto hidden md:block">
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <Filter className="h-5 w-5 mr-2 text-blue-400" />
              Filters
            </h3>

            {/* Search */}
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Search Citizen</label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                <Input
                  placeholder="Search by name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 bg-[#1E293B] border-blue-500/30 text-white placeholder:text-gray-500"
                />
              </div>
            </div>

            {/* Segment Filter */}
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Segment</label>
              <select
                value={filters.segment}
                onChange={(e) => setFilters(prev => ({ ...prev, segment: e.target.value }))}
                className="w-full px-3 py-2 bg-[#1E293B] border border-blue-500/30 rounded-md text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All Segments</option>
                <option value="Youth">Youth</option>
                <option value="Women">Women</option>
                <option value="Senior Citizen">Senior Citizen</option>
                <option value="Business">Business</option>
                <option value="Farmer">Farmer</option>
                <option value="Urban Poor">Urban Poor</option>
                <option value="Community Leader">Community Leader</option>
              </select>
            </div>

            {/* Booth ID */}
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Booth ID</label>
              <Input
                type="number"
                placeholder="Enter booth ID"
                value={filters.boothId}
                onChange={(e) => setFilters(prev => ({ ...prev, boothId: e.target.value }))}
                className="bg-[#1E293B] border-blue-500/30 text-white placeholder:text-gray-500"
              />
            </div>

            {/* Influence Threshold */}
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Minimum Influence: {filters.minInfluence}</label>
              <Slider
                value={[filters.minInfluence]}
                onValueChange={(value) => setFilters(prev => ({ ...prev, minInfluence: value[0] }))}
                max={100}
                step={5}
                className="mt-2"
              />
            </div>

            {/* Mode Selection */}
            <div>
              <label className="text-sm text-gray-400 mb-2 block">View Mode</label>
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  variant={mode === 'full' ? 'default' : 'outline'}
                  onClick={() => switchMode('full')}
                  className={mode === 'full' ? 'bg-blue-600' : 'border-blue-500/30 text-gray-300'}
                >
                  <Network className="h-4 w-4 mr-1" />
                  Full
                </Button>
                <Button
                  size="sm"
                  variant={mode === 'influence' ? 'default' : 'outline'}
                  onClick={() => switchMode('influence')}
                  className={mode === 'influence' ? 'bg-blue-600' : 'border-blue-500/30 text-gray-300'}
                >
                  <TrendingUp className="h-4 w-4 mr-1" />
                  Influence
                </Button>
                <Button
                  size="sm"
                  variant={mode === 'community' ? 'default' : 'outline'}
                  onClick={() => switchMode('community')}
                  className={mode === 'community' ? 'bg-blue-600' : 'border-blue-500/30 text-gray-300'}
                >
                  <Layers className="h-4 w-4 mr-1" />
                  Community
                </Button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2 pt-2">
              <Button onClick={fetchGraphData} className="w-full bg-blue-600 hover:bg-blue-700">
                Apply Filters
              </Button>
              <Button
                onClick={() => {
                  setFilters({ segment: '', boothId: '', minInfluence: 0, searchQuery: '' });
                  fetchGraphData();
                }}
                variant="outline"
                className="w-full border-blue-500/30 text-gray-300"
              >
                Reset
              </Button>
            </div>

            {/* Legend */}
            <div className="pt-6 border-t border-blue-500/20">
              <h4 className="text-sm font-semibold text-white mb-3">Legend</h4>
              <div className="space-y-2">
                {Object.entries(SEGMENT_COLORS).map(([seg, color]) => (
                  <div key={seg} className="flex items-center space-x-2 text-sm">
                    <span className="inline-block w-4 h-4 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-gray-400">{seg}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 bg-yellow-500/10 rounded-md border border-yellow-500/30">
                <p className="text-xs text-yellow-400 flex items-center">
                  <span className="mr-1">⭐</span> Glowing nodes = Top 10 Influencers
                </p>
              </div>
            </div>
          </div>
        </aside>

        {/* Graph Area */}
        <main className="flex-1 relative" ref={reactFlowWrapper}>
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4" />
                <p className="text-gray-400">Loading knowledge graph...</p>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onPaneClick={clearHighlight}
              onInit={setReactFlowInstance}
              onMove={(evt) => {
                // Guard against null viewport
                if (evt?.viewport?.zoom !== undefined) {
                  setZoomLevel(evt.viewport.zoom);
                }
              }}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-left"
              className="bg-[#0B1120]"
            >
              <Background color="#1E293B" gap={16} />
              <Controls
                className="!bg-[#1E293B] !border-blue-500/30 [&>button]:!text-gray-300 [&>button:hover]:!bg-blue-500/20"
                showInteractive={false}
              />
              <MiniMap
                nodeColor={(node) => node.data.color}
                className="!bg-[#1E293B] !border-blue-500/30"
                maskColor="rgba(11, 17, 32, 0.8)"
              />
              <Panel position="top-right" className="bg-[#1E293B]/80 backdrop-blur-sm p-2 rounded-lg border border-blue-500/30">
                <div className="flex space-x-2">
                  <Button size="sm" variant="ghost" onClick={() => reactFlowInstance?.fitView({ padding: 0.2 })}>
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => reactFlowInstance?.zoomOut()}>
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => reactFlowInstance?.fitView({ nodes: [selectedNode], duration: 800 })} disabled={!selectedNode}>
                    <Target className="h-4 w-4" />
                  </Button>
                </div>
              </Panel>
            </ReactFlow>
          )}
        </main>

        {/* Analytics Panel */}
        {showAnalytics && (
          <aside className="w-80 bg-[#0B1120]/90 backdrop-blur-xl border-l border-blue-500/20 p-5 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Graph Analytics</h3>
              <Button size="sm" variant="ghost" onClick={() => setShowAnalytics(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4">
              <Card className="p-4 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/20">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Nodes</span>
                    <span className="text-white font-bold">{graphStats.totalNodes}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Edges</span>
                    <span className="text-white font-bold">{graphStats.totalEdges}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Avg Influence</span>
                    <span className="text-white font-bold">{graphStats.avgInfluence}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Communities</span>
                    <span className="text-white font-bold">{graphStats.communities}</span>
                  </div>
                </div>
              </Card>
              {graphStats.topInfluencer && (
                <Card className="p-4 bg-gradient-to-br from-yellow-950/40 to-amber-950/30 border-yellow-500/20">
                  <p className="text-sm text-gray-400 mb-1">Top Influencer</p>
                  <p className="text-xl font-bold text-white">{graphStats.topInfluencer.name}</p>
                  <p className="text-sm text-yellow-400">Score: {graphStats.topInfluencer.score}</p>
                </Card>
              )}
              <div className="pt-4">
                <h4 className="text-sm font-semibold text-white mb-2">Influence Distribution</h4>
                <div className="h-32 bg-[#1E293B] rounded-md flex items-end justify-around p-2">
                  {nodes.slice(0, 10).map(node => (
                    <div
                      key={node.id}
                      style={{ height: `${node.data.influence_score}%`, width: '8%', backgroundColor: node.data.color }}
                      className="rounded-t"
                    />
                  ))}
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* Detail Drawer */}
        {selectedNode && citizenDetail && (
          <aside className="w-96 bg-[#0B1120]/90 backdrop-blur-xl border-l border-blue-500/20 p-5 overflow-y-auto animate-in slide-in-from-right">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-bold text-white">{citizenDetail.citizen.name}</h3>
              <Button size="sm" variant="ghost" onClick={clearHighlight} className="text-gray-400 hover:text-white">
                <X className="h-5 w-5" />
              </Button>
            </div>
            <div className="space-y-6">
              {/* Influence Card */}
              <Card className="p-4 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/20">
                <p className="text-sm text-gray-400 mb-1">Influence Score</p>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold text-white">{citizenDetail.influence.score}</span>
                  <span className="text-sm text-gray-400">/100</span>
                </div>
                <p className="text-xs text-blue-400 mt-1">Rank #{citizenDetail.influence.rank}</p>
              </Card>

              {/* Demographics */}
              <div>
                <h4 className="text-sm font-semibold text-white mb-3">Demographics</h4>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-gray-400">Age:</dt>
                    <dd className="text-white">{citizenDetail.citizen.age}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-400">Gender:</dt>
                    <dd className="text-white">{citizenDetail.citizen.gender}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-400">Occupation:</dt>
                    <dd className="text-white">{citizenDetail.citizen.occupation}</dd>
                  </div>
                </dl>
              </div>

              {/* Segments */}
              {citizenDetail.segments?.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-white mb-3">Segments</h4>
                  <div className="flex flex-wrap gap-2">
                    {citizenDetail.segments.map((seg, idx) => (
                      <span key={idx} className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs">
                        {seg}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sentiment */}
              <div>
                <h4 className="text-sm font-semibold text-white mb-3">Sentiment</h4>
                <div className="p-3 bg-[#1E293B] rounded-md">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-400 text-sm">Avg Score:</span>
                    <span className={`font-bold ${
                      citizenDetail.sentiment.label === 'Positive' ? 'text-green-400' :
                      citizenDetail.sentiment.label === 'Negative' ? 'text-red-400' : 'text-gray-400'
                    }`}>
                      {citizenDetail.sentiment.label}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{citizenDetail.sentiment.count} feedback entries</p>
                </div>
              </div>

              {/* Schemes */}
              {citizenDetail.schemes?.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-white mb-3">Scheme Participation ({citizenDetail.schemes.length})</h4>
                  <div className="space-y-2">
                    {citizenDetail.schemes.slice(0, 3).map((scheme, idx) => (
                      <div key={idx} className="p-2 bg-[#1E293B] rounded-md text-xs">
                        <p className="text-white font-medium">{scheme.name}</p>
                        <p className="text-gray-500">{scheme.category}</p>
                      </div>
                    ))}
                    {citizenDetail.schemes.length > 3 && (
                      <p className="text-xs text-gray-500">+{citizenDetail.schemes.length - 3} more</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};

export default NetworkGraph;