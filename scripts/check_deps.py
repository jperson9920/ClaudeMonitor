import sys
import importlib.util as iu

print(sys.version)
print("PYQT5:", iu.find_spec("PyQt5") is not None)
print("QDARK:", iu.find_spec("qdarktheme") is not None)