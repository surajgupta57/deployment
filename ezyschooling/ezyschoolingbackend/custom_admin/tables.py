import django_tables2 as tables
from django.db.models import Count

from admission_forms.models import ChildSchoolCart, SchoolApplication
from parents.models import ParentProfile
from schools.models import SchoolEnquiry, SchoolView


class ParentTable(tables.Table):
    class Meta:
        model = ParentProfile
        empty_text = "No data available in table"
        order_by = "-user__date_joined"
        fields = [
            "name",
            "phone",
            "email",
            "child_count",
            "user__date_joined"
        ]

    def render_name(self, record):
        return str(record.name.title())


class SchoolViewTable(tables.Table):
    parent = tables.Column(empty_values=())
    school = tables.Column(
        linkify=(
            "custom_admin:school_details", [
                tables.A("school__pk")]))

    class Meta:
        model = SchoolView
        empty_text = "No data available in table"
        order_by = "-updated_at"
        fields = [
            "parent",
            "school",
            "count",
            "updated_at"
        ]

    def render_parent(self, record):
        return str(record.user.name)

    def render_school(self, record):
        return str(record.school.name.title())


class ChildSchoolCartTable(tables.Table):
    parent = tables.Column(empty_values=())
    school = tables.Column(
        linkify=(
            "custom_admin:school_details", [
                tables.A("school__pk")]))

    class Meta:
        model = ChildSchoolCart
        empty_text = "No data available in table"
        order_by = "-timestamp"
        fields = [
            "child",
            "parent",
            "school",
            "child__class_applying_for",
            "timestamp"
        ]

    def render_parent(self, record):
        return str(record.form.user.name)

    def render_school(self, record):
        return str(record.school.name.title())


class SchoolApplicationTable(tables.Table):
    view_form = tables.LinkColumn(
        exclude_from_export=True,
        text="View Form",
        viewname="custom_admin:form_details",
        args=[
            tables.A("form__pk")])
    school = tables.Column(
        linkify=(
            "custom_admin:school_details", [
                tables.A("school__pk")]))

    class Meta:
        model = SchoolApplication
        empty_text = "No data available in table"
        order_by = "-timestamp"
        fields = [
            "user",
            "child",
            "school",
            "school__region",
            "apply_for",
            "timestamp",
            "view_form"
        ]

    def render_user(self, record):
        return str(record.user.name)

    def render_school(self, record):
        return str(record.school.name.title())


class SchoolEnquiryTable(tables.Table):
    school = tables.Column(
        linkify=(
            "custom_admin:school_details", [
                tables.A("school__pk")]))
    parent = tables.Column(empty_values=(), verbose_name="Parent")
    parent_email = tables.Column(empty_values=(), verbose_name="Email")
    parent_phone = tables.Column(empty_values=(), verbose_name="Phone")

    class Meta:
        model = SchoolEnquiry
        empty_text = "No data available in table"
        order_by = "-timestamp"
        fields = [
            "parent",
            "school",
            "parent_email",
            "parent_phone",
            "query",
            "timestamp",
        ]

    def render_parent(self, record):
        if record.user:
            return str(record.user.name)
        else:
            return str(record.parent_name)

    def render_parent_phone(self, record):
        if record.user:
            parent = ParentProfile.objects.get(id=record.user.current_parent)
            return str(parent.phone)
        else:
            return str(record.phone_no)

    def render_parent_email(self, record):
        if record.user:
            return str(record.user.email)
        else:
            return str(record.email)
