import hashlib
import os
import tempfile
import requests
import zipfile
from io import BytesIO
from pathlib import Path
import shutil
import argparse
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICU_DIR = os.path.join(BASE_DIR, "../icu_src")
CACHE_DIR = Path(tempfile.gettempdir(), "icu-cache")
DEFAULT_VERSION = "73-1"

def main(version=DEFAULT_VERSION, cache_download=True):
    # Check if the zip file is already cached
    do_download = True
    if cache_download and Path(CACHE_DIR, "icu-release-" + version + ".zip").exists():
        do_download = False

    if do_download:
        # Define the URL for the ICU source zip
        zip_url = f"https://github.com/unicode-org/icu/archive/refs/tags/release-{version}.zip"

        # Download the ICU zip file
        response = requests.get(zip_url)
        zip_file = zipfile.ZipFile(BytesIO(response.content))

        if cache_download:
            Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
            with open(Path(CACHE_DIR, "icu-release-" + version + ".zip"), "wb") as f:
                f.write(response.content)
    else:
        zip_file = zipfile.ZipFile(Path(CACHE_DIR, "icu-release-" + version + ".zip"))

    path_re = re.compile(r"icu-[^\\/]+[/\\]icu4c[/\\]source[/\\].*")
    zip_files = [
        i.filename
        for i in zip_file.filelist
        if path_re.match(i.filename)
        and i.file_size > 0
    ]
    dst_files = [Path(ICU_DIR, *Path(i).parts[3:]) for i in zip_files]

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
        # Delete all content in the ICU directory
        shutil.rmtree(ICU_DIR, ignore_errors=True)
        Path(ICU_DIR).mkdir(parents=True, exist_ok=True)

        # Extract contents directly into the ICU_DIR
        for file, file_path in zip(zip_files, dst_files):
            file_path.parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_bytes(zip_file.read(file))

    print(f"Downloaded and extracted ICU release-{version} successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="ICU release version to download", default=DEFAULT_VERSION)
    parser.add_argument(
        "--cache_download", help="Cache the download", action="store_true", default=True
    )
    args = parser.parse_args()
    main(args.version, args.cache_download)
