from __future__ import absolute_import

# doing lazy loading of yaml should carve about 40ms from
# startup time


class _stub(object):
    """A stub for importing functionality from yaml module upon demand

    Supports only callables and attributes ATM.
    """
    def __init__(self, name):
        self.name = name
        self.was_called = False

    @property
    def __realthing__(self):
        import yaml as mod
        from . import yaml as this_mod
        if self.was_called:
            raise RuntimeError("Should have not been called twice!!!!")
        this_mod.__doc__ = mod.__doc__
        a = getattr(mod, self.name)
        setattr(this_mod, self.name, a)
        self.was_called = True
        return a

    def __getattr__(self, name):
        return getattr(self.__realthing__, name)

    def __call__(self, *args, **kwargs):
        return self.__realthing__(*args, **kwargs)


load = _stub('load')
safe_dump = _stub('safe_dump')
safe_load = _stub('safe_load')
SafeDumper = _stub('SafeDumper')