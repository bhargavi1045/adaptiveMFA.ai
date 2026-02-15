import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/common/Button';
import { ROUTES } from '@/utils/constants';
import { sessionService } from '@/services/api/sessionService';
import {
  Shield,
  Brain,
  Network,
  TrendingUp,
  CheckCircle,
  AlertTriangle,
  XCircle,
  LogOut,
  Settings,
  Clock,
  MapPin,
  Cpu,
  Database,
  Zap,
  GitBranch,
  Loader,
} from 'lucide-react';

interface DashboardData {
  user: {
    email: string;
    mfa_enabled: boolean;
    created_at: string;
    last_login?: string;
  };
  risk_assessment: {
    risk_score: number;
    risk_level: string;
    anomaly_score: number;
    device_known: boolean;
    device_fingerprint?: string;
    device_status?: string; 
    location: string;
    location_data?: any; 
    ip_address: string;
    timestamp: string;
    explanation: string;
    mfa_required: boolean;
  } | null;
  rag_insights: {
    similar_cases: Array<{
      explanation: string;
      outcome: string;
      similarity_score: number;
      location: string;
      timestamp: string;
    }>;
    total_found: number;
    retrieval_method: string;
    embedding_model: string;
  } | null;
  ml_analysis: {
    model_used: string;
    anomaly_score: number;
    behavior_risk: string;
    features_analyzed: string[];
  };
  workflow_info: {
    pipeline: string;
    technologies: string[];
  };
  sessions: Array<{
    id: string;
    device_fingerprint?: string;
    device_display?: string; 
    location?: string; 
    ip_address?: string;
    created_at: string;
    is_active: boolean;
  }>;
  login_history: Array<{
    id: string;
    timestamp: string;
    ip_address?: string;
    location: string;
    device_fingerprint?: string;
    device_display?: string; 
    device_known: boolean;
    device_status?: string; 
    risk_score: number;
    risk_level: string;
    user_action: string;
  }>;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError('');

