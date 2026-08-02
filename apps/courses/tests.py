from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Tblcourse, Quiz, QuizQuestion


class QuizQuestionSaveTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.course = Tblcourse.objects.create(name='Test Course', section='A', schoolyr='2024-2025')
        self.quiz = Quiz.objects.create(course=self.course, title='Sample Quiz')

    def test_identification_question_saves_text_answer(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('courses:question_save', args=[self.quiz.id]),
            {
                'question_text': 'What is the capital of France?',
                'question_type': 'identification',
                'identification_answer': 'Paris',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        question = QuizQuestion.objects.latest('id')
        self.assertEqual(question.question_type, 'identification')
        self.assertEqual(question.correct_option, 'Paris')
        self.assertEqual(question.option_a, '')

    def test_true_false_question_uses_boolean_style_answer(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse('courses:question_save', args=[self.quiz.id]),
            {
                'question_text': 'The Earth is round.',
                'question_type': 'true_false',
                'correct_option': 'False',
            },
            follow=True,
        )
        question = QuizQuestion.objects.latest('id')
        self.assertEqual(question.question_type, 'true_false')
        self.assertEqual(question.correct_option, 'False')
        self.assertEqual(question.option_a, 'True')
        self.assertEqual(question.option_b, 'False')
