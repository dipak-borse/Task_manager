from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


class Task(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks'
    )
    text = models.TextField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self) -> str:
        return f'{self.user.username}: {self.text[:40]}'


def _task_image_upload_to(instance: 'TaskImage', filename: str) -> str:
    # Keep filenames unique to avoid accidental overwrites.
    rand = get_random_string(12)
    return f'task-images/task-{instance.task_id}/{rand}-{filename}'


class TaskImage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=_task_image_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'TaskImage(task_id={self.task_id})'


class Message(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.username}: {self.text[:40]}'


class Quiz(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quizzes'
    )
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.username}: {self.title}'


class Question(models.Model):
    ANSWER_A = 'A'
    ANSWER_B = 'B'
    ANSWER_C = 'C'
    ANSWER_D = 'D'
    ANSWER_CHOICES = [
        (ANSWER_A, 'A'),
        (ANSWER_B, 'B'),
        (ANSWER_C, 'C'),
        (ANSWER_D, 'D'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)

    def __str__(self) -> str:
        return f'Question(quiz_id={self.quiz_id})'


class Answer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_answers'
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers'
    )
    selected_option = models.CharField(max_length=1, choices=Question.ANSWER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'], name='unique_answer_per_user_question'
            )
        ]

    def __str__(self) -> str:
        return f'Answer(user={self.user_id}, question={self.question_id})'


class Homework(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='homeworks'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Homework(user={self.user_id})'


def _homework_upload_to(instance: 'HomeworkSubmission', filename: str) -> str:
    rand = get_random_string(12)
    return f'homework-submissions/user-{instance.user_id}/hw-{instance.homework_id}/{rand}-{filename}'


class HomeworkSubmission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='homework_submissions',
    )
    homework = models.ForeignKey(
        Homework, on_delete=models.CASCADE, related_name='submissions'
    )
    image1 = models.ImageField(upload_to=_homework_upload_to, blank=True, null=True)
    image2 = models.ImageField(upload_to=_homework_upload_to, blank=True, null=True)
    image3 = models.ImageField(upload_to=_homework_upload_to, blank=True, null=True)
    image4 = models.ImageField(upload_to=_homework_upload_to, blank=True, null=True)
    image5 = models.ImageField(upload_to=_homework_upload_to, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'homework'],
                name='unique_homework_submission_per_user_homework',
            )
        ]

    def __str__(self) -> str:
        return f'HomeworkSubmission(user={self.user_id}, homework={self.homework_id})'
