import subprocess
import re
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
    # TODO: hide and make smarter
    # TODO: add exception raising
    TOOL_DIR = "/opt/potreeconverter/PotreeConverter"
    TOOL_DIR = clean_path(TOOL_DIR)

    # make paths safe, so it would not crash with 123 error
    clean_file_path = clean_path(file_path)

    # build command
    # it's just the standard PotreeConverter 2.0 command
    cmd = []
    cmd.append(TOOL_DIR)
    cmd.append(clean_file_path)

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
        check=True
    )
    # temporary measure
    print(result.stdout)

    # extract output location from logs
    out = re.search(r'output location: .+\n', result.stdout)
    out = out.group(0).split()[2]
    out = str(clean_path(out))
    return out
