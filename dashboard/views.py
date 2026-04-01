import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST


from .forms import (
    HomeworkCreateForm,
    HomeworkSubmissionForm,
    MessageForm,
    QuizCreateForm,
    QuizQuestionFormSet,
    TaskCreateForm,
)
from .models import Answer, Homework, HomeworkSubmission, Message, Question, Quiz, Task

def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    tasks = (
        Task.objects.filter(user=request.user)
        .prefetch_related('images')
        .order_by('-date', '-created_at')
    )
    latest_message = (
        Message.objects.filter(user=request.user).order_by('-created_at').first()
    )

    quiz = Quiz.objects.filter(user=request.user).prefetch_related('questions').first()
    homework = Homework.objects.filter(user=request.user).first()
    homework_submission = None
    if homework:
        homework_submission = HomeworkSubmission.objects.filter(
            user=request.user, homework=homework
        ).first()

    quiz_score = None
    quiz_submitted = False
    if quiz:
        question_ids = list(quiz.questions.values_list('id', flat=True))
        if question_ids:
            answers = Answer.objects.filter(
                user=request.user, question_id__in=question_ids
            ).select_related('question')
            quiz_submitted = answers.exists()
            if quiz_submitted:
                correct = sum(
                    1 for a in answers if a.selected_option == a.question.correct_answer
                )
                quiz_score = correct * 2  # 5 questions × 2 marks = 10

    completed_count = tasks.filter(is_completed=True).count()
    pending_count = tasks.filter(is_completed=False).count()

    return render(
        request,
        'dashboard/dashboard.html',
        {
            'tasks': tasks,
            'latest_message': latest_message,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'quiz': quiz,
            'quiz_submitted': quiz_submitted,
            'quiz_score': quiz_score,
            'homework': homework,
            'homework_submission': homework_submission,
        },
    )


@login_required
@require_POST
def toggle_task(request: HttpRequest, task_id: int) -> JsonResponse:
    task = get_object_or_404(Task, id=task_id, user=request.user)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}

    is_completed = payload.get('is_completed')
    if not isinstance(is_completed, bool):
        return JsonResponse({'ok': False, 'error': 'Invalid payload'}, status=400)

    task.is_completed = is_completed
    task.save(update_fields=['is_completed'])

    completed_count = Task.objects.filter(user=request.user, is_completed=True).count()
    pending_count = Task.objects.filter(user=request.user, is_completed=False).count()

    return JsonResponse(
        {
            'ok': True,
            'task_id': task.id,
            'is_completed': task.is_completed,
            'completed_count': completed_count,
            'pending_count': pending_count,
        }
    )


def _is_teacher(user) -> bool:
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_teacher)
def teacher_panel(request: HttpRequest) -> HttpResponse:
    task_form = TaskCreateForm(prefix='task')
    message_form = MessageForm(prefix='msg')
    quiz_form = QuizCreateForm(prefix='quiz')
    quiz_questions_formset = QuizQuestionFormSet(prefix='qq')
    homework_form = HomeworkCreateForm(prefix='hw')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_task':
            task_form = TaskCreateForm(request.POST, prefix='task')
            if task_form.is_valid():
                task_form.save()
                return redirect('teacher_panel')

        if action == 'set_message':
            message_form = MessageForm(request.POST, prefix='msg')
            if message_form.is_valid():
                Message.objects.create(
                    user=message_form.cleaned_data['user'],
                    text=message_form.cleaned_data['text'],
                )
                return redirect('teacher_panel')

        if action == 'create_quiz':
            quiz_form = QuizCreateForm(request.POST, prefix='quiz')
            if quiz_form.is_valid():
                # IMPORTANT: create quiz + 5 questions atomically.
                # If questions are invalid/incomplete, rollback so we don't create a "broken" quiz.
                with transaction.atomic():
                    quiz = quiz_form.save()
                    quiz_questions_formset = QuizQuestionFormSet(
                        request.POST, prefix='qq', instance=quiz
                    )
                    if not quiz_questions_formset.is_valid():
                        raise ValueError('Quiz must have 5 valid questions')
                    quiz_questions_formset.save()
                    return redirect('teacher_panel')
            else:
                quiz_questions_formset = QuizQuestionFormSet(request.POST, prefix='qq')

        if action == 'create_homework':
            homework_form = HomeworkCreateForm(request.POST, prefix='hw')
            if homework_form.is_valid():
                homework_form.save()
                return redirect('teacher_panel')

    recent_tasks = Task.objects.select_related('user').order_by('-created_at')[:10]
    recent_messages = Message.objects.select_related('user').order_by('-created_at')[:10]
    recent_quizzes = Quiz.objects.select_related('user').order_by('-created_at')[:10]
    recent_homeworks = Homework.objects.select_related('user').order_by('-created_at')[
        :10
    ]
    recent_homework_submissions = (
        HomeworkSubmission.objects.select_related('user', 'homework')
        .order_by('-submitted_at')[:10]
    )

    # Recent quiz results (teacher-only): compute score and include selected/correct options.
    recent_answers = (
        Answer.objects.select_related('user', 'question', 'question__quiz')
        .order_by('-created_at')[:200]
    )
    quiz_result_map: dict[tuple[int, int], dict] = {}
    for ans in recent_answers:
        key = (ans.user_id, ans.question.quiz_id)
        if key not in quiz_result_map:
            quiz_result_map[key] = {
                'user': ans.user,
                'quiz': ans.question.quiz,
                'total_questions': 0,
                'correct': 0,
                'answers': [],
            }
        entry = quiz_result_map[key]
        entry['total_questions'] += 1
        if ans.selected_option == ans.question.correct_answer:
            entry['correct'] += 1
        entry['answers'].append(
            {
                'question_text': ans.question.text,
                'selected_option': ans.selected_option,
                'correct_answer': ans.question.correct_answer,
            }
        )

    recent_quiz_results = []
    for entry in quiz_result_map.values():
        # Score out of 10, each question = 2 marks (expected 5 questions).
        score = entry['correct'] * 2
        recent_quiz_results.append({**entry, 'score': score})

    recent_quiz_results.sort(key=lambda x: x['quiz'].created_at, reverse=True)
    recent_quiz_results = recent_quiz_results[:10]

    return render(
        request,
        'dashboard/teacher_panel.html',
        {
            'task_form': task_form,
            'message_form': message_form,
            'quiz_form': quiz_form,
            'quiz_questions_formset': quiz_questions_formset,
            'homework_form': homework_form,
            'recent_tasks': recent_tasks,
            'recent_messages': recent_messages,
            'recent_quizzes': recent_quizzes,
            'recent_homeworks': recent_homeworks,
            'recent_homework_submissions': recent_homework_submissions,
            'recent_quiz_results': recent_quiz_results,
        },
    )


