import { useEffect, useRef, useState } from "react";
import { Card } from "antd";

interface LogEntry {
  type: string;
  level?: string;
  message: string;
  time: string;
}

interface Props {
  projectId: string;
}

export default function LogPanel({ projectId }: Props) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "log" || data.type === "task_complete" || data.type === "task_started" || data.type === "coverage_update" || data.type === "progress") {
        setLogs((prev) => [...prev.slice(-200), { ...data, time: new Date().toLocaleTimeString() }]);
      }
    };

    ws.onclose = () => setLogs((prev) => [...prev, { type: "system", message: "WebSocket disconnected", time: new Date().toLocaleTimeString() }]);

    return () => { ws.close(); };
  }, [projectId]);

  useEffect(() => {
    if (containerRef.current) containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [logs]);

  const levelColor = (level?: string) => {
    if (level === "error") return "#ff4d4f";
    if (level === "warn") return "#faad14";
    return "#52c41a";
  };

  return (
    <Card title="实时日志" style={{ marginTop: 16 }}>
      <div ref={containerRef} style={{ maxHeight: 300, overflowY: "auto", fontFamily: "monospace", fontSize: 13, lineHeight: 1.8 }}>
        {logs.map((log, i) => (
          <div key={i} style={{ color: levelColor(log.level) }}>
            <span style={{ color: "#888" }}>[{log.time}]</span> {log.message}
          </div>
        ))}
        {logs.length === 0 && <div style={{ color: "#888" }}>等待连接...</div>}
      </div>
    </Card>
  );
}
