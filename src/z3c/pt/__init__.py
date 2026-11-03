from importlib.metadata import PackageNotFoundError
from importlib.metadata import distribution


try:
    distribution('chameleon-rst')
    import chameleon_rs.compat
    chameleon_rs.compat.install()
except PackageNotFoundError:
    # Fix a NameError in Chameleon.
    import chameleon.i18n  # noqa: E402

    chameleon.i18n.basestring = (str,)
