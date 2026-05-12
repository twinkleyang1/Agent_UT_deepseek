import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";
import { Spin, Segmented, Card } from "antd";
import { useState } from "react";
import { getCoverageHistory } from "../api/projects";

export default function TrendPage() {
  const { id } = useParams<{ id: string }>();
  const [window, setWindow] = useState<string>("all");
  const { data: history, isLoading } = useQuery({
    queryKey: ["coverage-history", id],
    queryFn: () => getCoverageHistory(id!),
    refetchInterval: 30000,
  });

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  const data = (history ?? [])
    .filter((_, i, arr) => window === "all" || i >= arr.length - (window === "6h" ? 6 : 24))
    .map((h) => ({
      time: h.timestamp ? new Date(h.timestamp).toLocaleTimeString() : "",
      line: Math.round(h.line_coverage * 100),
      branch: Math.round(h.branch_coverage * 100),
    }));

  return (
    <div style={{ padding: 24 }}>
      <h2>覆盖率趋势 — {id}</h2>
      <Segmented
        options={[
          { label: "全部", value: "all" },
          { label: "最近 24 条", value: "24h" },
          { label: "最近 6 条", value: "6h" },
        ]}
        value={window}
        onChange={(v) => setWindow(v as string)}
        style={{ marginBottom: 16 }}
      />
      <Card>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <ReferenceLine y={70} stroke="#faad14" strokeDasharray="5 5" label="Line Target 70%" />
            <ReferenceLine y={60} stroke="#ff4d4f" strokeDasharray="5 5" label="Branch Target 60%" />
            <Line type="monotone" dataKey="line" stroke="#1677ff" name="行覆盖 %" strokeWidth={2} />
            <Line type="monotone" dataKey="branch" stroke="#52c41a" name="分支覆盖 %" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
