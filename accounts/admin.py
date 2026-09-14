from django.contrib import admin
from .models import Course, Question, Result

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'total_marks')
    search_fields = ('course_name',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'course', 'correct_answer')
    list_filter = ('course',)
    search_fields = ('question_text',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'marks_scored', 'date_taken')
    list_filter = ('exam', 'date_taken')
    search_fields = ('student__username', 'exam__course_name')