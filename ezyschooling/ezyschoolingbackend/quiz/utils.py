import csv
from django.http import HttpResponse


def quiztaker_export_as_csv(self, request, queryset):

    meta = self.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}.csv'.format(
        meta)
    writer = csv.writer(response)

    output = []
    writer.writerow(['Username', 'User\'s Name', 'Email',
                     'Quiz Name', 'Board', 'Completed', 'Timestamp'])
    for obj in queryset:
        board = None
        if obj.quiz.board:
            board = obj.quiz.board.name
        output.append([obj.user.username, obj.user.name, obj.user.email,
                       obj.quiz.name, board, obj.completed, obj.timestamp])
    writer.writerows(output)
    return response
