from django import forms
from .models import Course, Question

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_name', 'total_marks', 'time_limit']
        widgets = {
            'course_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Advanced Python Programming',
                'autocomplete': 'off'
            }),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 100',
                'min': '1'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 30',
                'min': '1'
            }),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
        widgets = {
            'question_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your question here...',
                'autocomplete': 'off'
            }),
            'option1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choice A',
                'autocomplete': 'off'
            }),
            'option2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choice B',
                'autocomplete': 'off'
            }),
            'option3': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choice C',
                'autocomplete': 'off'
            }),
            'option4': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choice D',
                'autocomplete': 'off'
            }),
            'correct_answer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Must exactly match Choice A, B, C, or D',
                'autocomplete': 'off'
            }),
        }
