from os import walk
from os.path import dirname, pardir, join, realpath
from zipfile import ZipFile


def pack() -> str:
    module_dir: str = realpath(join(dirname(__file__), pardir, pardir))
    zip_path: str = realpath(join(module_dir, pardir, 'Shelly.zip'))
    with ZipFile(join(zip_path), 'w') as zipf:
        for root, dirs, files in walk(module_dir):
            if 'venv' in root or '__pycache__' in root or '.idea' in root:
                continue
            module_root: str = root[root.find("Shelly")-1:]
            zipf.mkdir(module_root)
            for file in files:
                actual_path: str = join(root, file)
                module_path: str = join(module_root, file)
                zipf.write(actual_path, module_path)

    return zip_path
