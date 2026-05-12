import { Card, Progress, Statistic, Row, Col } from "antd";

interface Props {
  line: number;
  branch: number;
  methodsPass: number;
  methodsTotal: number;
  phase: string;
}

export default function CoverageCard({ line, branch, methodsPass, methodsTotal, phase }: Props) {
  const linePct = Math.round(line * 100);
  const branchPct = Math.round(branch * 100);
  return (
    <Card>
      <Row gutter={16}>
        <Col span={6}><Progress type="circle" percent={linePct} format={() => `${linePct}%`} /><div style={{ textAlign: "center", marginTop: 4 }}>行覆盖</div></Col>
        <Col span={6}><Progress type="circle" percent={branchPct} format={() => `${branchPct}%`} /><div style={{ textAlign: "center", marginTop: 4 }}>分支覆盖</div></Col>
        <Col span={6}><Statistic title="方法已测" value={methodsPass} suffix={`/ ${methodsTotal}`} /></Col>
        <Col span={6}><Statistic title="当前阶段" value={phase} /></Col>
      </Row>
    </Card>
  );
}
