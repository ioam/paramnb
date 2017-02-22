import param

class _View(param.Parameter):
    """
    Output parameters allow representing some output to be displayed.
    Output parameters may have a callback, which is called when a new
    value is set on the parameter. Additionally they should implement
    a render method, which returns the data in a displayable format,
    e.g. HTML.
    """

    __slots__ = ['callback']

    def render(self, value):
        return value

    def __init__(self, default=None, callback=None,**kwargs):
        self.callback = None
        super(_View, self).__init__(default, **kwargs)

    def __set__(self, obj, val):
        super(_View, self).__set__(obj, val)
        if self.callback:
            self.callback(self.render(val))


class HTML(_View, param.String):
    """
    HTML is a View parameter that allows displaying HTML output.
    """


class HView(_View):
    """
    HView is an View parameter meant for displaying HoloViews objects.
    In combination with HoloViews streams this parameter may be used
    to build complex dashboards.
    """

    def render(self, value):
        import holoviews as hv
        backend = hv.Store.current_backend
        renderer = hv.Store.renderers[backend]
        plot = renderer.get_plot(value)
        plot.initialize_plot()
        size = renderer.get_size(plot)
        return renderer.html(plot), size
