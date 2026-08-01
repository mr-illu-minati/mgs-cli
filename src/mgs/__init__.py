"""mgs — one CLI for Microsoft 365."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("mgs-cli")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.7.1"
