import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";

function RecenterMap({ lat, lon }) {
  const map = useMap();
  useEffect(() => {
    if (lat && lon) {
      map.setView([lat, lon], 7, { animate: true });
    }
  }, [lat, lon, map]);
  return null;
}

function getMarkerColor(score) {
  if (score >= 70) return "#dc2626";
  if (score >= 40) return "#d97706";
  return "#16a34a";
}

export default function ProjectMap({ projects, activeProject, onSelectProject }) {
  const centerLat = activeProject?.lat || 23.2332;
  const centerLon = activeProject?.lon || 77.4343;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-base">GIS Project Risk Map</h2>
          <p className="text-xs text-slate-500">
            Red = High Collusion Risk (70+), Amber = Medium (40-69), Green = Lower (&lt;40)
          </p>
        </div>
      </div>

      <div className="h-80 w-full">
        <MapContainer
          center={[centerLat, centerLon]}
          zoom={6}
          className="h-full w-full z-0"
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <RecenterMap lat={centerLat} lon={centerLon} />

          {projects.map((project) => {
            const color = getMarkerColor(project.graph_collusion_score);
            return (
              <CircleMarker
                key={project.id}
                center={[project.lat, project.lon]}
                radius={11}
                pathOptions={{
                  color,
                  fillColor: color,
                  fillOpacity: 0.75,
                }}
                eventHandlers={{
                  click: () => onSelectProject(project.id),
                }}
              >
                <Popup>
                  <div className="text-xs space-y-1">
                    <p className="font-bold">
                      {project.id} — {project.name}
                    </p>
                    <p>Vendor: {project.vendor_name}</p>
                    <p>Collusion Score: {project.graph_collusion_score} / 100</p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}