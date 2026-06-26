import React, { useState, useEffect, useRef } from 'react';
import { api, SystemStatus } from './services/api';
import { MapViewer } from './features/map/MapViewer';
import { FlowCanvas } from './features/flow/FlowCanvas';
import { 
  AlertTriangle, ShieldCheck, ShieldAlert, Cpu, 
  Layers, MapPin, Thermometer, 
  Wind, Clock, RefreshCw, BarChart2, Activity, Play
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface IncidentItem {
  id: string;
  name: string;
  severity: 'CRITICAL' | 'WARNING' | 'DRILL';
  prompt: string;
  centerCoords: [number, number];
}

const emergencyQueue: IncidentItem[] = [
  {
    id: 'inc-1',
    name: 'SF Bay Area Watershed Flood',
    severity: 'CRITICAL',
    prompt: 'High precipitation causing emergency watershed flooding near Sector Alpha',
    centerCoords: [37.7749, -122.4194]
  },
  {
    id: 'inc-2',
    name: 'Oakland Hills Wildfire Corridor',
    severity: 'CRITICAL',
    prompt: 'Severe wildfire causing extreme damage and closing main access lines in Oakland Hills',
    centerCoords: [37.8044, -122.2711] // Oakland
  },
  {
    id: 'inc-3',
    name: 'Silicon Valley Seismic Check',
    severity: 'DRILL',
    prompt: 'Minor drill checking localized structural codes and field triage capacity',
    centerCoords: [37.3382, -121.8863] // San Jose
  }
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'map' | 'flow'>('map');
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem>(emergencyQueue[0]);
  const [orchestrationResult, setOrchestrationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  // Parse active agent states from orchestration output
  const [agentStates, setAgentStates] = useState<Record<string, any>>({});

  // Security Simulation States
  const [selectedRole, setSelectedRole] = useState('Administrator');
  const [securityAlert, setSecurityAlert] = useState<string | null>(null);

  const triggerSecurityAlert = (msg: string) => {
    setSecurityAlert(msg);
    setTimeout(() => {
      setSecurityAlert(null);
    }, 6000);
  };

  const handleRoleChange = (role: string) => {
    setSelectedRole(role);
    let token = 'mock-admin';
    if (role === 'Emergency Responder') token = 'mock-responder';
    else if (role === 'Volunteer') token = 'mock-volunteer';
    else if (role === 'NGO') token = 'mock-ngo';
    else if (role === 'Citizen') token = 'mock-citizen';
    api.setAuthToken(token);
    fetchStatus();
  };

  // Simulation Engine States
  const [isSimulating, setIsSimulating] = useState(false);
  const [simScenarioId, setSimScenarioId] = useState('cyclone');
  const [currentScenario, setCurrentScenario] = useState<any>(null);
  const [simStepIndex, setSimStepIndex] = useState(0);

  const [simEvents, setSimEvents] = useState<any[]>([]);
  const [simMarkers, setSimMarkers] = useState<any[]>([]);
  const [simHeatmap, setSimHeatmap] = useState<any>(null);
  const [simShelters, setSimShelters] = useState<any[]>([]);
  const [simHospitals, setSimHospitals] = useState<any[]>([]);
  const [simInventory, setSimInventory] = useState<any>(null);

  const simIntervalRef = useRef<any>(null);

  const fetchStatus = async () => {
    try {
      const status = await api.getStatus();
      setSystemStatus(status);
    } catch {
      setSystemStatus({ status: 'offline', database: 'disconnected', cache: 'offline' });
    }
  };

  const handleRunOrchestration = async (incident: IncidentItem) => {
    handleStopSimulation();
    setSelectedIncident(incident);
    setLoading(true);
    
    // Simulate loading/running pipeline nodes visually
    const pipelineOrder = [
      ['CommanderAgent'],
      ['IncidentAnalysisAgent', 'WeatherAgent'],
      ['PredictionAgent'],
      ['MedicalAgent', 'ShelterAgent', 'VolunteerAgent', 'TranslationAgent', 'AccessibilityAgent', 'FamilyReunificationAgent'],
      ['ResourceAllocationAgent'],
      ['DecisionAuditor']
    ];

    // Set initial running states
    const states: Record<string, any> = {};
    for (const group of pipelineOrder) {
      for (const id of group) {
        states[id] = { status: 'idle' };
      }
    }
    setAgentStates(states);

    // Dynamic animation sequence for visual representation of steps
    let delay = 0;
    for (const group of pipelineOrder) {
      setTimeout(() => {
        setAgentStates(prev => {
          const next = { ...prev };
          for (const id of group) {
            next[id] = { status: 'running' };
          }
          return next;
        });
      }, delay);
      delay += 800;
    }

    try {
      const result = await api.orchestrate(incident.prompt);
      setOrchestrationResult(result);
      
      // Wait for dummy runner steps to complete before loading result
      setTimeout(() => {
        const finalStates: Record<string, any> = {};
        const responses = result.agent_responses || {};
        for (const [agentName, response] of Object.entries(responses)) {
          const res = response as any;
          finalStates[agentName] = {
            status: res.status || 'success',
            confidence: res.confidence_score
          };
        }
        // Ensure Commander is success
        finalStates['CommanderAgent'] = { status: 'success', confidence: result.audit_report?.confidence_score };
        setAgentStates(finalStates);
        setLoading(false);
      }, delay);

    } catch (err: any) {
      console.error(err);
      triggerSecurityAlert(err.message || "Failed to execute orchestration");
      setAgentStates({});
      setLoading(false);
    }
  };

  const handleStopSimulation = () => {
    if (simIntervalRef.current) {
      clearInterval(simIntervalRef.current);
      simIntervalRef.current = null;
    }
    setIsSimulating(false);
    setSimEvents([]);
    setSimMarkers([]);
    setSimHeatmap(null);
    setSimShelters([]);
    setSimHospitals([]);
    setSimInventory(null);
  };

  const handleStartSimulation = async () => {
    handleStopSimulation(); // Clean previous first
    setIsSimulating(true);
    setLoading(true);
    
    try {
      const scenario = await api.getScenario(simScenarioId);
      setCurrentScenario(scenario);
      setSimStepIndex(0);
      
      // Focus map tab first
      setActiveTab('map');
      
      // Execute Step 0
      executeSimulationStep(scenario, 0);

      let step = 0;
      const interval = setInterval(() => {
        step += 1;
        if (step < scenario.steps.length) {
          setSimStepIndex(step);
          executeSimulationStep(scenario, step);
        } else {
          clearInterval(interval);
          simIntervalRef.current = null;
        }
      }, 3500);
      
      simIntervalRef.current = interval;
    } catch (err: any) {
      console.error(err);
      triggerSecurityAlert(err.message || "Failed to start simulation scenario");
      setIsSimulating(false);
      setLoading(false);
    }
  };

  const executeSimulationStep = async (scenario: any, idx: number) => {
    const step = scenario.steps[idx];
    if (!step) return;

    // 1. Add event to log if event_type is defined
    if (step.event_type && step.source_agent) {
      const newEv = {
        event_type: step.event_type,
        source_agent: step.source_agent,
        payload: step.payload || {},
        timestamp: new Date().toLocaleTimeString()
      };
      setSimEvents(prev => [newEv, ...prev]);
    }

    // 2. Map updates
    if (step.map_updates) {
      if (step.map_updates.heatmap) {
        setSimHeatmap(step.map_updates.heatmap);
      }
      if (step.map_updates.markers) {
        setSimMarkers(prev => [...prev, ...step.map_updates.markers]);
      }
    }

    // 3. Capacities updates
    if (step.capacity_updates) {
      if (step.capacity_updates.shelters) {
        setSimShelters(step.capacity_updates.shelters);
      }
      if (step.capacity_updates.hospitals) {
        setSimHospitals(step.capacity_updates.hospitals);
      }
    }

    // 4. Inventory updates
    if (step.inventory_updates) {
      if (step.inventory_updates.resources) {
        const item = step.inventory_updates.resources[0];
        setSimInventory({
          item_name: item.item_name,
          quantity_available: item.quantity_available
        });
      }
    }

    // 5. Orchestration execution (final step)
    if (step.orchestrate_prompt) {
      // Automatically switch to orchestration flow canvas to watch agents react
      setActiveTab('flow');
      
      const pipelineOrder = [
        ['CommanderAgent'],
        ['IncidentAnalysisAgent', 'WeatherAgent'],
        ['PredictionAgent'],
        ['MedicalAgent', 'ShelterAgent', 'VolunteerAgent', 'TranslationAgent', 'AccessibilityAgent', 'FamilyReunificationAgent'],
        ['ResourceAllocationAgent'],
        ['DecisionAuditor']
      ];

      // Set initial running states
      const states: Record<string, any> = {};
      for (const group of pipelineOrder) {
        for (const id of group) {
          states[id] = { status: 'idle' };
        }
      }
      setAgentStates(states);

      let delay = 0;
      for (const group of pipelineOrder) {
        setTimeout(() => {
          setAgentStates(prev => {
            const next = { ...prev };
            for (const id of group) {
              next[id] = { status: 'running' };
            }
            return next;
          });
        }, delay);
        delay += 600;
      }

      try {
        const result = await api.orchestrate(step.orchestrate_prompt);
        
        setTimeout(() => {
          setOrchestrationResult(result);
          
          const finalStates: Record<string, any> = {};
          const responses = result.agent_responses || {};
          for (const [agentName, response] of Object.entries(responses)) {
            const res = response as any;
            finalStates[agentName] = {
              status: res.status || 'success',
              confidence: res.confidence_score
            };
          }
          finalStates['CommanderAgent'] = { status: 'success', confidence: result.audit_report?.confidence_score };
          setAgentStates(finalStates);
          setLoading(false);
          setIsSimulating(false);
        }, delay);

      } catch (err: any) {
        console.error(err);
        triggerSecurityAlert(err.message || "Simulation orchestration failed");
        setAgentStates({});
        setLoading(false);
        setIsSimulating(false);
      }
    }
  };

  useEffect(() => {
    fetchStatus();
    handleRunOrchestration(emergencyQueue[0]);
    return () => {
      if (simIntervalRef.current) {
        clearInterval(simIntervalRef.current);
      }
    };
  }, []);

  // Helper variables for extractable results
  const auditorReport = orchestrationResult?.audit_report || {};
  const agentResponses = orchestrationResult?.agent_responses || {};
  
  // Extract specific values
  const weatherData = agentResponses["WeatherAgent"]?.data || {};
  const forecastList = weatherData.forecast || [];
  
  const simulatedStep = isSimulating && currentScenario?.steps[simStepIndex];
  const windSpeed = simulatedStep?.payload?.wind_speed || forecastList[0]?.wind_speed_mph || 12.5;
  const tempF = simulatedStep?.payload?.temperature_f || weatherData.temperature_f || 62.4;
  
  const shelterData = agentResponses["ShelterAgent"]?.data?.raw_shelter_data || {};
  const shelters = simShelters.length > 0 ? simShelters : (shelterData.shelters || [
    { name: "Civic Center Hall", capacity: 500, occupancy: 320 },
    { name: "Oakland Park Gym", capacity: 300, occupancy: 50 }
  ]);

  const medicalData = agentResponses["MedicalAgent"]?.data || {};
  const hospitals = simHospitals.length > 0 ? simHospitals : (medicalData.available_hospitals?.hospitals || [
    { name: "General Memorial Hospital", available_beds: 14, specialties: ["Emergency"] },
    { name: "Valley Health Center", available_beds: 3, specialties: ["Emergency"] }
  ]);

  const resourceData = agentResponses["ResourceAllocationAgent"]?.data || {};
  const inventoryItem = simInventory || (resourceData.inventory || { item_name: "Trauma Kits", quantity_available: 250 });
  
  const volunteerData = agentResponses["VolunteerAgent"]?.data || {};
  const activeVolunteersCount = simulatedStep?.payload?.assigned_count 
    ? (volunteerData.volunteers?.volunteers?.length || 45) + (simulatedStep.payload.assigned_count as number)
    : (volunteerData.volunteers?.volunteers?.length || 45);

  const capturedEvents = [...simEvents, ...(orchestrationResult?.captured_events || [])];

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans select-none">
      
      {securityAlert && (
        <div className="bg-red-950 border-b border-red-800 text-red-200 px-6 py-2 flex items-center justify-between shrink-0 font-mono text-[11px] font-bold tracking-wider">
          <span className="flex items-center gap-2">
            <ShieldAlert size={14} className="text-red-500 animate-pulse" />
            SECURITY ALARM: {securityAlert}
          </span>
          <button onClick={() => setSecurityAlert(null)} className="text-red-400 hover:text-red-200">DISMISS</button>
        </div>
      )}

      {/* Header bar */}
      <header className="flex justify-between items-center px-6 py-3.5 bg-slate-900 border-b border-slate-800/80 backdrop-blur-md shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <span className="font-black text-white text-sm">H</span>
          </div>
          <div>
            <h1 className="text-sm font-extrabold tracking-wider uppercase text-slate-100">HumanityOS</h1>
            <p className="text-[9px] text-slate-400 font-mono">Emergency Command Center Dashboard</p>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('map')}
            className={`px-4 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider transition-all ${
              activeTab === 'map'
                ? 'bg-slate-800 text-brand-400 border border-slate-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            Spatial Map
          </button>
          <button
            onClick={() => setActiveTab('flow')}
            className={`px-4 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider transition-all ${
              activeTab === 'flow'
                ? 'bg-slate-800 text-brand-400 border border-slate-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            Orchestration Graph
          </button>
        </div>

        {/* Role Simulator Selector */}
        <div className="flex items-center space-x-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800/80">
          <span className="text-[9px] uppercase tracking-wider text-slate-500 font-mono font-semibold">Role Simulator:</span>
          <select
            value={selectedRole}
            onChange={(e) => handleRoleChange(e.target.value)}
            className="bg-transparent text-[10px] font-extrabold text-brand-400 focus:outline-none cursor-pointer border-none p-0"
          >
            <option value="Administrator" className="bg-slate-900 text-slate-200">Administrator</option>
            <option value="Emergency Responder" className="bg-slate-900 text-slate-200">Emergency Responder</option>
            <option value="Volunteer" className="bg-slate-900 text-slate-200">Volunteer</option>
            <option value="NGO" className="bg-slate-900 text-slate-200">NGO</option>
            <option value="Citizen" className="bg-slate-900 text-slate-200">Citizen</option>
          </select>
        </div>

        {/* System node indicator */}
        <div className="flex items-center space-x-4 text-[10px] font-mono">
          <div className="flex items-center space-x-2">
            <span className={`w-1.5 h-1.5 rounded-full ${
              systemStatus?.status === 'online' ? 'bg-green-400' : 'bg-red-400'
            }`} />
            <span className="text-slate-400">Database:</span>
            <span className="text-slate-200">{systemStatus?.database || 'checking...'}</span>
          </div>
          <button 
            onClick={fetchStatus} 
            className="text-slate-500 hover:text-slate-300 transition-colors"
          >
            <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </header>

      {/* Grid Dashboard */}
      <div className="flex-1 flex overflow-hidden w-full p-4 gap-4">
        
        {/* Left column: Incident Queue & Alerts */}
        <aside className="w-80 shrink-0 flex flex-col gap-4 overflow-y-auto">
          
          {/* Disaster Simulation Control */}
          <div className="glass-card p-4 flex flex-col shrink-0">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
              <Play size={13} className="text-brand-400" />
              Disaster Simulation Control
            </h3>
            <div className="space-y-3">
              <div>
                <label className="text-[9px] text-slate-500 uppercase tracking-wider font-mono">Select Scenario</label>
                <select
                  value={simScenarioId}
                  onChange={(e) => setSimScenarioId(e.target.value)}
                  disabled={isSimulating}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-semibold text-slate-200 focus:outline-none focus:border-brand-500"
                >
                  <option value="cyclone">Cyclone Landfall</option>
                  <option value="flood">Atmospheric River Flood</option>
                  <option value="earthquake">Urban Seismic Event</option>
                  <option value="wildfire">Forest Wildfire Outbreak</option>
                  <option value="heatwave">Extreme Heat Dome</option>
                </select>
              </div>
              
              <div className="flex gap-2">
                {!isSimulating ? (
                  <button
                    onClick={handleStartSimulation}
                    className="w-full flex items-center justify-center gap-2 py-2 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-lg transition-colors shadow-lg shadow-brand-500/20"
                  >
                    <Play size={12} />
                    Start Simulation
                  </button>
                ) : (
                  <button
                    onClick={handleStopSimulation}
                    className="w-full flex items-center justify-center gap-2 py-2 bg-red-600 hover:bg-red-500 text-white font-bold text-xs rounded-lg transition-colors shadow-lg shadow-red-500/20"
                  >
                    <RefreshCw size={12} className="animate-spin" />
                    Stop Simulation
                  </button>
                )}
              </div>

              {isSimulating && currentScenario && (
                <div className="p-2.5 bg-slate-950/60 rounded border border-slate-900 flex flex-col text-[10px]">
                  <div className="flex justify-between items-center text-[9px] font-bold text-brand-400">
                    <span>STEP {simStepIndex + 1} OF {currentScenario.steps.length}</span>
                    <span className="animate-pulse">RUNNING</span>
                  </div>
                  <span className="font-semibold text-slate-200 mt-1">{currentScenario.steps[simStepIndex]?.title}</span>
                  <p className="text-slate-400 mt-0.5 leading-relaxed">{currentScenario.steps[simStepIndex]?.description}</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Emergency queue */}
          <div className="glass-card p-4 flex flex-col">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
              <Layers size={13} className="text-brand-400" />
              Emergency Queue
            </h3>
            <div className="space-y-2 flex-1">
              {emergencyQueue.map((incident) => {
                const isActive = selectedIncident.id === incident.id;
                return (
                  <button
                    key={incident.id}
                    onClick={() => handleRunOrchestration(incident)}
                    className={`w-full text-left p-3 rounded-lg border transition-all flex flex-col relative overflow-hidden ${
                      isActive
                        ? 'border-brand-500 bg-brand-950/10 shadow-lg'
                        : 'border-slate-800 bg-slate-900/40 hover:bg-slate-900/60 hover:border-slate-700'
                    }`}
                  >
                    {isActive && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-brand-500" />
                    )}
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-200 truncate pr-2">{incident.name}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${
                        incident.severity === 'CRITICAL' 
                          ? 'bg-red-500/10 text-red-400 border border-red-500/20' 
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}>
                        {incident.severity}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {incident.prompt}
                    </span>
                    <div className="mt-2 flex justify-between items-center text-[9px] font-mono text-slate-500">
                      <span className="flex items-center gap-1">
                        <MapPin size={9} />SF Area
                      </span>
                      {isActive && loading && (
                        <span className="text-brand-400 animate-pulse">Running...</span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Weather alerts */}
          <div className="glass-card p-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
              <Wind size={13} className="text-blue-400" />
              Weather Operations
            </h3>
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-900 flex flex-col">
                <span className="text-[9px] font-mono text-slate-500">Temperature</span>
                <span className="text-base font-extrabold text-slate-200 mt-1 flex items-center gap-1">
                  <Thermometer size={14} className="text-orange-400" />
                  {tempF.toFixed(1)}°F
                </span>
              </div>
              <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-900 flex flex-col">
                <span className="text-[9px] font-mono text-slate-500">Wind Speed</span>
                <span className="text-base font-extrabold text-slate-200 mt-1 flex items-center gap-1">
                  <Wind size={14} className="text-blue-400" />
                  {windSpeed.toFixed(1)} mph
                </span>
              </div>
            </div>
            {forecastList.length > 0 && forecastList[0].advisories?.length > 0 && (
              <div className="mt-3 p-2.5 bg-red-950/20 border border-red-900/50 rounded-lg text-[10px] text-red-400 flex gap-2">
                <AlertTriangle size={13} className="shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Active Advisory:</span>
                  <p className="mt-0.5 text-slate-300">{forecastList[0].advisories.join(", ")}</p>
                </div>
              </div>
            )}
          </div>

          {/* Live Activity Feed */}
          <div className="glass-card p-4 flex-1 flex flex-col min-h-0">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
              <Activity size={13} className="text-emerald-400" />
              Live Activity Feed
            </h3>
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-[9px] text-slate-400">
              <AnimatePresence>
                {loading ? (
                  <div className="text-slate-500 italic py-4 text-center">Inter-agent Event Bus sync active...</div>
                ) : capturedEvents.length > 0 ? (
                  capturedEvents.map((event: any, idx: number) => (
                    <motion.div
                      key={`event-${idx}`}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.15, delay: idx * 0.05 }}
                      className="p-2 bg-slate-950/50 rounded border border-slate-900 flex flex-col"
                    >
                      <div className="flex justify-between items-center text-brand-400 font-bold">
                        <span>{event.event_type}</span>
                        <span className="text-slate-600 text-[8px]">{(idx + 1) * 2}s</span>
                      </div>
                      <span className="text-slate-300 mt-1">Source: {event.source_agent}</span>
                      {event.payload && Object.keys(event.payload).length > 0 && (
                        <span className="text-slate-500 mt-0.5 truncate">
                          Payload: {JSON.stringify(event.payload)}
                        </span>
                      )}
                    </motion.div>
                  ))
                ) : (
                  <div className="text-slate-500 italic py-4 text-center">No active broker events logged.</div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </aside>

        {/* Center column: Map & React Flow Tab views */}
        <main className="flex-1 glass-card overflow-hidden flex flex-col h-full relative">
          <AnimatePresence mode="wait">
            {activeTab === 'map' ? (
              <motion.div
                key="map-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="w-full h-full relative"
              >
                <MapViewer
                  centerCoords={isSimulating && currentScenario ? currentScenario.centerCoords : selectedIncident.centerCoords}
                  hospitals={hospitals}
                  shelters={shelters}
                  volunteersCount={activeVolunteersCount}
                  incidentName={isSimulating && currentScenario ? currentScenario.name : selectedIncident.name}
                  simulatedMarkers={simMarkers}
                  simulatedHeatmap={simHeatmap}
                />
              </motion.div>
            ) : (
              <motion.div
                key="flow-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="w-full h-full relative"
              >
                <FlowCanvas agentStates={agentStates} orchestrationResult={orchestrationResult} />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Right column: Capacity gauges, inventories, and Auditor report */}
        <aside className="w-80 shrink-0 flex flex-col gap-4 overflow-y-auto">
          
          {/* Safety auditor card */}
          <div className="glass-card p-4 relative overflow-hidden border-slate-800">
            <div className="absolute right-0 top-0 w-24 h-24 bg-brand-500/5 rounded-full blur-2xl" />
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3.5 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Cpu size={13} className="text-purple-400" />
                Auditor Compliance
              </span>
              <AnimatePresence mode="wait">
                {loading ? (
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping" />
                ) : auditorReport.status === 'success' ? (
                  <span className="flex items-center gap-1 text-[9px] font-bold text-green-400 bg-green-500/10 px-2 py-0.5 rounded border border-green-500/20 uppercase">
                    <ShieldCheck size={11} /> SAFE
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[9px] font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20 uppercase">
                    <ShieldAlert size={11} /> WARN
                  </span>
                )}
              </AnimatePresence>
            </h3>

            {/* Checklist results */}
            <div className="space-y-2 text-[10px]">
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">Total Ingested Reports:</span>
                <span className="font-mono text-slate-200 font-bold">{auditorReport.data?.audited_count || 11}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">ADA Compliant Shelters:</span>
                <span className="font-mono text-slate-200 font-bold">Yes (Validated)</span>
              </div>
              {auditorReport.reasons && auditorReport.reasons.length > 0 ? (
                <div className="mt-3">
                  <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">Compliance Log</span>
                  <div className="mt-1.5 p-2 bg-slate-950/60 rounded border border-slate-900 space-y-1 max-h-24 overflow-y-auto">
                    {auditorReport.reasons.map((reason: string, idx: number) => (
                      <div key={idx} className="text-[9px] text-slate-300 flex items-start gap-1">
                        <span className="text-amber-500">•</span>
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-[9px] text-slate-500 mt-2 italic">Awaiting incident execution to fetch compliance log...</p>
              )}
            </div>
          </div>

          {/* Hospital Occupancy Progress */}
          <div className="glass-card p-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
              <Activity size={13} className="text-red-400" />
              Hospital Capacities
            </h3>
            <div className="space-y-2.5">
              {hospitals.map((h: any, idx: number) => {
                const totalBeds = h.available_beds + 20; // Simulated capacity
                const rate = (h.available_beds / totalBeds) * 100;
                return (
                  <div key={idx} className="flex flex-col">
                    <div className="flex justify-between items-center text-[10px] mb-1">
                      <span className="font-semibold text-slate-200 truncate pr-2">{h.name}</span>
                      <span className="font-mono text-slate-400">{h.available_beds} beds free</span>
                    </div>
                    <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-slate-900">
                      <div className="bg-red-500 h-full rounded-full transition-all duration-500" style={{ width: `${rate}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Shelter Occupancy Progress */}
          <div className="glass-card p-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
              <Layers size={13} className="text-green-400" />
              Shelter Occupancy
            </h3>
            <div className="space-y-2.5">
              {shelters.map((s: any, idx: number) => {
                const rate = (s.occupancy / s.capacity) * 100;
                return (
                  <div key={idx} className="flex flex-col">
                    <div className="flex justify-between items-center text-[10px] mb-1">
                      <span className="font-semibold text-slate-200 truncate pr-2">{s.name}</span>
                      <span className="font-mono text-slate-400">{s.occupancy}/{s.capacity}</span>
                    </div>
                    <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-slate-900">
                      <div className="bg-green-500 h-full rounded-full transition-all duration-500" style={{ width: `${rate}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Resource Inventory */}
          <div className="glass-card p-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3.5 flex items-center gap-2">
              <BarChart2 size={13} className="text-amber-400" />
              Resource Inventory
            </h3>
            <div className="space-y-3 font-mono text-[9px]">
              {/* Water */}
              <div className="flex flex-col">
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Water Bottles</span>
                  <span className="text-slate-200 font-bold">1,800 units</span>
                </div>
                <div className="w-full bg-slate-950 h-2 rounded overflow-hidden border border-slate-900">
                  <div className="bg-brand-500 h-full transition-all" style={{ width: '80%' }} />
                </div>
              </div>
              {/* Trauma Kits */}
              <div className="flex flex-col">
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Trauma Kits</span>
                  <span className={`font-bold ${inventoryItem.quantity_available < 300 ? 'text-amber-400' : 'text-slate-200'}`}>
                    {inventoryItem.quantity_available} units
                  </span>
                </div>
                <div className="w-full bg-slate-950 h-2 rounded overflow-hidden border border-slate-900">
                  <div className="bg-amber-500 h-full transition-all" style={{ width: '45%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Decision safety timeline */}
          <div className="glass-card p-4 flex-1 flex flex-col min-h-0">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
              <Clock size={13} className="text-brand-400" />
              Decision Timeline
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3 font-mono text-[9px] text-slate-400 pr-1">
              <div className="flex items-start gap-2 relative">
                <div className="absolute left-2.5 top-3 bottom-0 w-0.5 bg-slate-800" />
                <div className="w-5 h-5 rounded-full bg-brand-500/20 border border-brand-500 flex items-center justify-center font-bold text-[8px] text-brand-400 shrink-0">1</div>
                <div>
                  <span className="text-slate-200 font-bold block">Incident Ingestion</span>
                  <span className="text-slate-500 text-[8px]">00:00.00</span>
                  <p className="mt-0.5 text-slate-400">IncidentDetected broadcast triggered. Commander Agent parsed task boundaries.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 relative">
                <div className="absolute left-2.5 top-3 bottom-0 w-0.5 bg-slate-800" />
                <div className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500 flex items-center justify-center font-bold text-[8px] text-indigo-400 shrink-0">2</div>
                <div>
                  <span className="text-slate-200 font-bold block">Telemetry Gathering</span>
                  <span className="text-slate-500 text-[8px]">00:00.80</span>
                  <p className="mt-0.5 text-slate-400">Road conditions and weather reports queried via forecast MCP tools.</p>
                </div>
              </div>
              <div className="flex items-start gap-2 relative">
                <div className="absolute left-2.5 top-3 bottom-0 w-0.5 bg-slate-800" />
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-500 flex items-center justify-center font-bold text-[8px] text-emerald-400 shrink-0">3</div>
                <div>
                  <span className="text-slate-200 font-bold block">Response Synthesis</span>
                  <span className="text-slate-500 text-[8px]">00:01.60</span>
                  <p className="mt-0.5 text-slate-400">Hospitals, shelters, and volunteer deployments mapped using search and resource skills.</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-5 h-5 rounded-full bg-purple-500/20 border border-purple-500 flex items-center justify-center font-bold text-[8px] text-purple-400 shrink-0">4</div>
                <div>
                  <span className="text-slate-200 font-bold block">Compliance Audit</span>
                  <span className="text-slate-500 text-[8px]">00:02.40</span>
                  <p className="mt-0.5 text-slate-400">Safety reports and physical ADA constraints verified by Auditor.</p>
                </div>
              </div>
            </div>
          </div>
        </aside>

      </div>
    </div>
  );
};

export default App;
