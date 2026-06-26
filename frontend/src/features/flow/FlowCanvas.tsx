import React, { useEffect, useState } from 'react';
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
import { X, Play, Layers, Activity } from 'lucide-react';

interface AgentStateInfo {
  status: 'idle' | 'running' | 'success' | 'warning' | 'failure';
  confidence?: number;
}

interface FlowCanvasProps {
  agentStates?: Record<string, AgentStateInfo>;
  orchestrationResult?: any;
}

interface AgentMetadata {
  name: string;
  purpose: string;
  skills: string[];
  mcpTools: string[];
  subscriptions: string[];
}

const AGENT_METADATA_REGISTRY: Record<string, AgentMetadata> = {
  CommanderAgent: {
    name: 'Commander Agent',
    purpose: 'Core coordinator and orchestrator. Decomposes queries, delegates parallel workflows to specialist agents, aggregates decisions, monitors execution confidence levels, and manages fallback replanning runs.',
    skills: ['Coordination & Planning'],
    mcpTools: [],
    subscriptions: ['IncidentDetected', 'RoadClosed', 'ShelterFull', 'HospitalOverloaded', 'VolunteerAssigned', 'ResourceDispatched', 'MissingPersonReported', 'WeatherAlert', 'PredictionUpdated']
  },
  IncidentAnalysisAgent: {
    name: 'Incident Analysis Agent',
    purpose: 'Parses raw disaster logs, telemetry feeds, and visual data. Triggers the primary incident classification, locates coordinates, and estimates damage levels using Gemini Vision capabilities.',
    skills: ['VisionSkill', 'NavigationSkill'],
    mcpTools: ['roadStatus', 'estimateDisasterDamage'],
    subscriptions: ['IncidentDetected', 'RoadClosed']
  },
  WeatherAgent: {
    name: 'Weather Prediction Agent',
    purpose: 'Retrieves localized climate indexes, wind speeds, and precipitation rates. Broadcasts critical weather safety alerts if thresholds are breached.',
    skills: ['WeatherSkill'],
    mcpTools: ['forecastWeather'],
    subscriptions: ['IncidentDetected', 'WeatherAlert']
  },
  PredictionAgent: {
    name: 'Prediction Agent',
    purpose: 'Projects future disaster trajectories and resource depletion rates. Uses historical averages to recommend preemptive inventory restock coordinates.',
    skills: ['WeatherSkill', 'ResourceSkill'],
    mcpTools: ['estimateDisasterDamage', 'forecastWeather'],
    subscriptions: ['IncidentDetected', 'WeatherAlert', 'PredictionUpdated']
  },
  MedicalAgent: {
    name: 'Medical Agent',
    purpose: 'Monitors intensive care bed availability, filters compatible emergency clinics, tracks drug stock levels, and estimates triage patient priority counts.',
    skills: ['MedicalSkill', 'ResourceSkill'],
    mcpTools: ['findHospital'],
    subscriptions: ['IncidentDetected', 'HospitalOverloaded']
  },
  ShelterAgent: {
    name: 'Shelter Agent',
    purpose: 'Searches for secure emergency safe zones, audits sleeping capacities, and checks for available blankets and supplies inside the shelters.',
    skills: ['NavigationSkill', 'SearchSkill'],
    mcpTools: ['findShelter'],
    subscriptions: ['IncidentDetected', 'ShelterFull']
  },
  VolunteerAgent: {
    name: 'Volunteer Coordination Agent',
    purpose: 'Coordinates deployment rosters for registered doctors, nurses, and NGOs. Matches responders based on locations, skill sets, and schedules.',
    skills: ['ResourceSkill', 'CommunicationSkill'],
    mcpTools: ['findVolunteer'],
    subscriptions: ['IncidentDetected', 'VolunteerAssigned']
  },
  TranslationAgent: {
    name: 'Translation Agent',
    purpose: 'Provides multilingual support for crisis centers. Translates localized safety maps, emergency broadcasts, and evacuation routes into target languages.',
    skills: ['TranslationSkill'],
    mcpTools: ['translateMessage'],
    subscriptions: ['IncidentDetected', 'WeatherAlert']
  },
  AccessibilityAgent: {
    name: 'Accessibility Agent',
    purpose: 'Audits physical locations for wheel-chair layout support, checks path gradients, and ensures emergency updates support simplified layout formats.',
    skills: ['VisionSkill', 'TranslationSkill'],
    mcpTools: ['findShelter'],
    subscriptions: ['IncidentDetected', 'ShelterFull']
  },
  FamilyReunificationAgent: {
    name: 'Family Reunification Agent',
    purpose: 'Cross-checks safe-zone logs and emergency databases to reconcile missing persons with registered family group records.',
    skills: ['SearchSkill', 'CommunicationSkill'],
    mcpTools: ['locateFamily', 'searchMissingPerson'],
    subscriptions: ['IncidentDetected', 'MissingPersonReported']
  },
  ResourceAllocationAgent: {
    name: 'Resource Allocation Agent',
    purpose: 'Audits central warehouses, manages logistics transport requests, dispatches supply trucks, and initiates automated purchase orders.',
    skills: ['ResourceSkill', 'NavigationSkill'],
    mcpTools: ['resourceInventory', 'dispatchResources'],
    subscriptions: ['IncidentDetected', 'RoadClosed', 'ResourceDispatched']
  },
  DecisionAuditor: {
    name: 'Decision Auditor Agent',
    purpose: 'Validates safety constraints of aggregate command center proposals. Audits shelter capacities, ADA features, and checks for model hallucinations or low confidence scores.',
    skills: ['Compliance Auditing'],
    mcpTools: [],
    subscriptions: ['audit_request', 'task_completed']
  }
};

