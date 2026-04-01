from django.contrib import admin

from .models import (
    Answer,
    Homework,
    HomeworkSubmission,
    Message,
    Question,
    Quiz,
    Task,
    TaskImage,
)


class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 2


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date', 'is_completed', 'created_at', 'text')
    list_filter = ('date', 'is_completed')
    search_fields = ('user__username', 'text')
    autocomplete_fields = ('user',)
    inlines = [TaskImageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'text')
    search_fields = ('user__username', 'text')
    autocomplete_fields = ('user',)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 5
    max_num = 5


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'created_at')
    search_fields = ('title', 'user__username')
    autocomplete_fields = ('user',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'quiz', 'correct_answer', 'text')
    search_fields = ('quiz__title', 'quiz__user__username', 'text')
    autocomplete_fields = ('quiz',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'selected_option', 'created_at')
    search_fields = ('user__username', 'question__quiz__title', 'question__text')
    autocomplete_fields = ('user', 'question')
    list_filter = ('selected_option',)


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'text')
    search_fields = ('user__username', 'text')
    autocomplete_fields = ('user',)


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'homework', 'submitted_at')
    search_fields = ('user__username', 'homework__text')
    autocomplete_fields = ('user', 'homework')
