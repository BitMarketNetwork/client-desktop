from inspect import currentframe

from .utils import NotImplementedInstance
from .utils.class_property import classproperty


class Debug(NotImplementedInstance):
    _ENABLED = None

    @classmethod
    def assertObjectCaller(cls, object_: object, name: str):
        current_frame = currentframe().f_back.f_back

        current_name = current_frame.f_code.co_name
        if current_name == name:
            if current_frame.f_locals.get("self") == object_:
                return
        current_object = current_frame.f_locals.get("self")

        if current_object is not None:
            current_name = (
                current_object.__class__.__name__ + "." + current_name
            )
        if object_ is not None:
            name = object_.__class__.__name__ + "." + name
        raise AssertionError(
            "invalid caller name '{}', required caller name is '{}'".format(
                current_name, name
            )
        )

    @classproperty
    def isEnabled(cls) -> bool:  # noqa
        assert cls._ENABLED is not None
        return cls._ENABLED

    @classmethod
    def setState(cls, enabled: bool) -> None:
        if cls._ENABLED is not None:
            raise RuntimeError(
                "can't change an already initialized {} state.".format(
                    cls.__name__
                )
            )

        cls._ENABLED = enabled
        if not cls._ENABLED:
            cls.assertObjectCaller = lambda *_, **__: None
