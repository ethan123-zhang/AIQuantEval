import onnx

m = onnx.load("/home/ethan/rknn_workspace/model/yolov8n.onnx")
print("IR:", m.ir_version, "opset:", m.opset_import[0].version if m.opset_import else None)


def dims_of(tt):
    return [
        d.dim_value if d.HasField("dim_value") else (d.dim_param or "?")
        for d in tt.shape.dim
    ]


for inp in m.graph.input:
    print("input:", inp.name, dims_of(inp.type.tensor_type))
for out in m.graph.output:
    print("output:", out.name, dims_of(out.type.tensor_type))