export const FlowCanvas: React.FC<FlowCanvasProps> = ({ 
  agentStates = {}, 
  orchestrationResult = null 
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  const getStatusColor = (status: string, isSelected: boolean) => {
    const ring = isSelected ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-900' : '';
    switch (status) {
      case 'running':
        return `${ring} border-blue-500 bg-blue-950/90 text-blue-200 shadow-lg shadow-blue-500/20`;
      case 'success':
        return `${ring} border-green-500 bg-green-950/90 text-green-200`;
      case 'warning':
        return `${ring} border-amber-500 bg-amber-950/90 text-amber-200`;
      case 'failure':
        return `${ring} border-red-500 bg-red-950/90 text-red-200`;
      default: // idle
        return `${ring} border-slate-800 bg-slate-900/90 text-slate-400`;
    }
  };

  useEffect(() => {
    const agentConfigs = [
      { id: 'CommanderAgent', name: 'Commander Agent', x: 380, y: 10, type: 'input' },
      { id: 'IncidentAnalysisAgent', name: 'Incident Analysis', x: 120, y: 110 },
      { id: 'WeatherAgent', name: 'Weather Agent', x: 380, y: 110 },
      { id: 'PredictionAgent', name: 'Prediction Agent', x: 640, y: 110 },
      
      // Parallel layer
      { id: 'MedicalAgent', name: 'Medical Agent', x: 20, y: 220 },
      { id: 'ShelterAgent', name: 'Shelter Agent', x: 160, y: 220 },
      { id: 'VolunteerAgent', name: 'Volunteer Agent', x: 300, y: 220 },
      { id: 'TranslationAgent', name: 'Translation Agent', x: 440, y: 220 },
      { id: 'AccessibilityAgent', name: 'Accessibility Agent', x: 580, y: 220 },
      { id: 'FamilyReunificationAgent', name: 'Family Reunification', x: 720, y: 220 },
      
      // Allocators & Auditor
      { id: 'ResourceAllocationAgent', name: 'Resource Allocation', x: 380, y: 330 },
      { id: 'DecisionAuditor', name: 'Decision Auditor', x: 380, y: 430, type: 'output' }
    ];

    const flowNodes: Node[] = agentConfigs.map((config) => {
      const state = agentStates[config.id] || { status: 'idle' };
      const isSelected = selectedAgentId === config.id;
      const statusColorClass = getStatusColor(state.status, isSelected);
      const isRunning = state.status === 'running';

      return {
        id: config.id,
        type: config.type || 'default',
        position: { x: config.x, y: config.y },
        style: {
          padding: '10px 14px',
          borderRadius: '8px',
          width: 145,
          fontSize: '11px',
          fontWeight: 600,
          border: '1.5px solid',
          cursor: 'pointer',
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

    const flowEdges: Edge[] = [
      { id: 'e-cmd-inc', source: 'CommanderAgent', target: 'IncidentAnalysisAgent', animated: agentStates['IncidentAnalysisAgent']?.status === 'running' },
      { id: 'e-cmd-wea', source: 'CommanderAgent', target: 'WeatherAgent', animated: agentStates['WeatherAgent']?.status === 'running' },
      { id: 'e-cmd-prd', source: 'CommanderAgent', target: 'PredictionAgent', animated: agentStates['PredictionAgent']?.status === 'running' },
      
      { id: 'e-inc-wea', source: 'IncidentAnalysisAgent', target: 'WeatherAgent' },
      { id: 'e-inc-prd', source: 'IncidentAnalysisAgent', target: 'PredictionAgent' },
      { id: 'e-wea-prd', source: 'WeatherAgent', target: 'PredictionAgent' },
      
      { id: 'e-wea-trans', source: 'WeatherAgent', target: 'TranslationAgent' },
      { id: 'e-prd-res', source: 'PredictionAgent', target: 'ResourceAllocationAgent' },

      { id: 'e-inc-med', source: 'IncidentAnalysisAgent', target: 'MedicalAgent' },
      { id: 'e-inc-shl', source: 'IncidentAnalysisAgent', target: 'ShelterAgent' },
      { id: 'e-inc-vol', source: 'IncidentAnalysisAgent', target: 'VolunteerAgent' },
      { id: 'e-shl-acc', source: 'ShelterAgent', target: 'AccessibilityAgent' },
      { id: 'e-inc-fam', source: 'IncidentAnalysisAgent', target: 'FamilyReunificationAgent' },

      { id: 'e-med-res', source: 'MedicalAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-shl-res', source: 'ShelterAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-vol-res', source: 'VolunteerAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-acc-res', source: 'AccessibilityAgent', target: 'ResourceAllocationAgent' },
      { id: 'e-fam-res', source: 'FamilyReunificationAgent', target: 'ResourceAllocationAgent' },

      { id: 'e-res-aud', source: 'ResourceAllocationAgent', target: 'DecisionAuditor', animated: agentStates['DecisionAuditor']?.status === 'running' },
      { id: 'e-trans-aud', source: 'TranslationAgent', target: 'DecisionAuditor' }
    ];

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [agentStates, selectedAgentId, setNodes, setEdges]);

  const meta = selectedAgentId ? AGENT_METADATA_REGISTRY[selectedAgentId] : null;
  const agentState = selectedAgentId ? (agentStates[selectedAgentId] || { status: 'idle' }) : null;
  
  const runtimeResult = selectedAgentId && orchestrationResult && orchestrationResult.agent_responses 
    ? (orchestrationResult.agent_responses[selectedAgentId] || orchestrationResult.audit_report) 
    : null;

  return (
    <div className="w-full h-full flex flex-col">
      <div className="p-4 bg-slate-900 border-b border-slate-800 flex justify-between items-center">
        <div>
          <h2 className="text-sm font-bold tracking-wider text-slate-100 uppercase">Agent Execution Pipeline</h2>
          <p className="text-[10px] text-slate-400 font-mono mt-0.5">Click any node to inspect agent skills, tools, and shared memory logs</p>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col md:flex-row relative min-h-[400px] h-full overflow-hidden">
        {/* Flow Canvas */}
        <div className="flex-1 relative z-0 h-full min-h-[350px]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={(_, node) => setSelectedAgentId(node.id)}
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

        {/* Dynamic Agent Inspector Panel */}
        {selectedAgentId && meta && (
          <div className="w-full md:w-[350px] shrink-0 border-t md:border-t-0 md:border-l border-slate-800 bg-slate-900/95 overflow-y-auto p-4 flex flex-col gap-4 text-slate-100 z-10">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <div className="flex flex-col">
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">Agent Inspector</span>
                <h3 className="text-sm font-bold text-slate-100">{meta.name}</h3>
              </div>
              <button 
                onClick={() => setSelectedAgentId(null)}
                className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* State & Status info */}
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-850">
              <div className="flex items-center gap-2">
                <Activity size={13} className="text-slate-400" />
                <span className="text-xs text-slate-300">Status:</span>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border capitalize ${
                agentState?.status === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' :
                agentState?.status === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
                agentState?.status === 'failure' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                agentState?.status === 'running' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400 animate-pulse' :
                'bg-slate-800 border-slate-700 text-slate-400'
              }`}>
                {agentState?.status || 'idle'}
              </span>
            </div>

            {/* Purpose */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Cognitive Instruction</span>
              <p className="text-xs text-slate-300 leading-relaxed font-mono bg-slate-950 p-2.5 rounded border border-slate-850">
                "{meta.purpose}"
              </p>
            </div>

            {/* Skills */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Layers size={11} className="text-blue-400" />
                Reusable Skills
              </span>
              <div className="flex flex-wrap gap-1.5">
                {meta.skills.map((skill, i) => (
                  <span key={i} className="text-[10px] bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* MCP Tools */}
            {meta.mcpTools.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Play size={11} className="text-purple-400" />
                  Model Context Tools (MCP)
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {meta.mcpTools.map((tool, i) => (
                    <span key={i} className="text-[10px] font-mono bg-purple-500/10 border border-purple-500/20 text-purple-400 px-2 py-0.5 rounded">
                      {tool}()
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Subscription Topics */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Event Bus subscriptions</span>
              <div className="flex flex-wrap gap-1.5">
                {meta.subscriptions.map((topic, i) => (
                  <span key={i} className="text-[9px] font-mono bg-slate-950 text-slate-400 px-1.5 py-0.5 rounded border border-slate-850">
                    {topic}
                  </span>
                ))}
              </div>
            </div>

            {/* Live Shared Memory Logs */}
            <div className="flex flex-col gap-1.5 mt-2 border-t border-slate-800 pt-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Shared Memory Records</span>
              {runtimeResult ? (
                <div className="flex flex-col gap-2.5">
                  {runtimeResult.confidence_score !== undefined && (
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-slate-400">Confidence Score:</span>
                      <span className="font-mono text-slate-200 font-bold">
                        {(runtimeResult.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}

                  {runtimeResult.reasons && runtimeResult.reasons.length > 0 && (
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] text-slate-400">Observations / Log:</span>
                      <ul className="list-disc pl-4 text-[11px] text-slate-300 flex flex-col gap-1 leading-relaxed">
                        {runtimeResult.reasons.map((reason: string, i: number) => (
                          <li key={i}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {runtimeResult.data && Object.keys(runtimeResult.data).length > 0 && (
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] text-slate-400">Supporting Evidence:</span>
                      <pre className="text-[9px] font-mono bg-slate-950 p-2 rounded border border-slate-850 overflow-x-auto max-h-40 text-slate-300">
                        {JSON.stringify(runtimeResult.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-[10px] font-mono text-slate-500 italic p-3 bg-slate-950/50 rounded border border-slate-900 text-center">
                  No records stored yet. Start a simulation scenario or run orchestration to populate shared memory.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default FlowCanvas;
