import re

import param
from param.parameterized import classlist

import ipywidgets
from ipywidgets import (SelectMultiple, Button, HBox, VBox, Layout,
                        Text, HTML, FloatSlider, FloatText, IntText,
                        IntSlider, SelectMultiple, Image, ColorPicker,
                        FloatRangeSlider, IntRangeSlider)
from traitlets import Unicode

from .util import named_objs
from .view import HTML as HTMLView, Image as ImageView


def FloatWidget(*args, **kw):
    """Returns appropriate slider or text boxes depending on bounds"""
    has_bounds = not (kw['min'] is None or kw['max'] is None)
    return (FloatSlider if has_bounds else FloatText)(*args,**kw)


def IntegerWidget(*args, **kw):
    """Returns appropriate slider or text boxes depending on bounds"""
    has_bounds = not (kw['min'] is None or kw['max'] is None)
    return (IntSlider if has_bounds else IntText)(*args,**kw)


def TextWidget(*args, **kw):
    """Forces a parameter value to be text"""
    kw['value'] = str(kw['value'])
    return Text(*args,**kw)


def HTMLWidget(*args, **kw):
    """Forces a parameter value to be text, displayed as HTML"""
    kw['value'] = str(kw['value'])
    return HTML(*args,**kw)


def DateWidget(*args, **kw):
    """
    DateWidget to pick datetime type, if bounds but no default is
    defined default to min.
    """
    if kw.get('value') is None and 'min' in kw:
        kw['value'] = kw['min']
    return DatePicker(*args, **kw)


def ColorWidget(*args, **kw):
    """Color widget to pick hex color (defaults to black)"""
    if kw.get('value') is None:
        kw['value'] = '#000000'
    return ColorPicker(*args, **kw)


class RangeWidget(param.ParameterizedFunction):
    """
    Range widget switches between integer and float slider dynamically
    and computes the step size based based on the steps parameter.
    """

    steps = param.Integer(default=50, doc="""
       Number of steps used to compute step size for float range.""")

    def __call__(self, *args, **kw):
        has_bounds = not (kw['min'] is None or kw['max'] is None)
        if not has_bounds:
            return TextWidget(*args,**kw)
        if all(kw[k] is None or isinstance(kw[k], int)
               for k in ['min', 'max']):
            widget = IntRangeSlider
            kw['step'] = 1
        else:
            widget = ipywidgets.FloatRangeSlider
            if not 'step' in kw:
                kw['step'] = float((kw['max'] - kw['min']))/self.steps
        return widget(*args, **kw)


class ListSelectorWidget(param.ParameterizedFunction):
    """
    Selects the appropriate ListSelector widget depending on the number
    of items.
    """

    item_limit = param.Integer(default=20, allow_None=True, doc="""
        The number of items in the ListSelector before it switches from
        a regular SelectMultiple widget to a two-pane CrossSelect widget.
        Setting the limit to None will disable the CrossSelect widget
        completely while a negative value will force it to be enabled.
    """)

    def __call__(self, *args, **kw):
        item_limit = kw.pop('item_limit', self.item_limit)
        if item_limit is not None and len(kw['options']) > item_limit:
            return CrossSelect(*args, **kw)
        else:
            return SelectMultiple(*args, **kw)


def ActionButton(*args, **kw):
    """Returns a ipywidgets.Button executing a paramnb.Action."""
    kw['description'] = str(kw['name'])
    value = kw["value"]
    w = ipywidgets.Button(*args,**kw)
    if value: w.on_click(value)
    return w


