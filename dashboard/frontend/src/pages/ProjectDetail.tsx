import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Button, Space, Spin } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { getProject, getClasses, getCoverage } from "../api/projects";
import { triggerScan, triggerEvaluate, triggerLoop } from "../api/tasks";
import CoverageCard from "../components/CoverageCard";
import ClassTable from "../components/ClassTable";
import LogPanel from "../components/LogPanel";

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: project, isLoading } = useQuery({ queryKey: ["project", id], queryFn: () => getProject(id!) });
  const { data: classList } = useQuery({ queryKey: ["classes", id], queryFn: () => getClasses(id!), enabled: !!project });
  const { data: coverage } = useQuery({ queryKey: ["coverage", id], queryFn: () => getCoverage(id!), enabled: !!project, refetchInterval: 15000 });

  if (isLoading || !project) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  const summary = project.summary;
  const classes = (classList?.classes ?? []).map((c) => ({
    name: c.name,
    package: c.package,
    type: c.type,
    methodCount: c.methods.length,
    lineCoverage: coverage?.overall_coverage?.per_class?.find((pc) => pc.class === c.name)?.line_coverage ?? 0,
    branchCoverage: coverage?.overall_coverage?.per_class?.find((pc) => pc.class === c.name)?.branch_coverage ?? 0,
  }));

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>返回</Button>
        <h2 style={{ margin: 0 }}>{project.name || project.id}</h2>
      </Space>

      <CoverageCard
        line={summary?.coverage?.line ?? 0}
        branch={summary?.coverage?.branch ?? 0}
        methodsPass={summary?.methods?.pass ?? 0}
        methodsTotal={summary?.methods?.total ?? 0}
        phase={summary?.phase ?? "unknown"}
      />

      <Space style={{ marginTop: 16, marginBottom: 16 }}>
        <Button type="primary" onClick={() => triggerScan(id!)}>Phase 1: 扫描</Button>
        <Button onClick={() => triggerEvaluate(id!)}>Phase 3: 评估覆盖率</Button>
        <Button type="primary" danger onClick={() => triggerLoop(id!, 200)}>全自动循环</Button>
      </Space>

      <ClassTable classes={classes} loading={false} />
      <LogPanel projectId={id!} />
    </div>
  );
}
