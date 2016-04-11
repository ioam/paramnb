import time
import glob
import os
import pickle
import re
from collections import OrderedDict

from IPython.display import display, Javascript
import ipywidgets
from ipywidgets.widgets import VBox

import param
from param.parameterized import classlist

IPYTHON = get_ipython()

class FileSelector(param.String):
    """
    Defines a glob to select a list of files.
    """


ptype2wtype = {
    param.Parameter: ipywidgets.Text,
    param.Selector: ipywidgets.Dropdown,
    param.Boolean: ipywidgets.Checkbox,
    param.Number: ipywidgets.FloatSlider,
    param.Integer: ipywidgets.IntSlider,
    FileSelector: ipywidgets.Dropdown,
}


def wtype(pobj):
    if pobj.constant:
        # constant params shouldn't be editable
        return ipywidgets.HTML
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

class NbParams(param.ParameterizedFunction):

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
        vbox = VBox(children=widgets)
        display(vbox)
        if self.execute:
            self.event_loop()

    def _make_widget(self, p_name):
        p_obj = self.parameterized.params(p_name)
        widget_class = wtype(p_obj)

        kw = dict(description=p_name, value=getattr(
            self.parameterized, p_name), tooltip=p_obj.doc)
        if hasattr(p_obj, 'get_range'):
            kw['options'] = p_obj.get_range()
        if hasattr(p_obj, 'bounds'):
            kw['min'], kw['max'] = p_obj.bounds if p_obj.bounds else (None, None)

        if isinstance(p_obj, FileSelector):
            files = glob.glob(kw['value'])
            kw['value'] = files[0] if files else ''
            kw['options'] = files
        elif issubclass(widget_class, ipywidgets.Text):
            kw['value'] = str(kw['value'])
        elif p_name=='name':
            name = kw['value']
            if isinstance(self.parameterized, param.Parameterized):
                name = name[:-5]
            kw['value'] = '<b>%s</b>' % name

        w = widget_class(**kw)
        
        def change_event(event):
            setattr(self.parameterized, p_name, event['new'])
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
            IPYTHON.kernel.do_one_iteration()


    def widgets(self):
        """Display widgets for all parameters (i.e. property sheet)"""
        # order by param precedence, but with name first and persist last
        params = self.parameterized.params().items()
        ordered_params = OrderedDict(sorted(params, key=lambda x: x[1].precedence)).keys()
        ordered_params.insert(0,ordered_params.pop(ordered_params.index('name')))

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
