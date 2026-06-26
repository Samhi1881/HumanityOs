import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl, Circle, CircleMarker, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Route } from 'lucide-react';

// Fix Leaflet marker icons issues
const DefaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});
L.Marker.prototype.options.icon = DefaultIcon;

// Helper component to handle dynamic panning/zooming when incident location changes
const ChangeView: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
};

interface HospitalItem {
  name: string;
  available_beds: number;
  specialties?: string[];
  distance_miles?: number;
}

interface ShelterItem {
  name: string;
  capacity: number;
  occupancy: number;
}

interface MapViewerProps {
  centerCoords?: [number, number];
  hospitals?: HospitalItem[];
  shelters?: ShelterItem[];
  volunteersCount?: number;
  incidentName?: string;
  simulatedMarkers?: Array<{ type: string; position: [number, number]; label: string }>;
  simulatedHeatmap?: { center: [number, number]; radius: number; color: string };
}

export const MapViewer: React.FC<MapViewerProps> = ({
  centerCoords = [37.7749, -122.4194], // SF default
  hospitals = [],
  shelters = [],
  volunteersCount = 0,
  incidentName = "Unscheduled Telemetry",
  simulatedMarkers = [],
  simulatedHeatmap
}) => {
  const [showRoutes, setShowRoutes] = useState(true);

  // Generate mock coordinates around the center coordinates for visual placement
  const generateOffsetCoords = (idx: number, multiplier = 1): [number, number] => {
    const offsets = [
      [0.012, -0.015],
      [-0.015, 0.018],
      [0.009, 0.022],
      [-0.008, -0.024],
      [0.022, 0.008]
    ];
    const offset = offsets[idx % offsets.length];
    return [centerCoords[0] + offset[0] * multiplier, centerCoords[1] + offset[1] * multiplier];
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="p-4 bg-slate-900 border-b border-slate-800 flex justify-between items-center">
        <div>
          <h2 className="text-sm font-bold tracking-wider text-slate-100 uppercase">Geospatial Operations Center</h2>
          <p className="text-[10px] text-slate-400 font-mono mt-0.5">Active Incident: {incidentName}</p>
        </div>
        <div className="flex gap-2.5 items-center">
          {/* AI Evacuation Routes Toggle */}
          <button
            onClick={() => setShowRoutes(!showRoutes)}
            className={`flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-1.5 rounded border transition-colors ${
              showRoutes 
                ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20' 
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-750'
            }`}
          >
            <Route size={12} />
            <span>{showRoutes ? 'Evacuation Routes: ON' : 'Evacuation Routes: OFF'}</span>
          </button>
          
          <span className="flex items-center text-[10px] text-red-400 font-mono bg-red-950/20 px-2 py-1.5 rounded border border-red-900/50">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-1.5 animate-ping" />
            Heatmap Active
          </span>
        </div>
      </div>
      
      <div className="flex-1 h-full min-h-[400px] relative z-0">
        <MapContainer
          center={centerCoords}
          zoom={13}
          scrollWheelZoom={true}
          zoomControl={false}
          className="h-full w-full"
        >
          <ChangeView center={centerCoords} zoom={13} />
          
          {/* CartoDB Dark Premium Tiles */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          <ZoomControl position="bottomright" />

          {/* 1. Risk Heatmap Overlay */}
          <Circle
            center={centerCoords}
            radius={2000}
            pathOptions={{
              fillColor: '#ef4444',
              fillOpacity: 0.15,
              color: '#dc2626',
              weight: 1.5,
              dashArray: "4, 6"
            }}
          />
          <Circle
            center={centerCoords}
            radius={800}
            pathOptions={{
              fillColor: '#ef4444',
              fillOpacity: 0.25,
              color: '#b91c1c',
              weight: 2
            }}
          />

          {simulatedHeatmap && (
            <Circle
              center={simulatedHeatmap.center as [number, number]}
              radius={simulatedHeatmap.radius}
              pathOptions={{
                fillColor: simulatedHeatmap.color,
                fillOpacity: 0.15,
                color: simulatedHeatmap.color,
                weight: 1.5,
                dashArray: "4, 6"
              }}
            />
          )}

          {/* Central disaster epicenter marker */}
          <Marker position={centerCoords}>
            <Popup>
              <div className="text-slate-900 font-sans p-1">
                <h3 className="font-bold text-xs text-red-600">Disaster Epicenter</h3>
                <p className="text-[10px] text-slate-500 mt-1">{incidentName}</p>
              </div>
            </Popup>
          </Marker>

          {/* Safe Shelter coordinates mapping for paths */}
          {showRoutes && shelters.map((_shelter, idx) => {
            const shelterPos = generateOffsetCoords(idx, 0.8);
            
            // Build a detour path routing around a potential hazard location
            // Epicenter -> Detour -> Shelter
            const detourPos: [number, number] = [
              (centerCoords[0] + shelterPos[0]) / 2 + 0.003,
              (centerCoords[1] + shelterPos[1]) / 2 - 0.004
            ];

            return (
              <Polyline
                key={`route-shelter-${idx}`}
                positions={[centerCoords, detourPos, shelterPos]}
                pathOptions={{
                  color: '#10b981',
                  weight: 3,
                  opacity: 0.75,
                  dashArray: '5, 8'
                }}
              />
            );
          })}

          {/* Medical routes mapping for paths */}
          {showRoutes && hospitals.map((_hospital, idx) => {
            const hospitalPos = generateOffsetCoords(idx + 2, 1.1);
            
            // Epicenter -> Hospital
            return (
              <Polyline
                key={`route-hospital-${idx}`}
                positions={[centerCoords, hospitalPos]}
                pathOptions={{
                  color: '#ef4444',
                  weight: 3,
                  opacity: 0.65,
                  dashArray: '4, 8'
                }}
              />
            );
          })}

          {/* Volunteer routes mapping for paths */}
          {showRoutes && Array.from({ length: Math.min(volunteersCount, 5) }).map((_, idx) => {
            const volPos = generateOffsetCoords(idx + 4, 1.4);
            
            // Epicenter -> Volunteer Squad
            return (
              <Polyline
                key={`route-volunteer-${idx}`}
                positions={[centerCoords, volPos]}
                pathOptions={{
                  color: '#3b82f6',
                  weight: 2.5,
                  opacity: 0.6,
                  dashArray: '2, 6'
                }}
              />
            );
          })}

          {/* 2. Safe Shelter Markers (Green) */}
          {shelters.map((shelter, idx) => {
            const pos = generateOffsetCoords(idx, 0.8);
            const rate = shelter.capacity > 0 ? (shelter.occupancy / shelter.capacity) * 100 : 0;
            return (
              <CircleMarker
                key={`shelter-${idx}`}
                center={pos}
                radius={9}
                pathOptions={{
                  fillColor: '#10b981',
                  fillOpacity: 0.8,
                  color: '#059669',
                  weight: 2
                }}
              >
                <Popup>
                  <div className="text-slate-900 font-sans p-1 min-w-[150px]">
                    <span className="text-[9px] uppercase tracking-wider font-bold text-green-600 block">Emergency Shelter</span>
                    <h3 className="font-semibold text-xs mt-0.5">{shelter.name}</h3>
                    <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div className="bg-green-500 h-full" style={{ width: `${rate}%` }} />
                    </div>
                    <span className="text-[10px] text-slate-600 mt-1 block">
                      Occupancy: {shelter.occupancy}/{shelter.capacity} ({rate.toFixed(0)}%)
                    </span>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

          {/* 3. Hospitals Medical Markers (Red Cross style) */}
          {hospitals.map((hospital, idx) => {
            const pos = generateOffsetCoords(idx + 2, 1.1);
            return (
              <CircleMarker
                key={`hospital-${idx}`}
                center={pos}
                radius={9}
                pathOptions={{
                  fillColor: '#ef4444',
                  fillOpacity: 0.8,
                  color: '#b91c1c',
                  weight: 2
                }}
              >
                <Popup>
                  <div className="text-slate-900 font-sans p-1 min-w-[150px]">
                    <span className="text-[9px] uppercase tracking-wider font-bold text-red-600 block">Medical Center</span>
                    <h3 className="font-semibold text-xs mt-0.5">{hospital.name}</h3>
                    <span className="text-[10px] text-slate-600 mt-1 block">
                      ICU Beds Available: <strong className="text-red-600">{hospital.available_beds}</strong>
                    </span>
                    {hospital.specialties && (
                      <span className="text-[9px] text-slate-400 block mt-0.5">
                        Specialties: {hospital.specialties.join(", ")}
                      </span>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

          {/* 4. Volunteer locations (Blue) */}
          {Array.from({ length: Math.min(volunteersCount, 5) }).map((_, idx) => {
            const pos = generateOffsetCoords(idx + 4, 1.4);
            return (
              <CircleMarker
                key={`volunteer-${idx}`}
                center={pos}
                radius={7}
                pathOptions={{
                  fillColor: '#3b82f6',
                  fillOpacity: 0.9,
                  color: '#1d4ed8',
                  weight: 1.5
                }}
              >
                <Popup>
                  <div className="text-slate-900 font-sans p-1">
                    <span className="text-[9px] uppercase tracking-wider font-bold text-blue-600 block">Volunteer Group</span>
                    <h3 className="font-semibold text-xs mt-0.5">Response Squad V-{100 + idx}</h3>
                    <p className="text-[10px] text-slate-500 mt-1">Status: Deploying to support supply corridors.</p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

          {/* 5. Simulated Markers */}
          {simulatedMarkers.map((marker, idx) => {
            const isHazard = marker.type === 'hazard';
            const isSearch = marker.type === 'search';
            const color = isHazard ? '#ef4444' : (isSearch ? '#f59e0b' : '#3b82f6');
            const strokeColor = isHazard ? '#b91c1c' : (isSearch ? '#d97706' : '#1d4ed8');
            return (
              <CircleMarker
                key={`sim-marker-${idx}`}
                center={marker.position}
                radius={isHazard ? 11 : 8}
                pathOptions={{
                  fillColor: color,
                  fillOpacity: 0.8,
                  color: strokeColor,
                  weight: 2
                }}
              >
                <Popup>
                  <div className="text-slate-900 font-sans p-1">
                    <span className="text-[9px] uppercase tracking-wider font-bold block" style={{ color: strokeColor }}>
                      {isHazard ? 'Hazard Block' : (isSearch ? 'Search Grid' : 'Volunteer Squad')}
                    </span>
                    <h3 className="font-semibold text-xs mt-0.5">{marker.label}</h3>
                    <p className="text-[10px] text-slate-500 mt-1">
                      {isHazard ? 'Area blocked. Avoid route corridor.' : (isSearch ? 'SAR teams scanning sector coordinates.' : 'Deployed to critical operations point.')}
                    </p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

        </MapContainer>
      </div>
    </div>
  );
};
export default MapViewer;
