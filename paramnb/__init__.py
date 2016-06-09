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


# belongs in Param
class FileSelector(param.ObjectSelector):
    """
    Given a path glob, allows one file to be selected from those matching.
    """
    __slots__ = ['path']

    def __init__(self, default=None, path="", **kwargs):
        super(FileSelector, self).__init__(default, **kwargs)
        self.path = path
        self.update()

    def update(self):
        self.objects = sorted(glob.glob(self.path))
        if self.default in self.objects:
            return
        self.default = self.objects[0] if self.objects else None


# belongs in Param
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


# belongs in Param
class MultiFileSelector(ListSelector):
    """
    Given a path glob, allows multiple files to be selected from the list of matches.
    """
    __slots__ = ['path']

    def __init__(self, default=None, path="", **kwargs):
        super(MultiFileSelector, self).__init__(default, **kwargs)
        self.path = path
        self.update()

    def update(self):
        self.objects = sorted(glob.glob(self.path))
        if self.default and all([o in self.objects for o in self.default]):
            return
        self.default = self.objects



def NumericWidget(*args, **kw):
    """Returns appropriate slider or text boxes depending on bounds"""
    if (kw['min'] is None or kw['max'] is None):
        return ipywidgets.FloatText(*args,**kw)
    else:
        return ipywidgets.HBox(children=[ipywidgets.FloatSlider(*args,**kw)])
#                                         ipywidgets.BoundedFloatText(*args,**kw)])


def TextWidget(*args, **kw):
    kw['value'] = str(kw['value'])
    return ipywidgets.Text(*args,**kw)


# Maps from Parameter type to ipython widget types with any options desired
ptype2wtype = {
    param.Parameter: (TextWidget,                 {}),
    param.Selector:  (ipywidgets.Dropdown,        {}),
    param.Boolean:   (ipywidgets.Checkbox,        {}),
    param.Number:    (NumericWidget,              {}),
    param.Integer:   (ipywidgets.IntSlider,       {}),
    ListSelector:    (ipywidgets.SelectMultiple,  {}),
}


def wtype(pobj):
    if pobj.constant: # Ensure constant parameters cannot be edited
        return (ipywidgets.HTML, {})
    for t in classlist(type(pobj))[::-1]:
        if t in ptype2wtype:
            return ptype2wtype[t]


def run_next_cells(n):
    if n=='all':
        n = 'NaN'
    elif n<1:
        return

    js_code = """
       var num = {0};
       var run = false;
       var current = $(this)[0];
       $.each(IPython.notebook.get_cells(), function (idx, cell) {{
          if ((cell.output_area === current) && !run) {{
             run = true;
          }} else if ((cell.cell_type == 'code') && !(num < 1) && run) {{
             cell.execute();
             num = num - 1;
          }}
       }});
    """.format(n)

    display(Javascript(js_code))


def estimate_label_width(labels):
    """
    Given a list of labels, estimate the width in pixels
    and return in a format accepted by CSS.
    Necessarily an approximation, since the font is unknown
    and is usually proportionally spaced.
    """
    max_length = max([len(l) for l in labels])
    return "{0}px".format(max(8,int(max_length*7.5)))


def named_objs(objlist):
    """
    Given a list of objects, returns a dictionary mapping from
    string name for the object to the object itself.
    """
    return {k.__name__ if hasattr(k, '__name__') else str(k) : obj
            for k,obj in objlist}


