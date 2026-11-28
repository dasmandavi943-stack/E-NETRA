export const mockProjects = [
  {
    id: "MPLAD_022",
    name: "Community Hall & Road Link",
    constituency: "Agra",
    vendor_id: "VEND_116",
    vendor_name: "Shan Enterprises",
    bank_hash: "BANK_HASH_1016",
    address: "55/986, Varma Zila, Agra",
    linked_mp: "Smt. Sandhya Ray",
    linked_projects: ["MPLAD_022", "MPLAD_445", "MPLAD_030", "MPLAD_274", "MPLAD_265", "MPLAD_197", "MPLAD_264"],
    ml_anomaly_score: 45.47,
    graph_collusion_score: 78,
    spatial_exif_score: 12,
    composite_cri: 45.16,
    lat: 27.1767,
    lon: 78.0081,
    status: "Under Review",
    ml_notes: [
      "Expenditure pattern shows repeated near-threshold billing.",
      "Multiple project IDs linked to the same vendor profile."
    ],
    collusion_notes: [
      "Shared bank hash (BANK_HASH_1016) across linked records.",
      "Common address reference tied to Shan Enterprises (VEND_116)."
    ]
  },
  {
    id: "MPLAD_101",
    name: "Public Drainage & Culvert Work",
    constituency: "Bhopal",
    vendor_id: "VEND_101",
    vendor_name: "Apex Infra Works",
    bank_hash: "BANK_HASH_01",
    address: "12 MP Nagar Bhopal",
    linked_mp: "District Nodal Office",
    linked_projects: ["MPLAD_101"],
    ml_anomaly_score: 22.10,
    graph_collusion_score: 15,
    spatial_exif_score: 5,
    composite_cri: 14.07,
    lat: 23.2332,
    lon: 77.4343,
    status: "In Progress",
    ml_notes: [
      "Sanction and release amounts align with standard milestones."
    ],
    collusion_notes: [
      "No overlapping bid ring detected in current sample."
    ]
  }
];