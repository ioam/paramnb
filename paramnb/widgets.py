import re

import param
from ipywidgets import SelectMultiple, Button, HBox, VBox, Layout, Text

from .util import named_objs


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
                matches = filter(match.search, options)
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

