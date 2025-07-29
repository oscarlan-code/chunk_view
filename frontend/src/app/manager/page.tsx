"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import ProgressBar from "../../components/ui/progress";

const SIDEBAR_LINKS = [
  { label: "Machines", key: "machines" },
  { label: "Operators", key: "operators" },
  { label: "Technicians", key: "technicians" },
  { label: "Documents", key: "documents" },
  { label: "Reports", key: "reports" },
  { label: "Query", key: "query" },
];

const STATUS_COLORS: Record<string, string> = {
  working: "#34c759",
  fixing: "#ff9500",
  "needs fix": "#ffd60a",
};

const STATUS_OPTIONS = ["working", "fixing", "needs fix"];

interface Document {
  id: number;
  filename: string;
  status: string;
  upload_time: string;
  type: string;
  tag: string;
  uploader_username: string;
}

interface QueryResponse {
  response: string;
  source: string;
  machine_id: number;
  documents_available: number;
  confidence_score: number | null;
  source_documents: string[] | null;
  processing_time: number | null;
}

interface WebSocketMessage {
  type: string;
  knowledge_id?: number;
  progress?: number;
  status?: string;
  message?: string;
}

export default function ManagerDashboard() {
  const router = useRouter();
  const [machines, setMachines] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: "",
    production_line: "",
    factory: "",
    status: "working",
    last_maintenance: ""
  });
  const [showDeleteId, setShowDeleteId] = useState<number | null>(null);
  const [uploadForMachine, setUploadForMachine] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [machineDocs, setMachineDocs] = useState<Record<number, Document[]>>({});
  const [documentProgress, setDocumentProgress] = useState<Record<number, { progress: number; status: string }>>({});
  const [userId, setUserId] = useState<number | null>(null);
  const [viewDocsForMachine, setViewDocsForMachine] = useState<number | null>(null);
  const [tag, setTag] = useState<string>("");
  const [customTag, setCustomTag] = useState<string>("");
  
  // Query functionality
  const [showQueryModal, setShowQueryModal] = useState(false);
  const [selectedMachine, setSelectedMachine] = useState<any>(null);
  const [query, setQuery] = useState("");
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  
  // Processing status tracking
  const [processingDocs, setProcessingDocs] = useState<Set<number>>(new Set());
  
  // Upload progress tracking
  const [uploadProgress, setUploadProgress] = useState<{
    progress: number;
    status: string;
    isUploading: boolean;
    isProcessing: boolean;
  }>({
    progress: 0,
    status: "",
    isUploading: false,
    isProcessing: false
  });

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null);
  const clientId = useRef<string>(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const getFileType = (file: File): string => {
    const fileName = file.name.toLowerCase();
    const fileExtension = fileName.split('.').pop() || '';
    
    switch (fileExtension) {
      case 'pdf':
        return 'pdf';
      case 'txt':
        return 'txt';
      case 'doc':
        return 'doc';
      case 'docx':
        return 'docx';
      default:
        return 'pdf'; // fallback
    }
  };

  useEffect(() => {
    const user = localStorage.getItem("user");
    if (!user) {
      router.push("/manager/signin");
      return;
    }
    const parsed = JSON.parse(user);
    if (parsed.role !== "manager") {
      router.push("/manager/signin");
    }
  }, [router]);

  const fetchMachines = async () => {
    try {
      const res = await fetch("http://localhost:8000/machines");
      if (res.ok) {
        const data = await res.json();
        setMachines(data);
        
        // Fetch documents for each machine
        for (const machine of data) {
          await fetchMachineDocuments(machine.id);
        }
      } else {
        console.error("Failed to fetch machines");
      }
    } catch (error) {
      console.error("Error fetching machines:", error);
    }
  };

  const fetchMachineDocuments = async (machineId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/knowledge/by_machine/${machineId}`);
      if (res.ok) {
        const documents = await res.json();
        setMachineDocs(prev => ({
          ...prev,
          [machineId]: documents
        }));
      }
    } catch (error) {
      console.error(`Error fetching documents for machine ${machineId}:`, error);
    }
  };

  const fetchUserId = () => {
    const user = localStorage.getItem("user");
    if (user) {
      const parsed = JSON.parse(user);
      setUserId(parsed.id);
    }
  };

  useEffect(() => {
    fetchMachines();
    fetchUserId();
    
    // Connect to WebSocket for real-time progress updates
    connectWebSocket();
    
    // Poll for updates every 3 seconds
    const interval = setInterval(() => {
      fetchMachines();
    }, 3000);
    
    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${clientId.current}`);
    
    ws.onopen = () => {
      console.log("WebSocket connected");
    };
    
    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        
        if (data.type === "progress" && data.knowledge_id) {
          // Update progress for specific knowledge item
          setUploadProgress({
            progress: data.progress || 0,
            status: data.message || data.status || "",
            isUploading: false,
            isProcessing: data.status !== "ready" && data.status !== "failed"
          });
          
          // Track progress for specific document
          setDocumentProgress(prev => ({
            ...prev,
            [data.knowledge_id!]: {
              progress: data.progress || 0,
              status: data.message || data.status || ""
            }
          }));
          
          // If processing is complete, refresh the machines data and documents
          if (data.status === "ready" || data.status === "failed") {
            fetchMachines(); // This will refresh all documents
            setUploadProgress({
              progress: 0,
              status: "",
              isUploading: false,
              isProcessing: false
            });
            // Clear the document progress when complete
            setDocumentProgress(prev => {
              const newProgress = { ...prev };
              delete newProgress[data.knowledge_id!];
              return newProgress;
            });
          }
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };
    
    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
    
    ws.onclose = () => {
      console.log("WebSocket disconnected");
    };
    
    wsRef.current = ws;
  };

  const handleAddOrEditMachine = async (e: any) => {
    e.preventDefault();
    const payload = {
      ...form,
      last_maintenance: form.last_maintenance ? new Date(form.last_maintenance).toISOString() : null
    };
    if (editId) {
      const res = await fetch(`http://localhost:8000/machines/${editId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const updated = await res.json();
        setMachines(prev => prev.map(m => m.id === editId ? updated : m));
        setEditId(null);
        setShowModal(false);
        setForm({ name: "", production_line: "", factory: "", status: "working", last_maintenance: "" });
      }
    } else {
      const res = await fetch("http://localhost:8000/machines", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const newMachine = await res.json();
        setMachines(prev => [...prev, newMachine]);
        setShowModal(false);
        setForm({ name: "", production_line: "", factory: "", status: "working", last_maintenance: "" });
      }
    }
  };

  const handleEdit = (machine: any) => {
    setEditId(machine.id);
    setForm({
      name: machine.name,
      production_line: machine.production_line,
      factory: machine.factory,
      status: machine.status,
      last_maintenance: machine.last_maintenance ? new Date(machine.last_maintenance).toISOString().split('T')[0] : ""
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    const res = await fetch(`http://localhost:8000/machines/${id}`, { method: "DELETE" });
    if (res.ok) {
      setMachines(prev => prev.filter(m => m.id !== id));
      setShowDeleteId(null);
    }
  };

  const handleStatusChange = async (id: number, status: string) => {
    const machine = machines.find(m => m.id === id);
    if (!machine) return;
    
    const res = await fetch(`http://localhost:8000/machines/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...machine, status })
    });
    if (res.ok) {
      const updated = await res.json();
      setMachines(prev => prev.map(m => m.id === id ? updated : m));
    }
  };

  const handleUploadDoc = (machineId: number) => {
    setUploadForMachine(machineId);
    setFile(null);
    setTag("");
    setCustomTag("");
  };

  const handleUploadSubmit = async (e: any) => {
    e.preventDefault();
    if (!file || !uploadForMachine || !userId) return;
    
    // Set initial upload progress
    setUploadProgress({
      progress: 0,
      status: "Starting upload...",
      isUploading: true,
      isProcessing: false
    });
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("uploaded_by", userId.toString());
    formData.append("type", getFileType(file));
    formData.append("machine_id", uploadForMachine.toString());
    formData.append("tag", tag === "other" ? customTag : tag);
    formData.append("client_id", clientId.current); // Send client_id for WebSocket updates
    
    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData
      });
      
      if (res.ok) {
        const newDoc = await res.json();
        setMachineDocs(prev => ({
          ...prev,
          [uploadForMachine]: [...(prev[uploadForMachine] || []), newDoc]
        }));
        setUploadForMachine(null);
        setFile(null);
        setTag("");
        setCustomTag("");
        
        // Switch to processing mode
        setUploadProgress({
          progress: 0,
          status: "Processing document...",
          isUploading: false,
          isProcessing: true
        });
      } else {
        const errorData = await res.json().catch(() => ({}));
        console.error("Upload failed:", errorData);
        setUploadProgress({
          progress: 0,
          status: "Upload failed",
          isUploading: false,
          isProcessing: false
        });
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadProgress({
        progress: 0,
        status: "Upload failed",
        isUploading: false,
        isProcessing: false
      });
    }
  };

  const handleDeleteDoc = async (docId: number, machineId: number) => {
    const res = await fetch(`http://localhost:8000/knowledge/${docId}`, { method: "DELETE" });
    if (res.ok) {
      setMachineDocs(prev => ({
        ...prev,
        [machineId]: prev[machineId]?.filter(doc => doc.id !== docId) || []
      }));
    }
  };

  // Query functionality
  const handleQuery = async () => {
    if (!selectedMachine || !query.trim()) return;

    setQueryLoading(true);
    try {
      const response = await fetch('http://localhost:8000/query/machine', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          machine_id: selectedMachine.id,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setQueryResponse(data);
      } else {
        console.error('Failed to get query response');
      }
    } catch (error) {
      console.error('Error querying machine:', error);
    } finally {
      setQueryLoading(false);
    }
  };

  const openQueryModal = (machine: any) => {
    setSelectedMachine(machine);
    setShowQueryModal(true);
    setQuery('');
    setQueryResponse(null);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <span style={{ color: '#28a745', fontWeight: 600, fontSize: '12px' }}>✅ Ready</span>;
      case 'processing':
        return <span style={{ color: '#ffc107', fontWeight: 600, fontSize: '12px' }}>🔄 Processing</span>;
      case 'failed':
        return <span style={{ color: '#dc3545', fontWeight: 600, fontSize: '12px' }}>❌ Failed</span>;
      default:
        return <span style={{ color: '#6c757d', fontWeight: 600, fontSize: '12px' }}>⏳ {status}</span>;
    }
  };

  const getProcessingAnimation = () => (
    <div style={{ 
      display: 'inline-flex', 
      alignItems: 'center', 
      gap: '4px',
      fontSize: '12px',
      color: '#ffc107',
      fontWeight: 600
    }}>
      <div style={{ 
        width: "8px", 
        height: "8px", 
        borderRadius: "50%", 
        border: "1px solid #ffc107", 
        borderTop: "1px solid transparent",
        animation: "spin 1s linear infinite"
      }}></div>
      Processing...
    </div>
  );

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#f5f6fa" }}>
      {/* Sidebar */}
      <aside style={{ width: 240, background: "#fff", borderRight: "1px solid #e5e7eb", padding: 32 }}>
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontWeight: 700, fontSize: 20, marginBottom: 4 }}>Company 1</div>
          <div style={{ color: "#888", fontSize: 14 }}>Maintenance System</div>
        </div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {SIDEBAR_LINKS.map(link => (
            <div key={link.key} style={{
              padding: "12px 16px",
              borderRadius: 8,
              background: link.key === "machines" ? "#f0f4ff" : "transparent",
              color: link.key === "machines" ? "#007aff" : "#222",
              fontWeight: link.key === "machines" ? 600 : 500,
              marginBottom: 4,
              cursor: "pointer"
            }}>{link.label}</div>
          ))}
        </nav>
      </aside>
      {/* Main Content */}
      <main style={{ flex: 1, padding: 40 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
          <div>
            <h1 style={{ fontWeight: 700, fontSize: 32, margin: 0 }}>Dashboard</h1>
            <div style={{ color: "#888", fontSize: 16, marginTop: 8 }}>
              Total Machines: <b>{machines.length}</b>
            </div>
          </div>
          <button onClick={() => { setShowModal(true); setEditId(null); setForm({ name: "", production_line: "", factory: "", status: "working", last_maintenance: "" }); }} style={{ background: "#007aff", color: "#fff", border: "none", borderRadius: 8, padding: "12px 28px", fontSize: 18, fontWeight: 600, cursor: "pointer", boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>+ Add Machine</button>
        </div>
        {/* Machine Cards Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 24 }}>
          {machines.map(machine => (
            <div key={machine.id} style={{ background: "#fff", borderRadius: 14, boxShadow: "0 2px 8px rgba(0,0,0,0.04)", padding: 24, border: `1.5px solid #e5e7eb`, position: 'relative' }}>
              <div style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 20 }}>{machine.name}</span>
                <span style={{ marginLeft: 12, fontSize: 14, fontWeight: 600, color: STATUS_COLORS[machine.status?.toLowerCase()] || '#888', background: '#f5f6fa', borderRadius: 8, padding: '2px 10px' }}>{machine.status?.charAt(0).toUpperCase() + machine.status?.slice(1)}</span>
                {/* Edit/Delete buttons */}
                <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                  <button onClick={() => handleEdit(machine)} style={{ background: 'none', border: 'none', color: '#007aff', fontWeight: 600, cursor: 'pointer', fontSize: 16 }}>Edit</button>
                  <button onClick={() => setShowDeleteId(machine.id)} style={{ background: 'none', border: 'none', color: '#d32f2f', fontWeight: 600, cursor: 'pointer', fontSize: 16 }}>Delete</button>
                </span>
              </div>
              <div style={{ color: '#555', fontSize: 15, marginBottom: 4 }}>
                <span role="img" aria-label="line">🏭</span> Production Line: {machine.production_line}
              </div>
              <div style={{ color: '#555', fontSize: 15, marginBottom: 4 }}>
                <span role="img" aria-label="factory">🏢</span> Factory: {machine.factory}
              </div>
              <div style={{ color: '#555', fontSize: 15, marginBottom: 16 }}>
                <span role="img" aria-label="calendar">📅</span> Last Maintenance: {machine.last_maintenance ? new Date(machine.last_maintenance).toLocaleDateString() : 'N/A'}
              </div>
              {/* Status dropdown */}
              <select value={machine.status} onChange={e => handleStatusChange(machine.id, e.target.value)} style={{ fontSize: 15, padding: 8, borderRadius: 8, border: "1px solid #ddd", marginBottom: 12, width: '100%' }}>
                {STATUS_OPTIONS.map(opt => <option key={opt} value={opt}>{opt.charAt(0).toUpperCase() + opt.slice(1)}</option>)}
              </select>
              
              {/* Document Status Section */}
              {machineDocs[machine.id] && machineDocs[machine.id].length > 0 && (
                <div style={{ marginBottom: 12, padding: '12px', background: '#f8f9fa', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, color: '#333' }}>
                    📄 Documents ({machineDocs[machine.id].length})
                  </div>
                  {machineDocs[machine.id].map((doc, idx) => (
                    <div key={doc.id} style={{ 
                      padding: '8px 0',
                      borderBottom: idx < machineDocs[machine.id].length - 1 ? '1px solid #eee' : 'none'
                    }}>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        marginBottom: doc.status === 'processing' ? '4px' : '0'
                      }}>
                        <div style={{ flex: 1, fontSize: '13px', color: '#666' }}>
                          {doc.filename}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {doc.status === 'processing' ? getProcessingAnimation() : getStatusBadge(doc.status)}
                        </div>
                      </div>
                      
                      {/* Progress bar for processing documents */}
                      {doc.status === 'processing' && (
                        <div style={{ marginTop: '4px' }}>
                          <ProgressBar 
                            progress={documentProgress[doc.id]?.progress || 0}
                            status={documentProgress[doc.id]?.status || "Processing document..."}
                            isUploading={false}
                            isProcessing={true}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: 8 }}>
                <button onClick={() => handleUploadDoc(machine.id)} style={{ 
                  background: "#007aff", 
                  color: "#fff", 
                  border: "none", 
                  borderRadius: 8, 
                  padding: "10px 0", 
                  flex: 1,
                  fontWeight: 600, 
                  fontSize: 16, 
                  cursor: "pointer" 
                }}>
                  Upload Doc
                </button>
                <button onClick={() => openQueryModal(machine)} style={{ 
                  background: "#28a745", 
                  color: "#fff", 
                  border: "none", 
                  borderRadius: 8, 
                  padding: "10px 0", 
                  flex: 1,
                  fontWeight: 600, 
                  fontSize: 16, 
                  cursor: "pointer" 
                }}>
                  Ask Question
                </button>
              </div>
              
              {machineDocs[machine.id] && machineDocs[machine.id].length > 0 && (
                <button onClick={() => setViewDocsForMachine(machine.id)} style={{ 
                  background: "#eee", 
                  color: "#007aff", 
                  border: "none", 
                  borderRadius: 8, 
                  padding: "8px 0", 
                  width: "100%", 
                  fontWeight: 600, 
                  fontSize: 15, 
                  cursor: "pointer" 
                }}>
                  View Documents
                </button>
              )}
              
              {/* Delete confirmation modal */}
              {showDeleteId === machine.id && (
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(255,255,255,0.96)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', borderRadius: 14, zIndex: 10 }}>
                  <div style={{ fontWeight: 600, fontSize: 18, marginBottom: 16 }}>Delete this machine?</div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <button onClick={() => setShowDeleteId(null)} style={{ background: '#eee', color: '#333', border: 'none', borderRadius: 8, padding: '10px 24px', fontWeight: 500, fontSize: 16, cursor: 'pointer' }}>Cancel</button>
                    <button onClick={() => handleDelete(machine.id)} style={{ background: '#d32f2f', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 24px', fontWeight: 600, fontSize: 16, cursor: 'pointer' }}>Delete</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Add/Edit Machine Modal */}
        {showModal && (
          <div style={{ position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh", background: "rgba(0,0,0,0.18)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div style={{ background: "#fff", borderRadius: 14, boxShadow: "0 4px 24px rgba(0,0,0,0.12)", padding: 36, minWidth: 340, maxWidth: 400 }}>
              <h2 style={{ fontWeight: 700, fontSize: 24, marginBottom: 18 }}>{editId ? "Edit Machine" : "Add New Machine"}</h2>
              <form onSubmit={handleAddOrEditMachine} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <input required placeholder="Machine Name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
                <input required placeholder="Production Line" value={form.production_line} onChange={e => setForm(f => ({ ...f, production_line: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
                <input required placeholder="Factory" value={form.factory} onChange={e => setForm(f => ({ ...f, factory: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
                <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }}>
                  <option value="working">Working</option>
                  <option value="fixing">Fixing</option>
                  <option value="needs fix">Needs Fix</option>
                </select>
                <input type="date" placeholder="Last Maintenance" value={form.last_maintenance} onChange={e => setForm(f => ({ ...f, last_maintenance: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
                <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
                  <button type="button" onClick={() => { setShowModal(false); setEditId(null); }} style={{ background: "#eee", color: "#333", border: "none", borderRadius: 8, padding: "10px 24px", fontWeight: 500, fontSize: 16, cursor: "pointer" }}>Cancel</button>
                  <button type="submit" style={{ background: "#007aff", color: "#fff", border: "none", borderRadius: 8, padding: "10px 24px", fontWeight: 600, fontSize: 16, cursor: "pointer" }}>{editId ? "Save Changes" : "Add Machine"}</button>
                </div>
              </form>
            </div>
          </div>
        )}
        
        {/* Upload Doc Modal */}
        {uploadForMachine && (
          <div style={{ position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh", background: "rgba(0,0,0,0.18)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div style={{ background: "#fff", borderRadius: 14, boxShadow: "0 4px 24px rgba(0,0,0,0.12)", padding: 36, minWidth: 340, maxWidth: 400 }}>
              <h2 style={{ fontWeight: 700, fontSize: 24, marginBottom: 18 }}>Upload Doc</h2>
              <form onSubmit={handleUploadSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <input type="file" accept=".pdf,image/*,.txt,.doc,.docx" onChange={e => setFile(e.target.files?.[0] || null)} style={{ fontSize: 16, padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
                <label style={{ fontSize: 16, fontWeight: 500 }}>Tag (Type of Document):</label>
                <select required value={tag} onChange={e => setTag(e.target.value)} style={{ fontSize: 16, padding: 8, borderRadius: 8, border: "1px solid #ddd" }}>
                  <option value="" disabled>Select tag</option>
                  <option value="handbook">Handbook</option>
                  <option value="sop">SOP</option>
                  <option value="bda">BDA</option>
                  <option value="other">Other (type in below)</option>
                </select>
                {tag === "other" && (
                  <input required placeholder="Enter custom tag" value={customTag} onChange={e => setCustomTag(e.target.value)} style={{ fontSize: 16, padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
                )}
                {/* Progress Bar */}
                {uploadProgress.progress > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <ProgressBar 
                      progress={uploadProgress.progress}
                      status={uploadProgress.status}
                      isUploading={uploadProgress.isUploading}
                      isProcessing={uploadProgress.isProcessing}
                    />
                  </div>
                )}
                
                <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
                  <button type="button" onClick={() => { setUploadForMachine(null); setFile(null); setTag(""); setCustomTag(""); setUploadProgress({ progress: 0, status: "", isUploading: false, isProcessing: false }); }} style={{ background: "#eee", color: "#333", border: "none", borderRadius: 8, padding: "10px 24px", fontWeight: 500, fontSize: 16, cursor: "pointer" }}>Cancel</button>
                  <button type="submit" disabled={uploadProgress.progress > 0} style={{ background: uploadProgress.progress > 0 ? "#ccc" : "#007aff", color: "#fff", border: "none", borderRadius: 8, padding: "10px 24px", fontWeight: 600, fontSize: 16, cursor: uploadProgress.progress > 0 ? "not-allowed" : "pointer" }}>Upload</button>
                </div>
              </form>
            </div>
          </div>
        )}
        
        {/* Query Modal */}
        {showQueryModal && selectedMachine && (
          <div style={{ position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh", background: "rgba(0,0,0,0.18)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div style={{ background: "#fff", borderRadius: 14, boxShadow: "0 4px 24px rgba(0,0,0,0.12)", padding: 36, minWidth: 500, maxWidth: 700, maxHeight: "80vh", overflowY: "auto" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
                <h2 style={{ fontWeight: 700, fontSize: 24, color: "#1d1d1f" }}>
                  🔍 Query: {selectedMachine.name}
                </h2>
                <button
                  onClick={() => setShowQueryModal(false)}
                  style={{ background: "none", border: "none", fontSize: 24, color: "#8e8e93", cursor: "pointer", padding: 8, borderRadius: 8 }}
                  onMouseOver={(e) => e.currentTarget.style.color = "#1d1d1f"}
                  onMouseOut={(e) => e.currentTarget.style.color = "#8e8e93"}
                >
                  ✕
                </button>
              </div>

              <div style={{ marginBottom: 24 }}>
                <label style={{ display: "block", fontWeight: 600, fontSize: 16, color: "#1d1d1f", marginBottom: 8 }}>
                  Your Question
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about this machine..."
                  style={{ 
                    width: "100%", 
                    padding: 16, 
                    border: "1px solid #d1d1d6", 
                    borderRadius: 12, 
                    fontSize: 16,
                    fontFamily: "inherit",
                    resize: "vertical",
                    minHeight: 100,
                    outline: "none"
                  }}
                  onFocus={(e) => e.target.style.borderColor = "#007aff"}
                  onBlur={(e) => e.target.style.borderColor = "#d1d1d6"}
                  rows={4}
                />
              </div>

              <button
                onClick={handleQuery}
                disabled={!query.trim() || queryLoading}
                style={{ 
                  width: "100%", 
                  background: !query.trim() || queryLoading ? "#f2f2f7" : "#007aff", 
                  color: !query.trim() || queryLoading ? "#8e8e93" : "#fff", 
                  border: "none", 
                  borderRadius: 12, 
                  padding: "16px 24px", 
                  fontWeight: 600, 
                  fontSize: 16, 
                  cursor: !query.trim() || queryLoading ? "not-allowed" : "pointer",
                  transition: "all 0.2s ease"
                }}
                onMouseOver={(e) => {
                  if (!(!query.trim() || queryLoading)) {
                    e.currentTarget.style.background = "#0056cc";
                  }
                }}
                onMouseOut={(e) => {
                  if (!(!query.trim() || queryLoading)) {
                    e.currentTarget.style.background = "#007aff";
                  }
                }}
              >
                {queryLoading ? (
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <div style={{ width: 16, height: 16, border: "2px solid transparent", borderTop: "2px solid #fff", borderRadius: "50%", animation: "spin 1s linear infinite", marginRight: 8 }}></div>
                    Processing...
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                    🔍 Ask Question
                  </div>
                )}
              </button>

              {queryResponse && (
                <div style={{ marginTop: 24, padding: 20, background: "#f2f2f7", borderRadius: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                    <h3 style={{ fontWeight: 600, fontSize: 18, color: "#1d1d1f" }}>Response</h3>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 14, color: "#8e8e93" }}>
                      <span>Confidence: {queryResponse.confidence_score ? `${(queryResponse.confidence_score * 100).toFixed(1)}%` : 'N/A'}</span>
                      {queryResponse.processing_time && (
                        <span>• {queryResponse.processing_time.toFixed(2)}s</span>
                      )}
                    </div>
                  </div>
                  
                  <div style={{ color: "#1d1d1f", marginBottom: 16, lineHeight: 1.5, fontSize: 16 }}>
                    {queryResponse.response}
                  </div>

                  {queryResponse.source_documents && queryResponse.source_documents.length > 0 && (
                    <div>
                      <h4 style={{ fontWeight: 600, fontSize: 16, color: "#1d1d1f", marginBottom: 12 }}>Source Documents:</h4>
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {queryResponse.source_documents.map((doc, index) => (
                          <div key={index} style={{ fontSize: 14, color: "#48484a", background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #e5e5ea" }}>
                            {doc}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* View Docs Modal */}
        {viewDocsForMachine && machineDocs[viewDocsForMachine] && (
          <div style={{ position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh", background: "rgba(0,0,0,0.18)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div style={{ background: "#fff", borderRadius: 14, boxShadow: "0 4px 24px rgba(0,0,0,0.12)", padding: 36, minWidth: 340, maxWidth: 600 }}>
              <h2 style={{ fontWeight: 700, fontSize: 24, marginBottom: 18 }}>Docs for Machine</h2>
              <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 16 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #eee" }}>
                    <th style={{ textAlign: "left", fontWeight: 600, fontSize: 15, padding: 6 }}>File</th>
                    <th style={{ textAlign: "left", fontWeight: 600, fontSize: 15, padding: 6 }}>Status</th>
                    <th style={{ textAlign: "left", fontWeight: 600, fontSize: 15, padding: 6 }}>Upload Time</th>
                    <th style={{ textAlign: "left", fontWeight: 600, fontSize: 15, padding: 6 }}>Tag</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {machineDocs[viewDocsForMachine].map(doc => (
                    <tr key={doc.id} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={{ padding: 6 }}>
                        <a href={`http://localhost:8000/files/${encodeURIComponent(doc.filename)}`} target="_blank" rel="noopener noreferrer" style={{ color: "#007aff", textDecoration: "underline", fontSize: 16 }}>
                          <span role="img" aria-label="doc">📄</span> {doc.filename}
                        </a>
                      </td>
                      <td style={{ padding: 6 }}>
                        {doc.status === 'processing' ? getProcessingAnimation() : getStatusBadge(doc.status)}
                      </td>
                      <td style={{ padding: 6 }}>{doc.upload_time ? new Date(doc.upload_time).toLocaleString() : "N/A"}</td>
                      <td style={{ padding: 6 }}>{doc.tag || ""}</td>
                      <td style={{ padding: 6 }}>
                        <button onClick={() => handleDeleteDoc(doc.id, viewDocsForMachine)} style={{ background: '#d32f2f', color: '#fff', border: 'none', borderRadius: 8, padding: '6px 16px', fontWeight: 600, fontSize: 15, cursor: 'pointer' }}>Delete</button>
                      </td>
                    </tr>
                  ))}
                  {/* Progress bars for processing documents */}
                  {machineDocs[viewDocsForMachine].filter(doc => doc.status === 'processing').map(doc => (
                    <tr key={`progress-${doc.id}`} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td colSpan={5} style={{ padding: "8px 6px" }}>
                        <div style={{ fontSize: "12px", color: "#666", marginBottom: "4px" }}>
                          Processing: {doc.filename}
                        </div>
                        <ProgressBar 
                          progress={75} // Simulated progress for processing
                          status="Processing document..."
                          isUploading={false}
                          isProcessing={true}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 16 }}>
                <button onClick={() => setViewDocsForMachine(null)} style={{ background: '#eee', color: '#333', border: 'none', borderRadius: 8, padding: '10px 24px', fontWeight: 500, fontSize: 16, cursor: 'pointer' }}>Close</button>
              </div>
            </div>
          </div>
        )}
      </main>
      
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
} 