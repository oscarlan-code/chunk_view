"use client";

interface ProgressBarProps {
  progress: number; // 0-100
  status: string;
  isUploading?: boolean;
  isProcessing?: boolean;
}

export default function ProgressBar({ progress, status, isUploading = false, isProcessing = false }: ProgressBarProps) {
  const getStatusColor = () => {
    if (isUploading) return "#007aff";
    if (isProcessing) return "#ffc107";
    if (progress === 100) return "#28a745";
    return "#007aff";
  };

  const getStatusIcon = () => {
    if (isUploading) return "📤";
    if (isProcessing) return "⚙️";
    if (progress === 100) return "✅";
    return "🔄";
  };

  return (
    <div style={{ 
      width: "100%", 
      background: "#f0f0f0", 
      borderRadius: "8px", 
      overflow: "hidden",
      marginTop: "8px",
      border: "1px solid #e0e0e0"
    }}>
      <div style={{
        width: `${progress}%`,
        height: "12px",
        background: getStatusColor(),
        transition: "width 0.3s ease",
        borderRadius: "8px",
        position: "relative"
      }}>
        <div style={{
          position: "absolute",
          right: "8px",
          top: "50%",
          transform: "translateY(-50%)",
          fontSize: "10px",
          color: "white",
          fontWeight: "bold",
          textShadow: "1px 1px 1px rgba(0,0,0,0.5)"
        }}>
          {progress}%
        </div>
      </div>
      <div style={{
        fontSize: "12px",
        color: "#666",
        marginTop: "6px",
        textAlign: "center",
        fontWeight: 500,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "4px"
      }}>
        <span>{getStatusIcon()}</span>
        <span>{status}</span>
        {progress < 100 && (
          <span style={{ fontSize: "10px", color: "#999" }}>
            ({progress}%)
          </span>
        )}
      </div>
    </div>
  );
} 