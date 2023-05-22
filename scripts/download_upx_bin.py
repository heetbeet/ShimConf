import hashlib
import os
import requests
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
import argparse
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPX_DIR = os.path.join(BASE_DIR, "../bin/upx")
CACHE_DIR = Path(tempfile.gettempdir(), "upx-cache")
DEFAULT_VERSION = "4.0.2"

def main(version=DEFAULT_VERSION, cache_download=True):
    # Check if the ZIP file is already cached
    do_download = True
    cache_path = Path(CACHE_DIR, "upx-" + version + ".zip")
    if cache_download and cache_path.exists():
        do_download = False

    if do_download:
        zip_url = f"https://github.com/upx/upx/releases/download/v{version}/upx-{version}-win64.zip"

        # Download the UPX ZIP file
        response = requests.get(zip_url)
        zip_file = zipfile.ZipFile(BytesIO(response.content))

        if cache_download:
            Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(response.content)
    else:
        zip_file = zipfile.ZipFile(cache_path)

    zip_files = [
        i.filename
        for i in zip_file.infolist()
        if len(Path(i.filename).parts) > 1
        and Path(i.filename).parts[0].startswith("upx-")
        and not i.is_dir()
    ]
    dst_files = [Path(UPX_DIR, *Path(i).parts[1:]) for i in zip_files]

    # Don't extract if the files are already extracted
    def test_already_extracted():
        for file, file_path in zip(zip_files, dst_files):
            if not os.path.exists(file_path):
                return False

            src = zip_file.read(file)
            if (
                hashlib.sha256(src).hexdigest()
                != hashlib.sha256(Path(file_path).read_bytes()).hexdigest()
            ):
                return False

        return True

    if not test_already_extracted():
        # Delete all content in the UPX directory
        shutil.rmtree(UPX_DIR, ignore_errors=True)
        Path(UPX_DIR).mkdir(parents=True, exist_ok=True)

        # Extract contents directly into the UPX_DIR
        for file, file_path in zip(zip_files, dst_files):
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with zip_file.open(file) as src, open(file_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

    print(f"Downloaded and extracted UPX v{version} successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="UPX version to download", default=DEFAULT_VERSION)
    parser.add_argument(
        "--cache_download",
        help="Cache the download",
        action="store_true",
        default=True,
    )
    args = parser.parse_args()

    main(args.version, args.cache_download)
