from django import forms
from django.contrib.auth import get_user_model

from django.forms import inlineformset_factory

from .models import Homework, HomeworkSubmission, Message, Question, Quiz, Task

User = get_user_model()


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['user', 'date', 'text']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'text': forms.Textarea(attrs={'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['user', 'text']
        widgets = {'text': forms.Textarea(attrs={'rows': 4})}


class QuizCreateForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['user', 'title']
        widgets = {'title': forms.TextInput(attrs={'placeholder': 'Daily Quiz'})}


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'text',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_answer',
        ]
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }


QuizQuestionFormSet = inlineformset_factory(
    Quiz,
    Question,
    form=QuestionForm,
    extra=5,
    min_num=5,
    validate_min=True,
    max_num=5,
    validate_max=True,
    can_delete=False,
)


class HomeworkCreateForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['user', 'text']
        widgets = {'text': forms.Textarea(attrs={'rows': 5})}


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['image1', 'image2', 'image3', 'image4', 'image5']
