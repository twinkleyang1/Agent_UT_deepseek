import { Modal, Form, Input, InputNumber } from "antd";
import { createProject } from "../api/projects";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function AddProjectModal({ open, onClose, onCreated }: Props) {
  const [form] = Form.useForm();

  const handleOk = async () => {
    const values = await form.validateFields();
    await createProject({
      ...values,
      coverage_targets: {
        line: values.line_target ?? 0.70,
        branch: values.branch_target ?? 0.60,
      },
    });
    form.resetFields();
    onCreated();
  };

  return (
    <Modal title="Register New Project" open={open} onOk={handleOk} onCancel={onClose} width={560}>
      <Form form={form} layout="vertical">
        <Form.Item name="id" label="Project ID" rules={[{ required: true }]}>
          <Input placeholder="e.g. dianping" />
        </Form.Item>
        <Form.Item name="name" label="Project Name">
          <Input placeholder="e.g. Dianping System" />
        </Form.Item>
        <Form.Item name="path" label="Project Path" rules={[{ required: true }]}>
          <Input placeholder="/home/user/projects/my-java-app" />
        </Form.Item>
        <Form.Item name="maven_bin" label="Maven Binary" rules={[{ required: true }]}>
          <Input placeholder="/usr/bin/mvn" />
        </Form.Item>
        <Form.Item name="maven_settings" label="Maven Settings (optional)">
          <Input placeholder="/path/to/settings.xml" />
        </Form.Item>
        <Form.Item name="line_target" label="Line Coverage Target" initialValue={0.70}>
          <InputNumber min={0} max={1} step={0.05} style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item name="branch_target" label="Branch Coverage Target" initialValue={0.60}>
          <InputNumber min={0} max={1} step={0.05} style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item name="batch_size" label="Batch Size" initialValue={5}>
          <InputNumber min={1} max={20} style={{ width: "100%" }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
