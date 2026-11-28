import ProjectMap from "./components/ProjectMap";
import { useMemo, useState } from "react";
import { AlertTriangle, Building2, Link2, MapPin, Search, ShieldCheck } from "lucide-react";
import { mockProjects } from "./data/mockProjects";

function getScoreBadgeClass(score) {
  if (score >= 70) return "bg-red-100 text-red-700 border-red-300";
  if (score >= 40) return "bg-amber-100 text-amber-800 border-amber-300";
  return "bg-emerald-100 text-emerald-700 border-emerald-300";
}

export default function App() {
  const [searchText, setSearchText] = useState("");
  const [selectedConstituency, setSelectedConstituency] = useState("ALL");
  const [selectedProjectId, setSelectedProjectId] = useState(mockProjects[0]?.id || null);

  const constituencies = useMemo(() => {
    const unique = new Set(mockProjects.map((p) => p.constituency));
    return ["ALL", ...Array.from(unique)];
  }, []);

  const filteredProjects = useMemo(() => {
    return mockProjects.filter((project) => {
      const matchesConstituency =
        selectedConstituency === "ALL" || project.constituency === selectedConstituency;
      const q = searchText.trim().toLowerCase();
      const matchesQuery =
        !q ||
        project.id.toLowerCase().includes(q) ||
        project.name.toLowerCase().includes(q) ||
        project.vendor_name.toLowerCase().includes(q) ||
        project.vendor_id.toLowerCase().includes(q);
      return matchesConstituency && matchesQuery;
    });
  }, [searchText, selectedConstituency]);

  const activeProject =
    filteredProjects.find((p) => p.id === selectedProjectId) ||
    filteredProjects[0] ||
    mockProjects[0];

  const highRiskCount = mockProjects.filter(
    (p) => p.graph_collusion_score >= 70 || p.composite_cri >= 70
  ).length;

  const avgCri = (
    mockProjects.reduce((sum, p) => sum + Number(p.composite_cri || 0), 0) /
    (mockProjects.length || 1)
  ).toFixed(2);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {/* Top Bar */}
      <header className="bg-slate-900 text-white px-6 py-4 shadow">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-bold tracking-tight">E-NETRA MPLAD Monitoring Dashboard</h1>
            <p className="text-xs text-slate-300">
              Frontend & GIS View — Financial ML, Vendor Collusion Graph & Spatial Verification
            </p>
          </div>
          <span className="text-xs bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-slate-200">
            Prototype Mode (Sample Data)
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
  <ProjectMap
    projects={filteredProjects}
    activeProject={activeProject}
    onSelectProject={(id) => setSelectedProjectId(id)}
  />

  {/* Top Summary Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-sm">
              <span>Monitored Projects</span>
              <Building2 className="w-4 h-4 text-blue-600" />
            </div>
            <p className="text-3xl font-bold mt-2">{mockProjects.length}</p>
            <p className="text-xs text-slate-500 mt-1">Active sample records loaded</p>
          </div>

          <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-sm">
              <span>High Risk Flags</span>
              <AlertTriangle className="w-4 h-4 text-red-600" />
            </div>
            <p className="text-3xl font-bold text-red-600 mt-2">{highRiskCount}</p>
            <p className="text-xs text-slate-500 mt-1">Score threshold ≥ 70</p>
          </div>

          <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-sm">
              <span>Average Composite CRI</span>
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
            </div>
            <p className="text-3xl font-bold mt-2">{avgCri}</p>
            <p className="text-xs text-slate-500 mt-1">Combined risk index across projects</p>
          </div>
        </section>

        {/* Search & Filter Bar */}
        <section className="bg-white rounded-xl p-4 shadow-sm border border-slate-200 flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search by Project ID, project name, or vendor..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={selectedConstituency}
            onChange={(e) => setSelectedConstituency(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {constituencies.map((c) => (
              <option key={c} value={c}>
                {c === "ALL" ? "All Constituencies" : c}
              </option>
            ))}
          </select>
        </section>

        {/* Main Two-Column Workspace */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Projects Table */}
          <div className="lg:col-span-7 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="font-semibold text-base">Projects & Risk Overview</h2>
              <p className="text-xs text-slate-500">Click any row to inspect collusion links and scores</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Project</th>
                    <th className="py-3 px-4">Vendor</th>
                    <th className="py-3 px-4">Collusion</th>
                    <th className="py-3 px-4">CRI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredProjects.map((project) => {
                    const isSelected = activeProject?.id === project.id;
                    return (
                      <tr
                        key={project.id}
                        onClick={() => setSelectedProjectId(project.id)}
                        className={`cursor-pointer transition ${
                          isSelected ? "bg-blue-50/70" : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-900">{project.id}</div>
                          <div className="text-xs text-slate-500">{project.name}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium">{project.vendor_name}</div>
                          <div className="text-xs text-slate-500">{project.vendor_id}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-block px-2.5 py-1 text-xs font-semibold rounded-full border ${getScoreBadgeClass(
                              project.graph_collusion_score
                            )}`}
                          >
                            {project.graph_collusion_score} / 100
                          </span>
                        </td>
                        <td className="py-3 px-4 font-semibold">{project.composite_cri}</td>
                      </tr>
                    );
                  })}
                  {filteredProjects.length === 0 && (
                    <tr>
                      <td colSpan="4" className="py-8 text-center text-slate-500">
                        No matching projects found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Project & Vendor Collusion Detail Panel */}
          {activeProject && (
            <div className="lg:col-span-5 bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-5">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                    {activeProject.id} • {activeProject.constituency}
                  </span>
                  <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium">
                    {activeProject.status}
                  </span>
                </div>
                <h2 className="text-lg font-bold mt-1">{activeProject.name}</h2>
                <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                  <MapPin className="w-3.5 h-3.5" />
                  {activeProject.address} ({activeProject.lat}, {activeProject.lon})
                </p>
              </div>

              {/* 4 Module Scores */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs text-slate-500">ML Anomaly</p>
                  <p className="text-lg font-bold mt-0.5">{activeProject.ml_anomaly_score}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs text-slate-500">Graph Collusion</p>
                  <p className="text-lg font-bold mt-0.5">{activeProject.graph_collusion_score}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs text-slate-500">Spatial EXIF</p>
                  <p className="text-lg font-bold mt-0.5">{activeProject.spatial_exif_score}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs text-slate-500">Composite CRI</p>
                  <p className="text-lg font-bold mt-0.5">{activeProject.composite_cri}</p>
                </div>
              </div>

              {/* Interactive Collusion Network Graph (Embedded from Streamlit) */}
              <div className="border-t border-slate-200 pt-4 space-y-2">
                <h3 className="text-sm font-semibold flex items-center gap-1.5">
                  <Link2 className="w-4 h-4 text-purple-600" />
                  Interactive Collusion Network Graph
                </h3>
                <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-50">
                  <iframe
                    key={activeProject.id}
                    src={`http://localhost:8501/?project_id=${encodeURIComponent(activeProject.id)}&embed=true`}
                    title={`Collusion Graph for ${activeProject.id}`}
                    className="w-full h-[460px] border-0"
                  />
                </div>
              </div>

              {/* Graph Collusion Links */}
              <div className="border-t border-slate-200 pt-4 space-y-2.5">
                <h3 className="text-sm font-semibold flex items-center gap-1.5">
                  <Link2 className="w-4 h-4 text-purple-600" />
                  Vendor Collusion Network Links
                </h3>
                <div className="text-xs space-y-1.5 bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <p>
                    <span className="font-semibold">Vendor:</span> {activeProject.vendor_name} (
                    {activeProject.vendor_id})
                  </p>
                  <p>
                    <span className="font-semibold">Bank Account Hash:</span> {activeProject.bank_hash}
                  </p>
                  <p>
                    <span className="font-semibold">Associated Entity / MP:</span>{" "}
                    {activeProject.linked_mp}
                  </p>
                  <div>
                    <span className="font-semibold">Connected Project IDs:</span>
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {activeProject.linked_projects.map((pid) => (
                        <span
                          key={pid}
                          className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-medium"
                        >
                          {pid}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Findings */}
              <div className="border-t border-slate-200 pt-4 space-y-2">
                <h3 className="text-sm font-semibold">Flagged Findings</h3>
                <ul className="list-disc list-inside text-xs text-slate-700 space-y-1">
                  {activeProject.collusion_notes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                  {activeProject.ml_notes.map((note, idx) => (
                    <li key={`ml-${idx}`}>{note}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}