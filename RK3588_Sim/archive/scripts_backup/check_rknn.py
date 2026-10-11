import importlib.util

spec = importlib.util.find_spec("rknn")
print("rknn spec:", spec)
if spec is not None:
    import rknn
    print("rknn import ok, version file:", getattr(rknn, "__version__", "n/a"))
