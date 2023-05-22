import hashlib
import os
import tempfile
import requests
import tarfile
from io import BytesIO
from pathlib import Path
import shutil
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LUA_DIR = os.path.join(BASE_DIR, "../lua_src")
CACHE_DIR = Path(tempfile.gettempdir(), "lua-cache")
DEFAULT_VERSION = "5.4.3"

def main(version=DEFAULT_VERSION, cache_download=True):
    # Check if the tar.gz file is already cached
    do_download = True
    if cache_download and Path(CACHE_DIR, "lua-" + version + ".tar.gz").exists():
        do_download = False

    if do_download:
        # Define the URL for the Lua source tar.gz
        tar_url = f"https://www.lua.org/ftp/lua-{version}.tar.gz"

        # Download the Lua tar.gz file
        response = requests.get(tar_url)
        tar_file = tarfile.open(fileobj=BytesIO(response.content), mode="r:gz")

        if cache_download:
            Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
            with open(Path(CACHE_DIR, "lua-" + version + ".tar.gz"), "wb") as f:
                f.write(response.content)
    else:
        tar_file = tarfile.open(Path(CACHE_DIR, "lua-" + version + ".tar.gz"))

    tar_files = [
        i.path
        for i in tar_file
        if len(Path(i.path).parts) > 1
        and Path(i.path).parts[0].startswith("lua-")
        and i.isreg()
    ]
    dst_files = [Path(LUA_DIR, *Path(i).parts[1:]) for i in tar_files]

    # Don't extract if the files are already extracted
    def test_already_extracted():
        for file, file_path in zip(tar_files, dst_files):
            if not os.path.exists(file_path):
                return False

            src = tar_file.extractfile(file).read()
            if (
                hashlib.sha256(src).hexdigest()
                != hashlib.sha256(Path(file_path).read_bytes()).hexdigest()
            ):
                return False

        return True

    if not test_already_extracted():
        # Delete all content in the Lua directory
        shutil.rmtree(LUA_DIR, ignore_errors=True)
        Path(LUA_DIR).mkdir(parents=True, exist_ok=True)

        # Extract contents directly into the LUA_DIR
        for file, file_path in zip(tar_files, dst_files):
            file_path.parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_bytes(tar_file.extractfile(file).read())

    print(f"Downloaded and extracted Lua v{version} successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Lua version to download", default=DEFAULT_VERSION)
    parser.add_argument(
        "--cache_download", help="Cache the download", action="store_true", default=True
    )
    args = parser.parse_args()
    main(args.version, args.cache_download)
    