import React, { useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';

interface AgentStateInfo {
  status: 'idle' | 'running' | 'success' | 'warning' | 'failure';
  confidence?: number;
}

interface FlowCanvasProps {
  agentStates?: Record<string, AgentStateInfo>;
}

export const FlowCanvas: React.FC<FlowCanvasProps> = ({ agentStates = {} }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'border-blue-500 bg-blue-950/90 text-blue-200 shadow-lg shadow-blue-500/20';
      case 'success':
        return 'border-green-500 bg-green-950/90 text-green-200';
      case 'warning':
        return 'border-amber-500 bg-amber-950/90 text-amber-200';
      case 'failure':
        return 'border-red-500 bg-red-950/90 text-red-200';
      default: // idle
        return 'border-slate-800 bg-slate-900/90 text-slate-400';
    }
  };

  useEffect(() => {
    // 1. Define nodes list with positions
    const agentConfigs = [
      { id: 'CommanderAgent', name: 'Commander Agent', x: 350, y: 10, type: 'input' },
      { id: 'IncidentAnalysisAgent', name: 'Incident Analysis', x: 100, y: 110 },
      { id: 'WeatherAgent', name: 'Weather Agent', x: 350, y: 110 },
      { id: 'PredictionAgent', name: 'Prediction Agent', x: 600, y: 110 },
      
      // Parallel layer
      { id: 'MedicalAgent', name: 'Medical Agent', x: 20, y: 220 },
      { id: 'ShelterAgent', name: 'Shelter Agent', x: 160, y: 220 },
      { id: 'VolunteerAgent', name: 'Volunteer Agent', x: 300, y: 220 },
      { id: 'TranslationAgent', name: 'Translation Agent', x: 440, y: 220 },
      { id: 'AccessibilityAgent', name: 'Accessibility Agent', x: 580, y: 220 },
      { id: 'FamilyReunificationAgent', name: 'Family Reunification', x: 720, y: 220 },
      
      // Allocators & Auditor
      { id: 'ResourceAllocationAgent', name: 'Resource Allocation', x: 350, y: 330 },
      { id: 'DecisionAuditor', name: 'Decision Auditor', x: 350, y: 430, type: 'output' }
    ];

    const flowNodes: Node[] = agentConfigs.map((config) => {
      const state = agentStates[config.id] || { status: 'idle' };
      const statusColorClass = getStatusColor(state.status);
      const isRunning = state.status === 'running';

      return {
        id: config.id,
        type: config.type || 'default',
        position: { x: config.x, y: config.y },
        style: {
          padding: '8px 12px',
          borderRadius: '8px',
          width: 140,
          fontSize: '11px',
          fontWeight: 600,
          border: '1.5px solid',
          transition: 'all 0.3s ease'
        },
        className: statusColorClass,
        data: {
          label: (
            <div className="flex flex-col text-left">
              <div className="flex justify-between items-center">
                <span>{config.name}</span>
                {isRunning && (
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                )}
              </div>
              {state.confidence !== undefined && state.confidence > 0 && (
                <span className="text-[9px] font-mono text-slate-400 mt-1">
                  Conf: {(state.confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
          )
        }
      };
    });

    // 2. Define edges showing orchestration mapping
    const flowEdges: Edge[] = [
      // Commander links to inputs
      { id: 'e-cmd-inc', source: 'CommanderAgent', target: 'IncidentAnalysisAgent', animated: agentStates['IncidentAnalysisAgent']?.status === 'running' },
      { id: 'e-cmd-wea', source: 'CommanderAgent', target: 'WeatherAgent', animated: agentStates['WeatherAgent']?.status === 'running' },
      { id: 'e-cmd-prd', source: 'CommanderAgent', target: 'PredictionAgent', animated: agentStates['PredictionAgent']?.status === 'running' },
      
      // Incident analysis links to forecast agents
      { id: 'e-inc-wea', source: 'IncidentAnalysisAgent', target: 'WeatherAgent' },
      { id: 'e-inc-prd', source: 'IncidentAnalysisAgent', target: 'PredictionAgent' },
      { id: 'e-wea-prd', source: 'WeatherAgent', target: 'PredictionAgent' },
      
      // Forecasts link to operational units
      { id: 'e-wea-trans', source: 'WeatherAgent', target: 'TranslationAgent' },
      { id: 'e-prd-res', source: 'PredictionAgent', target: 'ResourceAllocationAgent' },

      // Parallel triggers
      { id: 'e-inc-med', source: 'IncidentAnalysisAgent', target: 'MedicalAgent' },
      { id: 'e-inc-shl', source: 'IncidentAnalysisAgent', target: 'ShelterAgent' },
      { id: 'e-inc-vol', source: 'IncidentAnalysisAgent', target: 'VolunteerAgent' },
      { id: 'e-shl-acc', source: 'ShelterAgent', target: 'AccessibilityAgent' },
      { id: 'e-inc-fam', source: 'IncidentAnalysisAgent', target: 'FamilyReunificationAgent' },

      // Responders link to Allocation
      { id: 'e-med-res', source: 'MedicalAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-shl-res', source: 'ShelterAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-vol-res', source: 'VolunteerAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-acc-res', source: 'AccessibilityAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-fam-res', source: 'FamilyReunificationAgent', target: 'ResourceAllocationAgent' },

      // Allocation and translation feeds Auditor
      { id: 'e-res-aud', source: 'ResourceAllocationAgent', target: 'DecisionAuditor', animated: agentStates['DecisionAuditor']?.status === 'running' },
      { id: 'e-trans-aud', source: 'TranslationAgent', target: 'DecisionAuditor' }
    ];

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [agentStates, setNodes, setEdges]);

  return (
    <div className="w-full h-full flex flex-col">
      <div className="p-4 bg-slate-900 border-b border-slate-800 flex justify-between items-center">
        <div>
          <h2 className="text-sm font-bold tracking-wider text-slate-100 uppercase">Agent Execution Pipeline</h2>
          <p className="text-[10px] text-slate-400 font-mono mt-0.5">Model Context Protocol Graph State</p>
        </div>
      </div>
      
      <div className="flex-1 min-h-[400px] h-full relative z-0">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          fitViewOptions={{ padding: 0.15 }}
        >
          <Background color="#1e293b" gap={16} size={1} />
          <Controls className="bg-slate-800 border-slate-700 text-slate-100 fill-slate-100" />
          <MiniMap 
            nodeColor={() => '#1e293b'} 
            maskColor="rgba(15, 23, 42, 0.4)"
            className="bg-slate-900 border border-slate-800 rounded-lg hidden sm:block"
          />
        </ReactFlow>
      </div>
    </div>
  );
};
export default FlowCanvas;
