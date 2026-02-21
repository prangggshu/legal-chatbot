import importlib.util
import sys
import sysconfig
from pathlib import Path


def _load_stdlib_tokenize():
	stdlib_tokenize_path = Path(sysconfig.get_paths()["stdlib"]) / "tokenize.py"
	spec = importlib.util.spec_from_file_location("_stdlib_tokenize", stdlib_tokenize_path)
	if spec is None or spec.loader is None:
		raise RuntimeError("Unable to load stdlib tokenize module.")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


_stdlib_tokenize = _load_stdlib_tokenize()

for _name in dir(_stdlib_tokenize):
	if not _name.startswith("__"):
		globals()[_name] = getattr(_stdlib_tokenize, _name)


if __name__ == "__main__":
	script_dir = Path(__file__).resolve().parent
	if str(script_dir) not in sys.path:
		sys.path.insert(0, str(script_dir))
	from tokenize_dataset import main

	main()
