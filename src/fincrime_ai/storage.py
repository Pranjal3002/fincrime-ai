"""Local-first storage; S3 mapping only, with no network or credential discovery."""

from pathlib import Path


class LocalStore:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def resolve(self, key):
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Storage key escapes configured root")
        return path


def s3_uri(bucket, key):
    """Pure architecture adapter: returns a URI; does not upload or read AWS."""
    if not bucket or "/" in bucket or key.startswith("/") or ".." in key.split("/"):
        raise ValueError("Invalid logical S3 location")
    return f"s3://{bucket}/{key}"
