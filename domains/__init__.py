import importlib

def load(name="protein"):
    return importlib.import_module(f"domains.{name}")
