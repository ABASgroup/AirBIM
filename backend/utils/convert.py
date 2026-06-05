import os
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

    They will be saved in the path you provide 
    (if it doesn't exist, it will be created automatically).

    Returns:
        str: output location directory
    """
    # resolve converter path using env var
    tool_path = os.getenv("POTREE_CONVERTER_PATH")
    if tool_path:
        tool_path = clean_path(tool_path)
    else:
        raise FileNotFoundError("PotreeConverter not found")

    # make paths safe, so it would not crash with 123 error
    clean_file_path = clean_path(file_path)

    # build command
    # it's just the standard PotreeConverter 2.0 command
    cmd = []
    cmd.append(str(tool_path))
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
        check=False
    )

    # debug output
    print(f"Command: {cmd}")
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    # check for errors
    if result.returncode != 0:
        raise RuntimeError(f"PotreeConverter failed: {result.stderr}")

    # when the output directory is provided explicitly, return it directly
    if output_path:
        return str(clean_output_path)

    # fallback: parse the converter output for the generated directory
    out = re.search(
        r"(?:output location|target directory):\s+'?([^\n']+)'?", result.stdout)
    if out is None:
        raise RuntimeError(
            "PotreeConverter finished successfully, but output directory was not reported in stdout"
        )

    return str(clean_path(out.group(1)))