class CrossSelect(SelectMultiple):
    """
    CrossSelect provides a two-tab multi-selection widget with regex
    text filtering. Items can be transferred with buttons between the
    selected and unselected options.
    """

    def __init__(self, *args, **kwargs):
        # Compute selected and unselected values
        options = kwargs.get('options', {})
        if isinstance(options, list):
            options = named_objs([(opt, opt) for opt in options])
        self._reverse_lookup = {v: k for k, v in options.items()}
        selected = [self._reverse_lookup[v] for v in kwargs.get('value', [])]
        unselected = [k for k in options if k not in selected]

        # Define whitelist and blacklist
        self._lists = {False: SelectMultiple(options=unselected),
                       True: SelectMultiple(options=selected)}

        self._lists[False].observe(self._update_selection, 'value')
        self._lists[True].observe(self._update_selection, 'value')

        # Define buttons
        button_layout = Layout(width='50px')
        self._buttons = {False: Button(description='<<', layout=button_layout),
                         True: Button(description='>>', layout=button_layout)}
        self._buttons[False].on_click(self._apply_selection)
        self._buttons[True].on_click(self._apply_selection)

        # Define search
        self._search = {False: Text(placeholder='Filter available options'),
                        True: Text(placeholder='Filter selected options')}
        self._search[False].observe(self._filter_options, 'value')
        self._search[True].observe(self._filter_options, 'value')

        # Define Layout
        no_margin = Layout(margin='0')
        row_layout = Layout(margin='0', display='flex', justify_content='space-between')

        search_row = HBox([self._search[False], self._search[True]])
        search_row.layout = row_layout
        button_box = VBox([self._buttons[True], self._buttons[False]],
                          layout=Layout(margin='auto 0'))
        tab_row = HBox([self._lists[False], button_box, self._lists[True]])
        tab_row.layout = row_layout
        self._composite = VBox([search_row, tab_row], layout=no_margin)

        self.observe(self._update_options, 'options')
        self.observe(self._update_value, 'value')

        self._selected = {False: [], True: []}
        self._query = {False: '', True: ''}
        super(CrossSelect, self).__init__(*args, **dict(kwargs, options=options))


    def _update_value(self, event):
        selected = [self._reverse_lookup.get(v, v) for v in event['new']]
        self._lists[True].options = selected
        self._lists[True].value = []
        self._lists[False].options = [o for o in self.options
                                      if o not in selected]

    def _update_options(self, event):
        """
        Updates the options of each of the sublists after the options
        for the whole widget are updated.
        """
        self._reverse_lookup = {v: k for k, v in event['new'].items()}
        options = list(event['new'].keys()) if isinstance(event, dict) else event['new']
        self._selected[False] = []
        self._selected[True] = []
        self._lists[True].options = ['']
        self._lists[True].value = []
        self._lists[False].options = options
        self._lists[False].value = []
        self._apply_filters()

    def _apply_filters(self):
        self._filter_options({'owner': self._search[False]})
        self._filter_options({'owner': self._search[True]})

    def _filter_options(self, event):
        """
        Filters unselected options based on a text query event.
        """
        selected = event['owner'] is self._search[True]
        query = self._query[selected] if 'new' not in event else event['new']
        self._query[selected] = query
        other = self._lists[not selected].options
        options = [o for o in self.options if o not in other]
        if not query:
            self._lists[selected].options = options
            self._lists[selected].value = []
        else:
            try:
                match = re.compile(query)
                matches = list(filter(match.search, options))
                options = matches + [opt for opt in options if opt not in matches]
            except:
                matches = options
            self._lists[selected].options = options if options else ['']
            self._lists[selected].value = matches

    def _update_selection(self, event):
        """
        Updates the current selection in each list.
        """
        selected = event['owner'] is self._lists[True]
        self._selected[selected] = [v for v in event['new'] if v != '']

    def _apply_selection(self, event):
        """
        Applies the current selection depending on which button was
        pressed.
        """
        selected = event is self._buttons[True]
        new = self._selected[not selected]
        old = self._lists[selected].options
        other = self._lists[not selected].options

        merged = sorted([v for v in list(old) + list(new) if v != ''])
        leftovers = sorted([o for o in other if o not in new and o != ''])
        new_values = merged if selected else leftovers
        self._lists[selected].options = merged if merged else ['']
        self._lists[not selected].options = leftovers if leftovers else ['']
        self.value = [self._options_dict[o] for o in self._lists[True].options if o != '']
        self._apply_filters()

    def _ipython_display_(self, **kwargs):
        """
        Displays the composite widget.
        """
        self._composite._ipython_display_(**kwargs)
    
    def get_state(self, key=None, drop_defaults=False):
        # HACK: Lets this composite widget pretend to be a regular widget
        # when included into a layout.
        if key in ['value', '_options_labels']:
            return super(CrossSelect, self).get_state(key)
        return self._composite.get_state(key)


HTMLVIEW_JS = """
define('activehtml', ["jupyter-js-widgets"], function(widgets) {
    var ActiveHTMLView = widgets.HTMLView.extend({
        update: function() {
            $(this.el).html(this.model.get('value'));
        }
    });
    return {
        ActiveHTMLView: ActiveHTMLView
    };
});
"""

class ActiveHTMLWidget(HTML):
    _view_name = Unicode('ActiveHTMLView').tag(sync=True)
    _view_module = Unicode('activehtml').tag(sync=True)
    value = Unicode('').tag(sync=True)


def apply_error_style(w, error):
    "Applies error styling to the supplied widget based on the error code"
    if error:
        color = '#FFCC00' if error == 'eval' else '#cc0000'
        w.layout.border = '5px solid %s' % color
    else:
        w.layout.border = '0px'


# Combine all widget JS code into on variable
WIDGET_JS = ''.join([HTMLVIEW_JS])

# Define parameters which should be evaluated using ast.literal_eval
literal_params = (param.Dict, param.List, param.Tuple)

# Maps from Parameter type to ipython widget types with any options desired
ptype2wtype = {
    param.Parameter:     TextWidget,
    param.Dict:          TextWidget,
    param.Selector:      ipywidgets.Dropdown,
    param.Boolean:       ipywidgets.Checkbox,
    param.Number:        FloatWidget,
    param.Integer:       IntegerWidget,
    param.ListSelector:  ListSelectorWidget,
    param.Action:        ActionButton,
    HTMLView:            ActiveHTMLWidget,
    ImageView:           Image
}

# Handle new parameters introduced in param 1.5
try:
    from param import Color, Range
    ptype2wtype.update({
        Color: ColorWidget,
        Range: RangeWidget
    })
except:
    pass

try:
    from param import Date
    ptype2wtype[Date] = TextWidget

    from ipywidgets import DatePicker
    ptype2wtype[Date] = DateWidget
except:
    pass


def wtype(pobj):
    if pobj.constant: # Ensure constant parameters cannot be edited
        return HTMLWidget
    for t in classlist(type(pobj))[::-1]:
        if t in ptype2wtype:
            return ptype2wtype[t]
