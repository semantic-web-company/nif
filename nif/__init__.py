__all__ = (
    '__version__',
    'version_info'
)

from pbr.version import VersionInfo

_v = VersionInfo('nif').semantic_version()
__version__ = _v.release_string()
version_info = _v.version_tuple()