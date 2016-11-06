import importlib


def get_attr_from_dotted_path(path):
    providermodname, providerclsname = path.rsplit('.', 1)
    providermod = importlib.import_module(providermodname)
    return getattr(providermod, providerclsname)
