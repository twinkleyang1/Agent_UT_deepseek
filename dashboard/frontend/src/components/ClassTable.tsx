import { Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";

interface ClassRow {
  name: string;
  package: string;
  type: string;
  methodCount: number;
  lineCoverage: number;
  branchCoverage: number;
}

const columns: ColumnsType<ClassRow> = [
  { title: "类名", dataIndex: "name", key: "name", sorter: (a, b) => a.name.localeCompare(b.name) },
  { title: "包", dataIndex: "package", key: "package", ellipsis: true },
  { title: "类型", dataIndex: "type", key: "type", render: (t: string) => <Tag>{t}</Tag> },
  { title: "方法数", dataIndex: "methodCount", key: "methodCount" },
  { title: "行覆盖", dataIndex: "lineCoverage", key: "lineCoverage", sorter: (a, b) => a.lineCoverage - b.lineCoverage, render: (v: number) => `${Math.round(v * 100)}%` },
  { title: "分支覆盖", dataIndex: "branchCoverage", key: "branchCoverage", sorter: (a, b) => a.branchCoverage - b.branchCoverage, render: (v: number) => `${Math.round(v * 100)}%` },
];

interface Props {
  classes: ClassRow[];
  loading: boolean;
}

export default function ClassTable({ classes, loading }: Props) {
  return (
    <Table
      dataSource={classes}
      columns={columns}
      loading={loading}
      rowKey="name"
      size="small"
      pagination={{ pageSize: 20 }}
    />
  );
}
