import glob
import os
import pickle
import re
from collections import OrderedDict

import ipywidgets
from ipywidgets.widgets import VBox
import param
from param.parameterized import classlist


ptype2wtype = {
    param.Parameter: ipywidgets.Text,
    param.Selector: ipywidgets.Dropdown,
    param.Boolean: ipywidgets.Checkbox,
    param.Number: ipywidgets.FloatSlider,
    param.Integer: ipywidgets.IntSlider,
}

def wtype(pobj):
    if pobj.constant:
        # constant params shouldn't be editable
        return ipywidgets.HTML
    for t in classlist(type(pobj))[::-1]:
        if t in ptype2wtype:
            return ptype2wtype[t]


class NbParams(param.Parameterized):

    display_fn = param.Callable(default=None)
    
    blocking = param.Boolean(default=True)

    def __init__(self, parameterized, **params):
        self.parameterized = parameterized
        self._widgets = {}
        self.blocked = self.blocking
        super(NbParams, self).__init__(**params)


    def _make_widget(self, p_name):
        p_obj = self.parameterized.params(p_name)
        kw = dict(description=p_name, value=getattr(
            self.parameterized, p_name), tooltip=p_obj.doc)
        if hasattr(p_obj, 'get_range'):
            kw['options'] = p_obj.get_range()
        if hasattr(p_obj, 'bounds'):
            kw['min'],kw['max'] = p_obj.bounds

        if p_name=='name':
            name = kw['value']
            if isinstance(self.parameterized, param.Parameterized):
                name = name[:-5]
            kw['value'] = '<b>%s</b>' % name

        w = wtype(p_obj)(**kw)
        
        def change_event(event):
            setattr(self.parameterized, p_name, event['new'])
        w.observe(change_event, 'value')

        return w

    def widget(self, param_name):
        """Get widget for param_name"""
        if param_name not in self._widgets:
            self._widgets[param_name] = self._make_widget(param_name)
        return self._widgets[param_name]


    def widgets(self):
        """Get widgets for all parameters (i.e. property sheet)"""

        # order by param precedence, but with name first and persist last
        params = self.parameterized.params().items()
        ordered_params = OrderedDict(sorted(params, key=lambda x: x[1].precedence)).keys()
        ordered_params.insert(0,ordered_params.pop(ordered_params.index('name')))

        widgets = [self.widget(pname) for pname in ordered_params]
        if self.display_fn:
            display_button = ipywidgets.Button(description='Display')
            display_button.on_click(lambda x: self.display_fn(self.parameterized))
            widgets.append(display_button)
        if self.blocking:
            display_button = ipywidgets.Button(description='Run')
            display_button.on_click(lambda x: setattr(self, 'blocked', False))
            widgets.append(display_button)
            
        vbox = VBox(children=widgets)
        display(vbox)
        ipython=get_ipython()
        
        if self.blocking:
            while self.blocked:
                time.sleep(0.01)
                ipython.kernel.do_one_iteration()
