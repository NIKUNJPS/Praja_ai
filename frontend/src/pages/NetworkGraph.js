import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Home, Users, Filter, Search, Target } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Slider } from '../components/ui/slider';
import api from '../services/api';

const NetworkGraph = () => {
  const navigate = useNavigate();
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

  useEffect(() => {
    fetchGraphData();
  }, []);

  const fetchGraphData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('limit', '250');
      if (filters.boothId) params.append('booth_id', filters.boothId);
      if (filters.minInfluence > 0) params.append('min_influence', filters.minInfluence);
      if (filters.segment) params.append('segment', filters.segment);

      const response = await api.get(`/api/graph/network?${params.toString()}`);
      
      // Transform nodes with custom styling
      const transformedNodes = response.data.nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          label: node.data.name
        },
        style: {
          width: node.data.size,
          height: node.data.size,
          backgroundColor: node.data.color,
          border: node.data.is_top_influencer ? '3px solid #FBBF24' : '2px solid #374151',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '10px',
          color: '#fff',
          fontWeight: 'bold',
          boxShadow: node.data.is_top_influencer 
            ? '0 0 20px rgba(251, 191, 36, 0.6), 0 0 40px rgba(251, 191, 36, 0.3)' 
            : '0 2px 8px rgba(0,0,0,0.3)',
          transition: 'all 0.3s ease',
          cursor: 'pointer'
        }
      }));

      // Transform edges
      const transformedEdges = response.data.edges.map(edge => ({
        ...edge,
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edge.style.stroke
        }
      }));

      setNodes(transformedNodes);
      setEdges(transformedEdges);
      setMeta(response.data.meta);
    } catch (error) {
      console.error('Failed to fetch graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  const onNodeClick = useCallback(async (event, node) => {
    setSelectedNode(node);
    
    try {
      const response = await api.get(`/api/graph/citizen/${node.id}`);
      setCitizenDetail(response.data);
    } catch (error) {
      console.error('Failed to fetch citizen detail:', error);
    }
  }, []);

  const focusOnTopInfluencers = () => {
    const topNodes = nodes.filter(n => n.data.is_top_influencer);
    if (topNodes.length > 0) {
      // Highlight top influencer nodes
      setNodes(nodes.map(node => ({
        ...node,
        style: {
          ...node.style,
          opacity: node.data.is_top_influencer ? 1 : 0.3,
          transform: node.data.is_top_influencer ? 'scale(1.2)' : 'scale(1)'
        }
      })));
      
      // Animate edges connected to top influencers
      const topNodeIds = topNodes.map(n => n.id);
      setEdges(edges.map(edge => ({
        ...edge,
        animated: topNodeIds.includes(edge.source) || topNodeIds.includes(edge.target)
      })));
    }
  };

  const resetFilters = () => {
    setFilters({
      segment: '',
      boothId: '',
      minInfluence: 0,
      searchQuery: ''
    });
    fetchGraphData();
  };

  const applyFilters = () => {
    fetchGraphData();
  };

  const searchNodes = (query) => {
    if (!query) {
      fetchGraphData();
      return;
    }
    
    const filtered = nodes.filter(node => 
      node.data.name.toLowerCase().includes(query.toLowerCase())
    );
    
    setNodes(nodes.map(node => ({
      ...node,
      style: {
        ...node.style,
        opacity: filtered.some(f => f.id === node.id) ? 1 : 0.2
      }
    })));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B]">
      {/* Top Navigation */}
      <nav className="bg-[#0B1120]/80 backdrop-blur-xl border-b border-blue-500/20 px-6 py-4">
        <div className="max-w-full mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              data-testid="back-to-dashboard-btn"
              variant="ghost"
              onClick={() => navigate('/dashboard')}
            >
              <Home className="h-4 w-4 mr-2 text-white" />
              <span className="text-white">Dashboard</span>
            </Button>
            <div className="h-6 w-px bg-blue-500/30"></div>
            <h1 className="text-2xl font-bold text-white">Knowledge Graph</h1>
            {meta && (
              <div className="text-sm text-gray-400">
                {meta.total_nodes} nodes • {meta.total_edges} edges
              </div>
            )}
          </div>
          
          <Button
            data-testid="focus-top-influencers-btn"
            onClick={focusOnTopInfluencers}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
          >
            <Target className="h-4 w-4 mr-2" />
            Focus on Top Influencers
          </Button>
        </div>
      </nav>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Filter Panel */}
        <div className="w-80 bg-[#0B1120]/60 backdrop-blur-xl border-r border-blue-500/20 p-6 overflow-y-auto">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                <Filter className="h-5 w-5 mr-2 text-blue-400" />
                Filters
              </h3>
            </div>

            {/* Search */}
            <div>
              <label className="text-sm text-gray-400 mb-2 block">Search Citizen</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-500" />
                <Input
                  data-testid="search-citizen-input"
                  placeholder="Search by name..."
                  value={filters.searchQuery}
                  onChange={(e) => {
                    setFilters({...filters, searchQuery: e.target.value});
                    searchNodes(e.target.value);
                  }}
                  className="pl-10 bg-[#1E293B] border-blue-500/30 text-white placeholder:text-gray-500"
                />
              </div>
            </div>

            {/* Segment Filter */}
            <div>
              <label className="text-sm text-gray-400 mb-2 block">Segment</label>
              <select
                data-testid="segment-filter-select"
                value={filters.segment}
                onChange={(e) => setFilters({...filters, segment: e.target.value})}
                className="w-full px-4 py-2 bg-[#1E293B] border border-blue-500/30 rounded-lg text-white focus:outline-none focus:border-blue-500"
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

            {/* Influence Threshold */}
            <div>
              <label className="text-sm text-gray-400 mb-2 block">
                Min Influence: {filters.minInfluence}
              </label>
              <Slider
                data-testid="influence-slider"
                value={[filters.minInfluence]}
                onValueChange={(value) => setFilters({...filters, minInfluence: value[0]})}
                max={100}
                step={5}
                className="mt-2"
              />
            </div>

            {/* Apply Filters */}
            <div className="space-y-2">
              <Button
                data-testid="apply-filters-btn"
                onClick={applyFilters}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                Apply Filters
              </Button>
              <Button
                data-testid="reset-filters-btn"
                onClick={resetFilters}
                variant="outline"
                className="w-full border-blue-500/30 text-gray-300"
              >
                Reset
              </Button>
            </div>

            {/* Legend */}
            <div className="pt-6 border-t border-blue-500/20">
              <h4 className="text-sm font-bold text-white mb-3">Legend</h4>
              <div className="space-y-2">
                {[
                  { color: '#3B82F6', label: 'Youth' },
                  { color: '#EC4899', label: 'Women' },
                  { color: '#F59E0B', label: 'Senior Citizen' },
                  { color: '#A855F7', label: 'Business' },
                  { color: '#10B981', label: 'Farmer' },
                  { color: '#EF4444', label: 'Urban Poor' },
                  { color: '#8B5CF6', label: 'Community Leader' }
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center space-x-2">
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: item.color }}
                    ></div>
                    <span className="text-sm text-gray-400">{item.label}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
                <p className="text-xs text-yellow-400">
                  ⭐ Glowing nodes = Top 10 Influencers
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Graph Area */}
        <div className="flex-1 relative">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
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
              fitView
              attributionPosition="bottom-left"
              className="bg-[#0B1120]"
            >
              <Background color="#1E293B" gap={16} />
              <Controls className="!bg-[#1E293B] !border-blue-500/30" />
              <MiniMap 
                nodeColor={(node) => node.data.color}
                className="!bg-[#1E293B] !border-blue-500/30"
                maskColor="rgba(11, 17, 32, 0.8)"
              />
            </ReactFlow>
          )}
        </div>

        {/* Detail Drawer */}
        {selectedNode && citizenDetail && (
          <div className="w-96 bg-[#0B1120]/90 backdrop-blur-xl border-l border-blue-500/20 p-6 overflow-y-auto">
            <div className="space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">{citizenDetail.citizen.name}</h3>
                  <p className="text-sm text-gray-400">Citizen ID: {citizenDetail.citizen.id}</p>
                </div>
                <Button
                  data-testid="close-detail-btn"
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setSelectedNode(null);
                    setCitizenDetail(null);
                  }}
                  className="text-gray-400"
                >
                  ✕
                </Button>
              </div>

              {/* Influence */}
              <Card className="p-4 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border-blue-500/20">
                <p className="text-sm text-gray-400 mb-1">Influence Score</p>
                <div className="flex items-baseline space-x-2">
                  <h4 className="text-3xl font-bold text-white">{citizenDetail.influence.score}</h4>
                  <span className="text-sm text-gray-400">/100</span>
                </div>
                <p className="text-xs text-blue-400 mt-1">Rank #{citizenDetail.influence.rank}</p>
              </Card>

              {/* Demographics */}
              <div>
                <h4 className="text-sm font-bold text-white mb-3">Demographics</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Age:</span>
                    <span className="text-white">{citizenDetail.citizen.age}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Gender:</span>
                    <span className="text-white">{citizenDetail.citizen.gender}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Occupation:</span>
                    <span className="text-white">{citizenDetail.citizen.occupation}</span>
                  </div>
                </div>
              </div>

              {/* Segments */}
              <div>
                <h4 className="text-sm font-bold text-white mb-3">Segments</h4>
                <div className="flex flex-wrap gap-2">
                  {citizenDetail.segments.map((seg, idx) => (
                    <span 
                      key={idx}
                      className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs"
                    >
                      {seg}
                    </span>
                  ))}
                </div>
              </div>

              {/* Sentiment */}
              <div>
                <h4 className="text-sm font-bold text-white mb-3">Sentiment</h4>
                <div className="p-3 bg-[#1E293B] rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-400 text-sm">Avg Score:</span>
                    <span className={`font-bold ${
                      citizenDetail.sentiment.label === 'Positive' ? 'text-green-400' :
                      citizenDetail.sentiment.label === 'Negative' ? 'text-red-400' :
                      'text-gray-400'
                    }`}>
                      {citizenDetail.sentiment.label}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {citizenDetail.sentiment.count} feedback entries
                  </div>
                </div>
              </div>

              {/* Schemes */}
              <div>
                <h4 className="text-sm font-bold text-white mb-3">
                  Scheme Participation ({citizenDetail.schemes.length})
                </h4>
                <div className="space-y-2">
                  {citizenDetail.schemes.slice(0, 3).map((scheme, idx) => (
                    <div key={idx} className="p-2 bg-[#1E293B] rounded text-xs">
                      <p className="text-white font-medium">{scheme.name}</p>
                      <p className="text-gray-500">{scheme.category}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NetworkGraph;
