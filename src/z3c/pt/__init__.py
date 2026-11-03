from importlib.metadata import distribution
from importlib.metadata import PackageNotFoundError

try:
    distribution('chameleon-rst')
    import chameleon_rs.compat
    chameleon_rs.compat.install()
except PackageNotFoundError:
    # Fix a NameError in Chameleon.
    import chameleon.i18n  # noqa: E402


    chameleon.i18n.basestring = (str,)