class Widgets(param.ParameterizedFunction):

    callback = param.Callable(default=None, doc="""
        Custom callable to execute on button press
        (if `button`) else whenever a widget is changed,
        Should accept a Parameterized object argument.""")

    next_n = param.Parameter(default=0, doc="""
        When executing cells, integer number to execute (or 'all').
        A value of zero means not to control cell execution.""")

    button = param.Boolean(default=False, doc="""
        Whether to show a button to control cell execution
        If false, will execute `next` cells on any widget
        value change.""")

    label_width = param.Parameter(default=estimate_label_width, doc="""
        Width of the description for parameters in the list, using any
        string specification accepted by CSS (e.g. "100px" or "50%").
        If set to a callable, will call that function using the list of
        all labels to get the value.""")


    def __call__(self, parameterized, **params):
        self.p = param.ParamOverrides(self, params)
        self._widgets = {}
        self.parameterized = parameterized
        self.blocked = self.p.next_n>0 or self.p.callback and not self.p.button

        widgets = self.widgets()
        layout = ipywidgets.Layout(display='flex', flex_flow='row')
        vbox = ipywidgets.VBox(children=widgets, layout=layout)

        display(vbox)

        self.event_loop()

    def _make_widget(self, p_name):
        p_obj = self.parameterized.params(p_name)
        widget_class, widget_options = wtype(p_obj)

        kw = dict(value=getattr(self.parameterized, p_name), tooltip=p_obj.doc)
        kw.update(widget_options)

        if hasattr(p_obj, 'get_range'):
            kw['options'] = named_objs(p_obj.get_range().iteritems())

        if hasattr(p_obj, 'get_soft_bounds'):
            kw['min'], kw['max'] = p_obj.get_soft_bounds()

        w = widget_class(**kw)

        def change_event(event):
            new_values = event['new']
            setattr(self.parameterized, p_name, new_values)
            if not self.p.button:
                self.execute_widget(None)
        w.observe(change_event, 'value')

        # Hack ; should be part of Widget classes
        if hasattr(p_obj,"path"):
            def path_change_event(event):
                new_values = event['new']
                p_obj = self.parameterized.params(p_name)
                p_obj.path = new_values
                p_obj.update()

                # Update default value in widget, ensuring it's always a legal option
                selector = self._widgets[p_name].children[1]
                defaults = p_obj.default
                if not issubclass(type(defaults),list):
                    defaults = [defaults]
                selector.options.update(named_objs(zip(defaults,defaults)))
                selector.value=p_obj.default
                selector.options=named_objs(p_obj.get_range().iteritems())

                if p_obj.objects and not self.p.button:
                    self.execute_widget(None)

            path_w = ipywidgets.Text(value=p_obj.path)
            path_w.observe(path_change_event, 'value')
            w = ipywidgets.VBox(children=[path_w,w])

        return w


    def widget(self, param_name):
        """Get widget for param_name"""
        if param_name not in self._widgets:
            self._widgets[param_name] = self._make_widget(param_name)
        return self._widgets[param_name]


    def execute_widget(self, event):
        self.blocked = False
        run_next_cells(self.p.next_n)
        if self.p.callback is not None:
            self.p.callback(self.parameterized)


    def event_loop(self):
        while self.blocked:
            time.sleep(0.01)
            get_ipython().kernel.do_one_iteration()


    label_format = """<div style="padding: 5px; width: {0};
        text-align: right;">{1}</div>"""


    def widgets(self):
        """Return name,widget boxes for all parameters (i.e., a property sheet)"""

        params = self.parameterized.params().items()
        ordered_params = OrderedDict(sorted(params, key=lambda x: x[1].precedence)).keys()

        # Format name specially
        widgets = [ipywidgets.HTML("<b>"+self.parameterized.name+"</b>")]
        ordered_params.pop(ordered_params.index('name'))

        label_width=self.p.label_width
        if callable(label_width):
            label_width = label_width(self.parameterized.params().keys())

        widgets += [ipywidgets.HBox(children=[ipywidgets.HTML(self.label_format.format(label_width,pname)),
                                              self.widget(pname)])
                   for pname in ordered_params]

        if self.p.button and not (self.p.callback is None and self.p.next_n==0):
            label = 'Run %s' % self.p.next_n if self.p.next_n>0 else "Run"
            display_button = ipywidgets.Button(description=label)
            display_button.on_click(self.execute_widget)
            widgets.append(display_button)

        return widgets
