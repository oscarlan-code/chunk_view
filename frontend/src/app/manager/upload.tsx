"use client";
import { useState, useEffect, useRef } from "react";
import ProgressBar from "../../components/ui/progress";

interface KnowledgeItem {
  id: number;
  filename: string;
  type: string;
  status: string;
  upload_time: string;
  machine_id?: number;
  machine_name?: string;
}

interface UploadProgress {
  progress: number;
  status: string;
  isUploading: boolean;
  isProcessing: boolean;
}

interface WebSocketMessage {
  type: string;
  knowledge_id?: number;
  progress?: number;
  status?: string;
  message?: string;
}

export default function UploadKnowledge() {
  const [file, setFile] = useState<File | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [status, setStatus] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [processingItems, setProcessingItems] = useState<Set<number>>(new Set());
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    progress: 0,
    status: "",
    isUploading: false,
    isProcessing: false
  });
  
  const wsRef = useRef<WebSocket | null>(null);
  const clientId = useRef<string>(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    fetchKnowledge();
    
    // Connect to WebSocket for real-time progress updates
    connectWebSocket();
    
    // Poll for status updates every 3 seconds
    const interval = setInterval(() => {
      fetchKnowledge();
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
      console.log("✅ WebSocket connected successfully");
    };
    
    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        console.log("📨 WebSocket message received:", data);
        
        if (data.type === "connected") {
          console.log("✅ WebSocket connection confirmed");
        } else if (data.type === "progress" && data.knowledge_id) {
          console.log(`📊 Progress update: ${data.progress}% - ${data.status}`);
          
          // Update progress for specific knowledge item
          setUploadProgress({
            progress: data.progress || 0,
            status: data.message || data.status || "",
            isUploading: false,
            isProcessing: data.status !== "ready" && data.status !== "failed"
          });
          
          // If processing is complete, update the knowledge list
          if (data.status === "ready" || data.status === "failed") {
            console.log("✅ Processing completed, updating knowledge list");
            fetchKnowledge();
            setUploadProgress({
              progress: 0,
              status: "",
              isUploading: false,
              isProcessing: false
            });
          }
        } else if (data.type === "pong") {
          console.log("🏓 WebSocket ping/pong");
        }
      } catch (error) {
        console.error("❌ Error parsing WebSocket message:", error);
      }
    };
    
    ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
    };
    
    ws.onclose = () => {
      console.log("🔌 WebSocket disconnected");
      // Try to reconnect after 3 seconds
      setTimeout(() => {
        console.log("🔄 Attempting to reconnect WebSocket...");
        connectWebSocket();
      }, 3000);
    };
    
    wsRef.current = ws;
  };

  const fetchKnowledge = async () => {
    try {
      const res = await fetch("http://localhost:8000/knowledge");
      if (res.ok) {
        const data = await res.json();
        setKnowledge(data);
        
        // Track processing items
        const processing = new Set<number>();
        data.forEach((item: KnowledgeItem) => {
          if (item.status === 'processing') {
            processing.add(item.id);
          }
        });
        setProcessingItems(processing);
      }
    } catch (error) {
      console.error("Failed to fetch knowledge:", error);
    }
  };

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

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    
    setUploading(true);
    setStatus("Uploading...");
    
    // Set initial upload progress
    setUploadProgress({
      progress: 0,
      status: "Starting upload...",
      isUploading: true,
      isProcessing: false
    });
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("uploaded_by", "1");
      formData.append("type", getFileType(file));
      formData.append("client_id", clientId.current); // Send client_id for WebSocket updates
      
      console.log("📤 Starting upload with client_id:", clientId.current);
      
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData
      });
      
      if (res.ok) {
        const newItem = await res.json();
        console.log("✅ Upload successful, starting processing...");
        setStatus("Upload successful! Processing document...");
        setKnowledge(prev => [newItem, ...prev]);
        setProcessingItems(prev => new Set([...prev, newItem.id]));
        setFile(null);
        
        // Switch to processing mode
        setUploadProgress({
          progress: 0,
          status: "Processing document...",
          isUploading: false,
          isProcessing: true
        });
        
        // Clear status after 3 seconds
        setTimeout(() => setStatus(""), 3000);
      } else {
        const errorData = await res.json().catch(() => ({}));
        console.error("❌ Upload failed:", errorData);
        setStatus(`Upload failed: ${errorData.detail || 'Unknown error'}`);
        setUploadProgress({
          progress: 0,
          status: "Upload failed",
          isUploading: false,
          isProcessing: false
        });
      }
    } catch (error) {
      console.error("❌ Upload error:", error);
      setStatus("Upload failed");
      setUploadProgress({
        progress: 0,
        status: "Upload failed",
        isUploading: false,
        isProcessing: false
      });
    } finally {
      setUploading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <span style={{ color: '#28a745', fontWeight: 600 }}>✅ Ready</span>;
      case 'processing':
        return <span style={{ color: '#ffc107', fontWeight: 600 }}>🔄 Processing</span>;
      case 'failed':
        return <span style={{ color: '#dc3545', fontWeight: 600 }}>❌ Failed</span>;
      default:
        return <span style={{ color: '#6c757d', fontWeight: 600 }}>⏳ {status}</span>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return '✅';
      case 'processing':
        return '🔄';
      case 'failed':
        return '❌';
      default:
        return '⏳';
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f6fa", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: 'San Francisco, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif' }}>
      <div style={{ background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", padding: 40, minWidth: 400, maxWidth: 600 }}>
        <h2 style={{ fontWeight: 700, fontSize: 28, marginBottom: 24 }}>Upload Knowledge</h2>
        
        <form onSubmit={handleUpload} style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 24 }}>
          <div style={{ border: "2px dashed #ddd", borderRadius: 8, padding: 20, textAlign: "center" }}>
            <input 
              type="file" 
              accept=".pdf,image/*,.txt,.doc,.docx" 
              onChange={e => setFile(e.target.files?.[0] || null)}
              style={{ fontSize: 16, width: "100%" }}
              disabled={uploading}
            />
            {file && (
              <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
                Selected: {file.name}
              </div>
            )}
          </div>
          
          <button 
            type="submit" 
            disabled={!file || uploading}
            style={{ 
              background: uploading ? "#ccc" : "#007aff", 
              color: "#fff", 
              border: "none", 
              borderRadius: 8, 
              padding: "12px 0", 
              fontSize: 18, 
              fontWeight: 500, 
              cursor: uploading ? "not-allowed" : "pointer", 
              transition: "background 0.2s" 
            }}
          >
            {uploading ? "Uploading..." : "Upload Document"}
          </button>
        </form>
        
        {/* Progress Bar */}
        {uploadProgress.progress > 0 && (
          <div style={{ marginBottom: 16 }}>
            <ProgressBar 
              progress={uploadProgress.progress}
              status={uploadProgress.status}
              isUploading={uploadProgress.isUploading}
              isProcessing={uploadProgress.isProcessing}
            />
          </div>
        )}
        
        {status && (
          <div style={{ 
            color: status.includes("successful") ? "#28a745" : status.includes("failed") ? "#dc3545" : "#ffc107", 
            marginBottom: 16,
            padding: "12px",
            borderRadius: "8px",
            background: status.includes("successful") ? "#d4edda" : status.includes("failed") ? "#f8d7da" : "#fff3cd",
            border: `1px solid ${status.includes("successful") ? "#c3e6cb" : status.includes("failed") ? "#f5c6cb" : "#ffeaa7"}`
          }}>
            {status}
          </div>
        )}
        
        <h3 style={{ fontWeight: 600, fontSize: 20, marginBottom: 12 }}>Document Status</h3>
        <div style={{ maxHeight: "400px", overflowY: "auto" }}>
          {knowledge.length === 0 ? (
            <div style={{ textAlign: "center", color: "#666", padding: "20px" }}>
              No documents uploaded yet
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {knowledge.map(k => (
                <div key={k.id} style={{ 
                  background: k.status === 'ready' ? "#d4edda" : k.status === 'processing' ? "#fff3cd" : k.status === 'failed' ? "#f8d7da" : "#f8f9fa", 
                  borderRadius: 8, 
                  padding: 16, 
                  border: `1px solid ${k.status === 'ready' ? "#c3e6cb" : k.status === 'processing' ? "#ffeaa7" : k.status === 'failed' ? "#f5c6cb" : "#dee2e6"}`
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <div style={{ fontWeight: 600, fontSize: 16 }}>{k.filename}</div>
                    {getStatusBadge(k.status)}
                  </div>
                  
                  <div style={{ fontSize: 14, color: "#666", marginBottom: 4 }}>
                    Type: {k.type} • Uploaded: {new Date(k.upload_time).toLocaleString()}
                  </div>
                  
                  {k.machine_name && (
                    <div style={{ fontSize: 14, color: "#666" }}>
                      Machine: {k.machine_name}
                    </div>
                  )}
                  
                  {k.status === 'processing' && (
                    <div style={{ 
                      marginTop: 8, 
                      fontSize: 12, 
                      color: "#856404",
                      display: "flex", 
                      alignItems: "center", 
                      gap: 4 
                    }}>
                      <div style={{ 
                        width: "12px", 
                        height: "12px", 
                        borderRadius: "50%", 
                        border: "2px solid #ffc107", 
                        borderTop: "2px solid transparent",
                        animation: "spin 1s linear infinite"
                      }}></div>
                      Processing document...
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
} 