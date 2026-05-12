import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, Row, Col, Button, Progress, Tag, Spin } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { listProjects, deleteProject, ProjectConfig } from "../api/projects";

function formatPct(v: number | undefined): number {
  return Math.round((v ?? 0) * 100);
}

export default function ProjectList() {
  const navigate = useNavigate();
  const [showAdd, setShowAdd] = useState(false);
  const { data: projects, isLoading, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    refetchInterval: 10000,
  });

  const handleDelete = async (id: string) => {
    await deleteProject(id);
    refetch();
  };

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
        <h1>UT Orchestrator Dashboard</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/add")}>
          Add Project
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {(projects ?? []).map((p: ProjectConfig) => (
          <Col key={p.id} xs={24} sm={12} lg={8}>
            <Card
              hoverable
              onClick={() => navigate(`/projects/${p.id}`)}
              actions={[
                <DeleteOutlined key="delete" onClick={(e) => { e.stopPropagation(); handleDelete(p.id); }} />,
              ]}
            >
              <Card.Meta
                title={p.name || p.id}
                description={
                  <div>
                    <Tag color={p.summary?.targets_met ? "green" : "orange"}>
                      {p.summary?.phase ?? "unknown"}
                    </Tag>
                    <div style={{ marginTop: 12 }}>
                      <div>Line: <Progress percent={formatPct(p.summary?.coverage?.line)} size="small" /></div>
                      <div>Branch: <Progress percent={formatPct(p.summary?.coverage?.branch)} size="small" /></div>
                      <div style={{ marginTop: 8, fontSize: 12, color: "#888" }}>
                        Methods: {p.summary?.methods?.pass ?? 0}/{p.summary?.methods?.total ?? 0}
                      </div>
                    </div>
                  </div>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