    try {
      const response = await sessionService.getFullDashboard();
      setDashboardData(response);
    } catch (err: any) {
      console.error('Dashboard fetch error:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate(ROUTES.LOGIN);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchDashboardData();
    setIsRefreshing(false);
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'low':
        return 'bg-green-950 text-green-400 border-green-800';
      case 'medium':
        return 'bg-yellow-950 text-yellow-400 border-yellow-800';
      case 'high':
        return 'bg-red-950 text-red-400 border-red-800';
      default:
        return 'bg-gray-900 text-gray-400 border-gray-700';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'low':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'medium':
        return <AlertTriangle className="h-6 w-6 text-yellow-500" />;
      case 'high':
        return <XCircle className="h-6 w-6 text-red-500" />;
      default:
        return <Shield className="h-6 w-6 text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <div className="text-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-700 border-t-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading dashboard with real-time data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950 p-4">
        <div className="max-w-md w-full bg-gray-900 rounded-lg shadow p-6 border border-gray-800">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-center mb-2 text-white">Error Loading Dashboard</h2>
          <p className="text-gray-400 text-center mb-4">{error}</p>
          <Button onClick={fetchDashboardData} className="w-full">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!dashboardData) return null;

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Security Dashboard</h1>
                <p className="text-sm text-gray-400">Welcome, {dashboardData.user.email}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleRefresh}
                variant="secondary"
                disabled={isRefreshing}
                className="gap-2"
              >
                {isRefreshing ? (
                  <Loader className="h-4 w-4 animate-spin" />
                ) : (
                  <TrendingUp className="h-4 w-4" />
                )}
                {isRefreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
              <Button onClick={() => navigate(ROUTES.SETTINGS)} variant="secondary">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
              <Button onClick={handleLogout} variant="ghost">
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        
        {/* AI Workflow Pipeline Visualization */}
        <div className="bg-gradient-to-r from-purple-900 to-blue-900 rounded-lg shadow-lg p-6 text-white border border-purple-700">
          <div className="flex items-center mb-4">
            <GitBranch className="h-6 w-6 mr-3" />
            <h2 className="text-xl font-bold">AI-Powered Security Pipeline</h2>
          </div>
          <p className="text-purple-200 mb-4">{dashboardData.workflow_info.pipeline}</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {dashboardData.workflow_info.technologies.map((tech, index) => (
              <div key={index} className="bg-white/10 rounded-lg p-3 backdrop-blur-sm border border-white/20">
                <Zap className="h-4 w-4 mb-1" />
                <p className="text-sm font-medium">{tech}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-gray-900 rounded-lg shadow p-6 border-l-4 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Security Status</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {dashboardData.risk_assessment?.risk_level.toUpperCase() || 'N/A'}
                </p>
              </div>
              {dashboardData.risk_assessment && getRiskIcon(dashboardData.risk_assessment.risk_level)}
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6 border-l-4 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">MFA Status</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {dashboardData.user.mfa_enabled ? 'Enabled' : 'Disabled'}
                </p>
              </div>
              <Shield className={`h-8 w-8 ${dashboardData.user.mfa_enabled ? 'text-green-500' : 'text-gray-600'}`} />
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6 border-l-4 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">ML Anomaly Score</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {dashboardData.risk_assessment ? (dashboardData.risk_assessment.anomaly_score * 100).toFixed(0) + '%' : 'N/A'}
                </p>
              </div>
              <Brain className="h-8 w-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6 border-l-4 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">RAG Cases Found</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {dashboardData.rag_insights?.total_found || 0}
                </p>
              </div>
              <Database className="h-8 w-8 text-indigo-500" />
            </div>
          </div>
        </div>

        {/* Main Security Assessment Section - RAG + LangGraph Showcase */}
        {dashboardData.risk_assessment && (
          <div className="bg-gray-900 rounded-lg shadow-lg border-2 border-gray-800">
            <div className="bg-gradient-to-r from-blue-950 to-indigo-950 px-6 py-4 border-b border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Network className="h-6 w-6 text-blue-400 mr-3" />
                  <div>
                    <h2 className="text-lg font-bold text-white">
                      RAG-Enhanced Risk Assessment
                    </h2>
                    <p className="text-sm text-gray-400">
                      ML + Vector Retrieval + LLM Explanation
                    </p>
                  </div>
                </div>
                <div className={`px-4 py-2 rounded-lg border-2 font-bold ${getRiskColor(dashboardData.risk_assessment.risk_level)}`}>
                  {dashboardData.risk_assessment.risk_level.toUpperCase()}
                </div>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Risk Score Bar */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-gray-300">Risk Score</span>
                  <span className="text-2xl font-bold text-white">
                    {(dashboardData.risk_assessment.risk_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full transition-all duration-500 ${
                      dashboardData.risk_assessment.risk_level === 'low'
                        ? 'bg-green-600'
                        : dashboardData.risk_assessment.risk_level === 'medium'
                        ? 'bg-yellow-600'
                        : 'bg-red-600'
                    }`}
                    style={{ width: `${dashboardData.risk_assessment.risk_score * 100}%` }}
                  />
                </div>
              </div>

              {/* AI Explanation */}
              <div className={`rounded-lg border-2 p-5 ${getRiskColor(dashboardData.risk_assessment.risk_level)}`}>
                <div className="flex items-start">
                  <Brain className="h-6 w-6 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-bold mb-2 text-lg">LLM-Generated Analysis</h3>
                    <p className="leading-relaxed">{dashboardData.risk_assessment.explanation}</p>
                  </div>
                </div>
              </div>

              {/* ML Analysis Details */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-gray-800 rounded-lg p-4 border border-purple-900">
                  <div className="flex items-center mb-3">
                    <Cpu className="h-5 w-5 text-purple-400 mr-2" />
                    <h4 className="font-semibold text-purple-300">ML Model Analysis</h4>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Model:</span>
                      <span className="font-medium text-gray-200">{dashboardData.ml_analysis.model_used}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Anomaly Score:</span>
                      <span className="font-medium text-gray-200">
                        {(dashboardData.ml_analysis.anomaly_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Behavior Risk:</span>
                      <span className="font-medium text-gray-200 uppercase">
                        {dashboardData.ml_analysis.behavior_risk}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800 rounded-lg p-4 border border-blue-900">
                  <div className="flex items-center mb-3">
                    <MapPin className="h-5 w-5 text-blue-400 mr-2" />
                    <h4 className="font-semibold text-blue-300">
                      {/*Real-time location display */}
                      Login Context (Real-Time)
                    </h4>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Location:</span>
                      <span className="font-medium text-gray-200">
                        {dashboardData.risk_assessment.location || 'Fetching...'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">IP Address:</span>
                      <span className="font-medium text-gray-200">{dashboardData.risk_assessment.ip_address}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Device:</span>
                      <span className={`font-medium ${
                        dashboardData.risk_assessment.device_known 
                          ? 'text-green-400' 
                          : 'text-orange-400'
                      }`}>
                        {/*Device status from database */}
                        {dashboardData.risk_assessment.device_status || 'Checking...'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* RAG Retrieved Similar Cases */}
              {dashboardData.rag_insights && dashboardData.rag_insights.similar_cases.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <Database className="h-6 w-6 text-indigo-400 mr-2" />
                      <h3 className="text-lg font-bold text-white">
                        RAG: Similar Historical Patterns
                      </h3>
                    </div>
                    <div className="text-xs bg-indigo-950 text-indigo-300 px-3 py-1 rounded-full font-medium border border-indigo-800">
                      {dashboardData.rag_insights.retrieval_method}
                    </div>
                  </div>

                  <div className="space-y-3">
                    {dashboardData.rag_insights.similar_cases.map((case_item, index) => (
                      <div
                        key={index}
                        className="bg-gray-800 rounded-lg p-4 border-2 border-indigo-900 hover:border-indigo-700 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <p className="text-sm text-gray-200 font-medium mb-2">{case_item.explanation}</p>
                            <div className="flex items-center space-x-3 text-xs text-gray-400">
                              <span className="flex items-center">
                                <MapPin className="h-3 w-3 mr-1" />
                                {case_item.location || 'Unknown Location'}
                              </span>
                              <span className="flex items-center">
                                <Clock className="h-3 w-3 mr-1" />
                                {new Date(case_item.timestamp).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4 text-right">
                            <div className="text-lg font-bold text-indigo-400">
                              {(case_item.similarity_score * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-indigo-400">similarity</div>
                          </div>
                        </div>
                        <div>
                          <span
                            className={`inline-block text-xs px-3 py-1 rounded-full font-medium ${
                              case_item.outcome === 'approved'
                                ? 'bg-green-950 text-green-400'
                                : 'bg-red-950 text-red-400'
                            }`}
                          >
                            Outcome: {case_item.outcome}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 p-3 bg-gray-800 rounded-lg border border-gray-700">
                    <div className="flex items-center text-xs text-gray-400">
                      <TrendingUp className="h-4 w-4 mr-2" />
                      <span>
                        Using <strong>{dashboardData.rag_insights.embedding_model}</strong> for semantic similarity
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Features Analyzed */}
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <h4 className="font-semibold text-white mb-3 flex items-center">
                  <Zap className="h-5 w-5 mr-2 text-gray-400" />
                  Features Analyzed by ML Model
                </h4>
                <div className="flex flex-wrap gap-2">
                  {dashboardData.ml_analysis.features_analyzed.map((feature, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-gray-700 text-sm text-gray-300 rounded-full border border-gray-600"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Login History */}
         {dashboardData.login_history.length > 0 && (
  <div className="bg-gray-900 rounded-lg shadow border border-gray-800">
    <div className="px-6 py-4 border-b border-gray-800">
      <h2 className="text-lg font-semibold flex items-center text-white">
        <Clock className="h-5 w-5 mr-2 text-blue-400" />
        Recent Login History ({dashboardData.login_history.length})
      </h2>
    </div>
    <div className="divide-y divide-gray-800">
      {dashboardData.login_history.slice(0, 10).map((event) => (
        <div key={event.id} className="p-4 hover:bg-gray-800 transition-colors">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3 flex-1">
              <MapPin className="h-5 w-5 text-gray-600" />
              <div className="flex-1">
                <p className="font-medium text-white">
                  {event.location || 'Unknown Location'}
                </p>
                
                <p className="text-sm text-gray-400">
                  {/* Show device fingerprint if available */}
                  {event.device_fingerprint ? (
                    <>
                      <span className="font-mono bg-gray-800 px-2 py-1 rounded text-xs text-gray-300">
                        {event.device_fingerprint.substring(0, 8)}...
                      </span>
                      <span className="ml-2">•</span>
                      <span className={`ml-2 font-medium ${
                        event.device_known 
                          ? 'text-green-400' 
                          : 'text-orange-400'
                      }`}>
                        {event.device_known ? '✓ Known' : 'New Device'}
                      </span>
                    </>
                  ) : (
                    <>
                      {event.device_display || 'Unknown Device'}
                      <span className="ml-2">•</span>
                      <span className={`ml-2 ${
                        event.device_known 
                          ? 'text-green-400' 
                          : 'text-orange-400'
                      }`}>
                        {event.device_status || 'New'}
                      </span>
                    </>
                  )}
                </p>
              </div>
            </div>
            
            {/* RISK SCORE BADGE & TIMESTAMP */}
            <div className="text-right">
              <div className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                event.risk_level === 'low' 
                  ? 'bg-green-950 text-green-400'
                  : event.risk_level === 'medium'
                  ? 'bg-yellow-950 text-yellow-400'
                  : 'bg-red-950 text-red-400'
              }`}>
                {event.risk_level?.toUpperCase()}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(event.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
)}
      </main>
    </div>
  );
};

export default Dashboard;