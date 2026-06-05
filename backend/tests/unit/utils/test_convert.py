"""Unit tests for utils.convert, covering point cloud conversion logic and error handling."""
import os
import pytest
from unittest.mock import patch, MagicMock

from utils.convert import convert_point_cloud
from utils.files import clean_path

def test_convert_point_cloud_missing_tool():
    """Test exception raising if POTREE_CONVERTER_PATH env var is missing."""
    with patch.dict(os.environ, clear=True): # Ensure env is empty
        # Drop POTREE_CONVERTER_PATH
        if "POTREE_CONVERTER_PATH" in os.environ:
            del os.environ["POTREE_CONVERTER_PATH"]
            
        with pytest.raises(Exception, match="PotreeConverter not found"):
            convert_point_cloud("input.laz")


@patch("utils.convert.subprocess.run")
def test_convert_point_cloud_success(mock_subprocess_run):
    """Test standard execution of convert_point_cloud and checking subprocess arguments."""
    
    # Configure mocked subprocess to simulate success output
    mock_result = MagicMock()
    mock_result.returncode = 0
    # Simulate PotreeConverter stdout reporting output location
    mock_result.stdout = "some logs...\noutput location: /app/temp_output\nDone."
    mock_result.stderr = ""
    mock_subprocess_run.return_value = mock_result
    
    with patch.dict(os.environ, {"POTREE_CONVERTER_PATH": "/usr/local/bin/PotreeConverter"}):
        input_file = "test_data/input.laz"
        opt_output = "temp_output"
        
        result_dir = convert_point_cloud(input_file, opt_output)
        
        # Verify returned string matches output location in mock stdout (made absolute)
        assert result_dir == str(clean_path("temp_output"))
        
        # Verify subprocess.run command arguments
        mock_subprocess_run.assert_called_once()
        _, kwargs = mock_subprocess_run.call_args
        
        cmd = kwargs["args"]
        print(cmd)
        assert cmd[0] == str(clean_path("/usr/local/bin/PotreeConverter"))
        assert cmd[1] == str(clean_path(input_file))
        assert "-o" in cmd
        assert str(clean_path(opt_output)) in cmd
        assert "--method" in cmd
        assert "poisson" in cmd


@patch("utils.convert.subprocess.run")
def test_convert_point_cloud_failure(mock_subprocess_run):
    """Test handling of PotreeConverter runtime errors."""
    
    # Configure mocked subprocess to simulate failure
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Segmentation fault"
    mock_subprocess_run.return_value = mock_result
    
    with patch.dict(os.environ, {"POTREE_CONVERTER_PATH": "/path/to/PotreeConverter"}):
        with pytest.raises(RuntimeError, match="PotreeConverter failed: Segmentation fault"):
            convert_point_cloud("input.laz")
