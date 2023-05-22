from pathlib import Path
import sys
import subprocess
import os
import shutil
import hashlib
import json

this_dir = Path(__file__).parent
project_dir = this_dir.parent
py = (this_dir / "../venv/Scripts/python.exe").resolve()

if not py.exists():
    import subprocess
    subprocess.run(["python", "-m", "venv", "venv"], cwd=this_dir.parent, check=True)
    subprocess.call([py, "-m", "pip", "install", "-r", this_dir / "requirements.txt"], cwd=this_dir.parent)

if Path(sys.executable) != py:
    sys.exit(subprocess.run([py, __file__] + sys.argv[1:], check=False).returncode)
    
def dir_hash(path):
    return hashlib.sha256(
        b"e00939561f0d401a8ce348d2f8101a8c".join([str(i.relative_to(path)).encode() + i.read_bytes() for i in Path(path).rglob("*") if i.is_file() and i.name != ".compilehashes.json"])
    ).hexdigest()


class HashVerify:
    def __init__(self, src_dir, dst_dir) -> None:
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.hash_json = Path(dst_dir, ".compilehashes.json")
        self.src_hash_store, self.dst_hash_store = json.loads(self.hash_json.read_text()) if self.hash_json.exists() else [None, None]

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        src_hash = dir_hash(self.src_dir)
        dst_hash = dir_hash(self.dst_dir)

        Path(self.dst_dir).parent.mkdir(parents=True, exist_ok=True)
        
        self.hash_json.parent.mkdir(parents=True, exist_ok=True)
        self.hash_json.write_text(json.dumps([src_hash, dst_hash]))
        
    def check(self) -> bool:
        return self.src_hash_store == dir_hash(self.src_dir) and self.dst_hash_store == dir_hash(self.dst_dir)
    

# Do all the pip install stuff
with HashVerify(this_dir, this_dir.parent / "venv") as hash_verify:
    if not hash_verify.check():
        subprocess.call([py, "-m", "pip", "install", "-r", this_dir / "requirements.txt"], cwd=this_dir.parent, stdout=subprocess.DEVNULL)
    else:
        print("venv Requirements is up to date.")


sys.path.insert(0, str(this_dir))
import download_lua_src
import download_upx_bin
import download_icu_src
from glob import glob


download_lua_src.main()
download_upx_bin.main()
download_icu_src.main()

def source_vcvars():
    # Detecting Visual Studio
    try:
        vcvars_path = max(glob("C:\\Program Files\\Microsoft Visual Studio\\*\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat"))
    except ValueError:
        raise RuntimeError("Visual Studio not found in the default location. Please install Visual Studio 2019 or later.")

    # Run the source command and grab the environment variable changes
    div = "5cc27c9af73d11edb67e0242ac120002"
    process = subprocess.Popen(rf'"{vcvars_path}" && echo {div} && set', stdout=subprocess.PIPE, shell=True)
    lhs, rhs = process.communicate()[0].decode().split(div)
    print(lhs)

    os.environ.update({
        line.split('=', 1)[0]: line.split('=', 1)[1] for line in rhs.strip().splitlines() if '=' in line
    })


def clean_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    Path(path).mkdir(exist_ok=True)

os.chdir(this_dir.parent)

source_vcvars()

# Add all the directories to INCLUDE
os.environ["INCLUDE"] = f"{os.environ['INCLUDE']};{project_dir}\\lua_src\\src;{project_dir}\\src;"
for i in Path(project_dir, "icu_src").glob("*"):
    if i.is_dir():
        os.environ["INCLUDE"] += f";{i}"


# Compile Lua
with HashVerify("lua_src", "build/lua_src") as hash_verify:
    if not hash_verify.check():
        clean_dir("build/lua_src")
        for path in Path("lua_src/src").glob("*.c"):
            if path.name in ["lua.c", "luac.c"]:
                continue
            subprocess.call(["cl", "/nologo", "/c", f"/Fobuild/lua_src/{path.name}.obj", f"lua_src\\src\\{path.name}"], shell=True)    
    else:
        print("Lua objects is up to date.")


with HashVerify("icu_src/common", "build/icu_src/common") as hash_verify:
    if not hash_verify.check():
        clean_dir("build/icu_src/common")
        for path in Path("icu_src/common").glob("*.cpp"):
            subprocess.call(["cl", "/nologo", "/c", f"/Fobuild/icu_src/common/{path.name}.obj", f"icu_src\\common\\{path.name}"], shell=True)


clean_dir("dist")
for path in Path("src").glob("*.cpp"):
    clean_dir("dist")

    clean_dir(dst := "build/src-SHELL")
    subprocess.call(["cl", "/nologo", "/c", f"/Fo{dst}/{path.name}.obj", "/EHsc", "/std:c++20", "/W3", "/DSHELL", f"src/{path.name}"], shell=True)
    subprocess.call(["link", "/nologo", f"/out:dist/ShimConf-shell-64bit.exe", "build/lua_src/*.obj", f"{dst}/*.obj"], shell=True)
    subprocess.call([f"{project_dir}/bin/upx/upx.exe", "dist/ShimConf-shell-64bit.exe", "-o", "dist/ShimConf-shell-64bit-upx.exe"], shell=True)


    clean_dir(dst := "build/src-GUI")
    subprocess.call(["cl", "/nologo", "/c", f"/Fo{dst}/{path.name}.obj", "/EHsc", "/std:c++20", "/W3", "/DGUI", f"src/{path.name}"], shell=True)
    subprocess.call(["link", "/nologo", f"/out:dist/ShimConf-gui-64bit.exe", "build/lua_src/*.obj", f"{dst}/*.obj"], shell=True)
    subprocess.call([f"{project_dir}/bin/upx/upx.exe", "dist/ShimConf-gui-64bit.exe", "-o", "dist/ShimConf-gui-64bit-upx.exe"], shell=True)



    Path("dist\\ShimConf-shell-64bit.lua").write_text(
"""
exec = "notepad.exe"
args = "/h"
"""
)