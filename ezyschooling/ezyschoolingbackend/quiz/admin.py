import nested_admin
from django.contrib import admin

from .forms import PersonalityAdminForm
from .models import *
from .utils import quiztaker_export_as_csv

from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

class AnswerInline(nested_admin.NestedTabularInline):
    model = Answer
    autocomplete_fields = ["personality"]
    extra = 4
    max_num = 6


class QuestionInline(nested_admin.NestedTabularInline):
    model = Question
    inlines = [AnswerInline, ]
    extra = 19


class QuizAdmin(nested_admin.NestedModelAdmin):
    change_list_template = "quiz/admin_changelist.html"
    inlines = [QuestionInline, ]
    save_on_top = True
    list_display = ["name", "category", "board", "roll_out"]
    list_filter = ["category", "board", "roll_out", "created"]
    ordering = ["-created"]
    search_fields = ["name"]
    raw_id_fields = ["category", "board"]
    prepopulated_fields = {"slug": ("name", )}


@admin.register(QuizCategory)
class QuizCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "is_featured"]
    list_filter = ["is_featured"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name", )}


@admin.register(QuizCategoryPlace)
class QuizCategoryPlaceAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name", )}


class ResponseInline(admin.TabularInline):
    model = Response
    raw_id_fields = ["question", "answer"]
    extra = 0


quiztaker_export_as_csv.short_description = 'Export Selected User Data'


class QuizTakersAdmin(admin.ModelAdmin):
    inlines = [ResponseInline, ]
    list_display = ["user", "quiz",
                    "correct_answers", "completed", "timestamp"]
    raw_id_fields = ["user", "quiz"]
    actions = [quiztaker_export_as_csv]
    list_filter = ["quiz", "completed", ('timestamp', DateTimeRangeFilter)]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "quiz")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["text", "question", "is_correct"]
    raw_id_fields = ["question"]
    search_fields = ["text", "question__label"]
    list_per_page = 50
    list_filter = ["is_correct", ('timestamp', DateTimeRangeFilter)]

    def get_model_perms(self, request):
        return {}


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["label", "quiz", "order"]
    raw_id_fields = ["quiz"]
    search_fields = ["label"]
    list_per_page = 50
    list_filter = ["quiz", ('timestamp', DateTimeRangeFilter)]

    def get_model_perms(self, request):
        return {}


@admin.register(Personality)
class PersonalityAdmin(admin.ModelAdmin):
    form = PersonalityAdminForm
    list_display = ["name", "points", "result_start", "result_end"]
    search_fields = ["name"]


admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizTakers, QuizTakersAdmin)
