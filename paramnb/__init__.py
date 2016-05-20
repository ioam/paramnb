"""
Jupyter notebook interface for Param (https://github.com/ioam/param).

Given a Parameterized object, displays a box with an ipywidget for each
Parameter, allowing users to view and and manipulate Parameter values
from within a Jupyter/IPython notebook.  
"""

import time
import glob

from collections import OrderedDict

from IPython import get_ipython
from IPython.display import display, Javascript

import ipywidgets

import param
from param.parameterized import classlist


class FileSelector(param.ObjectSelector):
    """
    Given a path glob, allows one file to be selected from those matching.
    """
    __slots__ = ['path']

    def __init__(self, default=None, path="", **kwargs):
        super(FileSelector, self).__init__(default, **kwargs)
        self.path = path
        self.objects = sorted(glob.glob(self.path))
        if self.default is None and self.objects:
            self.default = self.objects[0]



class ListSelector(param.ObjectSelector):
    """
    Variant of ObjectSelector where the value can be multiple objects from
    a list of possible objects.
    """

    def compute_default(self):
        if self.default is None and callable(self.compute_default_fn):
            self.default = self.compute_default_fn()
            for o in self.default:
                if self.default not in self.objects:
                    self.objects.append(self.default)

    def _check_value(self, val, obj=None):
        for o in val:
            super(ListSelector, self)._check_value(o, obj)


class MultiFileSelector(ListSelector):
    """
    Given a path glob, allows multiple files to be selected from the list of matches.
    """
    __slots__ = ['path']

    def __init__(self, default=None, path="", **kwargs):
        super(MultiFileSelector, self).__init__(default, **kwargs)
        self.path = path
        self.objects = sorted(glob.glob(self.path))
        if self.default is None and self.objects:
            self.default = self.objects


# Maps from Parameter type to ipython widget types with any options desired
ptype2wtype = {
    param.Parameter: (ipywidgets.Text,            {}),
    param.Selector:  (ipywidgets.Dropdown,        {}),
    param.Boolean:   (ipywidgets.Checkbox,        {}),
    param.Number:    (ipywidgets.FloatSlider,     {}),
    param.Integer:   (ipywidgets.IntSlider,       {}),
    ListSelector:    (ipywidgets.SelectMultiple,  {}),
}


def wtype(pobj):
    # Achieves making constant parameters not editable, but doesn't show their names
    if pobj.constant:
        return (ipywidgets.HTML, {})
    for t in classlist(type(pobj))[::-1]:
        if t in ptype2wtype:
            return ptype2wtype[t]


def run_cells_below():
    js_code = """
       var nb = IPython.notebook;
       nb.execute_cell_range(nb.get_selected_index()+1, nb.ncells());
    """
    display(Javascript(js_code))


def run_next_cell():
    js_code = """
       var nb = IPython.notebook;
       var index = nb.get_selected_index();
       nb.execute_cell_range(index+1, index+2);
    """
    display(Javascript(js_code))


execution_hooks = {'below': run_cells_below,
                   'next': run_next_cell}


class Widgets(param.ParameterizedFunction):

    callback = param.Callable(default=None, allow_None=True, doc="""
        Custom callable to execute on button press or onchange.""")

    execute = param.ObjectSelector(default='below', allow_None=True,
                                   objects=['below', 'next'], doc="""
        Whether to execute cells 'below', the 'next' cell or None.""")

    onchange = param.Boolean(default=False, doc="""
        Whether to execute callback events onchange or on button press.""")

    halt = param.Boolean(default=False, doc="""
        Halt execution until event is generated.""")

    def __call__(self, parameterized, **params):
        self.p = param.ParamOverrides(self, params)
        self._widgets = {}
        self.parameterized = parameterized
        self.blocked = self.execute is not None
        widgets = self.widgets()
        vbox = ipywidgets.Box(children=widgets, layout=layout)

        display(vbox)
        if self.execute:
            self.event_loop()

    def _make_widget(self, p_name):
        p_obj = self.parameterized.params(p_name)
        widget_class, widget_options = wtype(p_obj)

        kw = dict(description=p_name, value=getattr(
            self.parameterized, p_name), tooltip=p_obj.doc)
        kw.update(widget_options)

        if hasattr(p_obj, 'get_range'):
            # List of available objects with concise names
            kw['options'] = {(key.__name__ if hasattr(key, '__name__') else str(key)):obj
                             for key,obj in p_obj.get_range().iteritems()}

        if hasattr(p_obj, 'get_soft_bounds'):
            kw['min'], kw['max'] = p_obj.get_soft_bounds()
           
        if issubclass(widget_class, ipywidgets.Text):
            kw['value'] = str(kw['value'])
        elif p_name == 'name':
            name = kw['value']
            if isinstance(self.parameterized, param.Parameterized):
                name = name[:-5]
            kw['value'] = '<b>%s</b>' % name

        if issubclass(type(p_obj), param.Number) and (kw['min'] is None or kw['max'] is None):
            # Supress slider if the range is not bounded
            widget_class = ipywidgets.FloatText

        w = widget_class(**kw)

        def change_event(event):
            new_values = event['new']
            setattr(self.parameterized, p_name, new_values)
            if self.p.onchange:
                self.execute_widget(None)
        w.observe(change_event, 'value')

        return w


    def widget(self, param_name):
        """Get widget for param_name"""
        if param_name not in self._widgets:
            self._widgets[param_name] = self._make_widget(param_name)
        return self._widgets[param_name]


    def execute_widget(self, event):
        self.blocked = False
        if self.p.halt:
            self.p.halt = False
        elif self.p.execute:
            execution_hooks[self.p.execute]()
        if self.p.callback:
            self.p.callback(self.parameterized)


    def event_loop(self):
        while self.blocked:
            time.sleep(0.01)
            get_ipython().kernel.do_one_iteration()


    def widgets(self):
        """Display widgets for all parameters (i.e. property sheet)"""
        # order by param precedence, but with name first
        params = self.parameterized.params().items()
        ordered_params = OrderedDict(sorted(params, key=lambda x: x[1].precedence)).keys()
        ordered_params.insert(0, ordered_params.pop(ordered_params.index('name')))

        widgets = [self.widget(pname) for pname in ordered_params]
        button = None
        if self.p.onchange:
            pass
        elif self.blocked:
            button = 'Run %s' % self.p.execute
        elif self.p.callback:
            button = 'Execute'
        if button:
            display_button = ipywidgets.Button(description=button)
            display_button.on_click(self.execute_widget)
            widgets.append(display_button)
        return widgets
