'''
Variuos utilities.

Copyright 2014, Konstantin Tretyakov
Licensed under MIT.
'''

import types

def with_closing_contextmanager(obj):
    '''Given an object, adds an empty __enter__ method and an __exit__ method that invokes self.close().
    Returns this object.
    Does nothing if any of those methods is already available.
    
     >>> class A:
     ...     def close(self):
     ...         self.closed = True
     ...
     >>> a = A()
     >>> with with_closing_contextmanager(a) as x:
     ...     assert not hasattr(a, 'closed')
     >>> a.closed
     True
     
    '''
    
    if hasattr(obj, '__enter__') or hasattr(obj, '__exit__'):
        return obj
    # http://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object
    obj.__enter__ = types.MethodType(lambda self: self, obj)
    obj.__exit__ = types.MethodType(lambda self, exc_type, exc_value, traceback: self.close(), obj)
    return obj

