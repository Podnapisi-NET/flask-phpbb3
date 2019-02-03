from __future__ import absolute_import

import pkg_resources

__version__ = pkg_resources.get_distribution(__name__).version

from .extension import PhpBB3

__all__ = (
    'PhpBB3',
)
