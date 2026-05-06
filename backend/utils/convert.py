import os
import subprocess
import re
from pathlib import Path
from utils.files import clean_path


def convert_point_cloud(
    file_path: str,
    output_path: str | None = None
) -> str:
    """
    Converts point cloud file (.las / .laz) into an LOD structure for real-time rendering.

    Uses PotreeConverter 2.0.

    Outputs 4 files:
    - metadata.json
    - hierarchy.bin
    - points.bin
    - log.txt

    They will be saved in the path you provide (if it doesn't exist, it will be created automatically).

    Returns output location.
    """
    # resolve converter path: env var → /usr/local/bin → /opt/potreeconverter
    tool_bin = os.getenv("POTREE_CONVERTER_BIN")
    if tool_bin:
        TOOL_DIR = clean_path(tool_bin)
    elif Path("/usr/local/bin/PotreeConverter").exists():
        TOOL_DIR = clean_path("/usr/local/bin/PotreeConverter")
    else:
        TOOL_DIR = clean_path("/opt/potreeconverter/PotreeConverter")

    # make paths safe, so it would not crash with 123 error
    clean_file_path = clean_path(file_path)

    # build command
    # it's just the standard PotreeConverter 2.0 command
    cmd = []
    cmd.append(str(TOOL_DIR))
    cmd.append(str(clean_file_path))

    if output_path:
        clean_output_path = clean_path(output_path)
        cmd.append("-o")
        cmd.append(str(clean_output_path))

    cmd.append("--method")
    cmd.append("poisson")

    # run command
    result = subprocess.run(
        args=cmd,
        capture_output=True,
        text=True,
        check=False  # не бросать исключение сразу
    )
    
    # debug output
    print(f"Command: {cmd}")
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")
    
    # check for errors
    if result.returncode != 0:
        raise RuntimeError(f"PotreeConverter failed: {result.stderr}")

    # extract output location from logs
    out = re.search(r'output location: .+\n', result.stdout)
    out = out.group(0).split()[2]
    out = str(clean_path(out))
    return out