@login_required
def quiz_page(request: HttpRequest) -> HttpResponse:
    quiz = Quiz.objects.filter(user=request.user).prefetch_related('questions').first()
    if not quiz:
        return render(request, 'dashboard/quiz.html', {'quiz': None})

    questions = list(quiz.questions.all())
    incomplete = len(questions) != 5
    question_ids = [q.id for q in questions]

    answers = (
        Answer.objects.filter(user=request.user, question_id__in=question_ids)
        .select_related('question')
        .all()
    )
    submitted = bool(answers)

    score = None
    if submitted:
        correct = sum(1 for a in answers if a.selected_option == a.question.correct_answer)
        score = correct * 2

    existing_map = {a.question_id: a.selected_option for a in answers}

    return render(
        request,
        'dashboard/quiz.html',
        {
            'quiz': quiz,
            'questions': questions,
            'submitted': submitted,
            'score': score,
            'existing_map': existing_map,
            'incomplete': incomplete,
        },
    )


@login_required
@require_POST
def quiz_submit(request: HttpRequest) -> HttpResponse:
    quiz = Quiz.objects.filter(user=request.user).prefetch_related('questions').first()
    if not quiz:
        return redirect('quiz_page')

    questions = list(quiz.questions.all())
    if len(questions) != 5:
        # Teacher must create exactly 5 questions.
        return redirect('quiz_page')

    question_ids = [q.id for q in questions]
    already = Answer.objects.filter(user=request.user, question_id__in=question_ids).exists()
    if already:
        # Optional bonus: prevent editing after submission.
        return redirect('quiz_page')

    selected = {}
    for q in questions:
        val = request.POST.get(f'q_{q.id}')
        if val not in {Question.ANSWER_A, Question.ANSWER_B, Question.ANSWER_C, Question.ANSWER_D}:
            return redirect('quiz_page')
        selected[q.id] = val

    with transaction.atomic():
        Answer.objects.bulk_create(
            [
                Answer(user=request.user, question_id=q_id, selected_option=opt)
                for q_id, opt in selected.items()
            ]
        )

    return redirect('quiz_page')


@login_required
def homework_page(request: HttpRequest) -> HttpResponse:
    homework = Homework.objects.filter(user=request.user).first()
    if not homework:
        return render(request, 'dashboard/homework.html', {'homework': None})

    submission = HomeworkSubmission.objects.filter(
        user=request.user, homework=homework
    ).first()

    if request.method == 'POST':
        if submission:
            return redirect('homework_page')
        form = HomeworkSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            new_sub = form.save(commit=False)
            new_sub.user = request.user
            new_sub.homework = homework
            new_sub.save()
            return redirect('homework_page')
    else:
        form = HomeworkSubmissionForm()

    # 🔥 ADD THIS PART (safe)
    images = []
    if submission:
        images = [
            submission.image1,
            submission.image2,
            submission.image3,
            submission.image4,
            submission.image5,
        ]

    return render(
        request,
        'dashboard/homework.html',
        {
            'homework': homework,
            'submission': submission,
            'form': form,
            'images': images,  # 👈 ADD THIS
        },
    )

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')

