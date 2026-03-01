import inspect
import types


class make_cache:
    def __init__(self, func):
        self.func = func
        self.func_name = func.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        # Use a more efficient caching mechanism
        if not hasattr(instance, "_memoize_cache"):
            instance._memoize_cache = {}
        
        def wrapper(*args, **kwargs):
            if self.func_name not in instance._memoize_cache:
                instance._memoize_cache[self.func_name] = self.func(instance, *args, **kwargs)
            return instance._memoize_cache[self.func_name]
        
        return wrapper
