"""S3 upload — uses AWS CLI if available."""
import os
import subprocess
import shutil


def aws_cli_available() -> bool:
    return shutil.which("aws") is not None


def upload_to_s3(local_path: str, bucket: str, key: str, region: str = "us-east-1") -> str:
    """Upload a file to S3 using AWS CLI. Returns S3 URI."""
    if not aws_cli_available():
        raise RuntimeError("AWS CLI not installed. Install with: brew install awscli")

    s3_uri = f"s3://{bucket}/{key}"
    result = subprocess.run(
        ["aws", "s3", "cp", local_path, s3_uri, "--region", region],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"S3 upload failed: {result.stderr}")
    return s3_uri


def upload_directory(local_dir: str, bucket: str, prefix: str, region: str = "us-east-1") -> str:
    """Upload entire directory to S3."""
    if not aws_cli_available():
        raise RuntimeError("AWS CLI not installed")

    s3_uri = f"s3://{bucket}/{prefix}"
    result = subprocess.run(
        ["aws", "s3", "sync", local_dir, s3_uri, "--region", region],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"S3 sync failed: {result.stderr}")
    return s3_uri
