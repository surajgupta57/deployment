from django.forms.widgets import MultiWidget
from django.utils.safestring import mark_safe
from bootstrap_datepicker_plus import DatePickerInput


class DateRangeInput(MultiWidget):
    """
    Render a filter with start date and end date using bootstrap and jquery.
    """

    def __init__(self, till_today=True, attrs=None):
        """
        The *till_today* flag configures what happens when the second date
        is blank. If true, the application receives today's date; if false,
        a ValidationError is raised. True is the default.
        """
        self.till_today = till_today
        opt = {
            "showClose": False,
            "format": "YYYY-MM-DD",
        }
        widget = (
            DatePickerInput(
                attrs={
                    "placeholder": "Start Date"}, options=opt), DatePickerInput(
                options=opt, attrs={
                    "placeholder": "End Date"}),)
        super().__init__(widget, attrs=attrs)

    def decompress(self, value):
        """
        Called when rendering the widget.
        """
        return value or (None, None)

    def format_output(self, rendered_widgets):
        return mark_safe('<br><br><br>'.join(rendered_widgets))
