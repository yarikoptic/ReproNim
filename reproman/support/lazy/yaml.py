from __future__ import absolute_import

# doing lazy loading of yaml should carve about 40ms from
# startup time


class _stub(object):
    """A stub for importing functionality from yaml module upon demand

    Supports only callables and attributes ATM.
    """

    _representers = []
    _mod = None
    _this_mod = None


    def __init__(self, name):
        self.name = name
        self.was_called = False

    @classmethod
    def __real_import(cls):
        import yaml as mod
        from . import yaml as this_mod
        cls._mod = mod
        cls._this_mod = this_mod
        this_mod.__doc__ = mod.__doc__
        for args in cls._representers:
            this_mod.SafeDumper.add_representer(*args)

    @property
    def __realthing__(self):
        if self.was_called:
            raise RuntimeError("Should have not been called twice!!!!")
        if self._mod is None:
            self.__real_import()

        a = getattr(self._mod, self.name)
        setattr(self._this_mod, self.name, a)
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


def _add_representer(*args):
    """A lazy collection of representers to be given to real SafeDumper when
    we finally import yaml"""
    _stub._representers.append(args)