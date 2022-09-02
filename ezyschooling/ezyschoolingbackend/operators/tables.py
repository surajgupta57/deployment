import django_tables2 as tables
from schools.models import SchoolProfile
from admission_forms.models import SchoolApplication


class AssignedSchoolsTable(tables.Table):
    view_applications = tables.LinkColumn(
        text = "view",
        viewname="operators:applications",
        args=[tables.A("pk")])
    name = tables.Column(
        linkify=(
            "operators:school_dashboard", [
                tables.A("pk")]))

    class Meta:
        model = SchoolProfile
        empty_text = "No data available in table"
        order_by = "name"
        fields = [
            "name",
            "region",
        ]

class SchoolApplicationTable(tables.Table):
    status = tables.LinkColumn(empty_values=(),
        verbose_name='Status',
        viewname="operators:status_edit",
        args=[
            tables.A("pk")])

    view_form = tables.LinkColumn(
        exclude_from_export=True,
        text="View Form",
        viewname="operators:common_form",
        args=[
            tables.A("form__pk")])
    edit_applications = tables.LinkColumn(
        exclude_from_export=True,
        text="points",
        viewname="operators:school_application_edit_form",
        args=[
            tables.A("pk")])

    def render_status(self, record):
        if record.status.exists():
            return record.status.latest('timestamp').status.name


    class Meta:
        model = SchoolApplication
        empty_text = "No data available in table"
        order_by = "-timestamp"
        fields = [
            "child",
            "school",
            "user",
            "edit_applications",
            "status",
            "apply_for",
            "timestamp",
            "view_form"
        ]

    def render_user(self, record):
        return str(record.user.name)

    def render_school(self, record):
        return str(record.school.name.title())
    
    def render_timestamp(self, record):
        return str(record.timestamp.strftime("%d/%m/%Y"))