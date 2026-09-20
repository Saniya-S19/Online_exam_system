from django import forms
from .models import Course, Question

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_name', 'total_marks']
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Basics'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control'}),
            'option1': forms.TextInput(attrs={'class': 'form-control'}),
            'option2': forms.TextInput(attrs={'class': 'form-control'}),
            'option3': forms.TextInput(attrs={'class': 'form-control'}),
            'option4': forms.TextInput(attrs={'class': 'form-control'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Must exactly match one of the options above'}),
        }