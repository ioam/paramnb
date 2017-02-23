import param

class _View(param.Parameter):
    """
    View parameters hold displayable output, they may have a callback,
    which is called when a new value is set on the parameter.
    Additionally they allow supplying a renderer function which renders
    the display output. The renderer function should return the
    appropriate output for the View parameter (e.g. HTML or PNG data),
    and may optionally supply the desired size of the viewport.
    """

    __slots__ = ['callback', 'renderer']

    def __init__(self, default=None, callback=None, renderer=None, **kwargs):
        self.callback = None
        self.renderer = (lambda x: x) if renderer is None else renderer
        super(_View, self).__init__(default, **kwargs)

    def __set__(self, obj, val):
        super(_View, self).__set__(obj, val)
        if self.callback:
            self.callback(self.renderer(val))


class HTML(_View):
    """
    HTML is a View parameter that allows displaying HTML output.
    """


class Image(_View):
    """
    Image is a View parameter that allows displaying PNG bytestrings.
    """
