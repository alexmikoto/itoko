import importlib

__all__ = ["import_object"]


def import_object(path: str) -> object:
    module, name = path.split(":")
    mod = importlib.import_module(module)
    return getattr(mod, name)
