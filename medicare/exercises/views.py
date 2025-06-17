from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Q
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    BodyPart, ExerciseCategory, DifficultyLevel, Exercise,
    ExerciseImage, ExerciseStep, EducationalMaterial
)
from .forms import ExerciseForm, ExerciseStepForm
from .serializers import (
    BodyPartSerializer, ExerciseCategorySerializer, DifficultyLevelSerializer,
    ExerciseSerializer, ExerciseImageSerializer, EducationalMaterialSerializer
)
from staff.permissions import IsAdminOrDoctor


class ExerciseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows exercises to be viewed or edited.
    Filtering by body_part, category, and difficulty is supported.
    """
    queryset = Exercise.objects.filter(is_public=True).prefetch_related('body_parts', 'categories', 'images')
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'body_parts__name': ['exact'],
        'categories__name': ['exact'],
        'difficulty__name': ['exact'],
    }
    search_fields = ['title', 'description', 'instructions']
    ordering_fields = ['title', 'created_at', 'difficulty__value']

    def get_queryset(self):
        # Allow doctors/admins to see non-public exercises
        user = self.request.user
        if user.is_authenticated and (user.user_type in ['admin', 'doctor']):
            return Exercise.objects.all().prefetch_related('body_parts', 'categories', 'images')
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Reading is available for any authenticated user.
        Creation/modification/deletion is only available for Admins or Doctors.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminOrDoctor]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super(ExerciseViewSet, self).get_permissions()


class BodyPartViewSet(viewsets.ModelViewSet):
    queryset = BodyPart.objects.all()
    serializer_class = BodyPartSerializer
    permission_classes = [IsAdminOrDoctor]


class ExerciseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExerciseCategory.objects.all()
    serializer_class = ExerciseCategorySerializer
    permission_classes = [IsAdminOrDoctor]


class DifficultyLevelViewSet(viewsets.ModelViewSet):
    queryset = DifficultyLevel.objects.all()
    serializer_class = DifficultyLevelSerializer
    permission_classes = [IsAdminOrDoctor]


class EducationalMaterialViewSet(viewsets.ModelViewSet):
    queryset = EducationalMaterial.objects.all()
    serializer_class = EducationalMaterialSerializer
    permission_classes = [IsAdminOrDoctor]


# Web Views (Class-Based Views for exercise management)
class ExerciseLibraryView(LoginRequiredMixin, ListView):
    model = Exercise
    template_name = 'exercises/exercise_library.html'
    context_object_name = 'exercises'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Exercise.objects.filter(is_public=True).prefetch_related('body_parts', 'categories', 'images')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(instructions__icontains=search)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(categories__id=category)
            
        # Filter by body part
        body_part = self.request.GET.get('body_part')
        if body_part:
            queryset = queryset.filter(body_parts__id=body_part)
            
        # Filter by difficulty
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty__id=difficulty)
            
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ExerciseCategory.objects.all()
        context['body_parts'] = BodyPart.objects.all()
        context['difficulty_levels'] = DifficultyLevel.objects.all()
        return context


class ExerciseDetailView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = 'exercises/exercise_detail.html'
    context_object_name = 'exercise'


class ExerciseCreateView(LoginRequiredMixin, CreateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'exercises/exercise_form.html'
    success_url = reverse_lazy('exercises:exercise_library')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Handle exercise steps
        self._save_exercise_steps()
        
        return response
    
    def _save_exercise_steps(self):
        """Save exercise steps from form data"""
        steps_data = []
        i = 0
        while f'step_{i}_instruction' in self.request.POST:
            instruction = self.request.POST.get(f'step_{i}_instruction', '').strip()
            if instruction:
                step_data = {
                    'step_number': i + 1,
                    'instruction': instruction,
                    'image': self.request.FILES.get(f'step_{i}_image')
                }
                steps_data.append(step_data)
            i += 1
        
        # Create exercise steps
        for step_data in steps_data:
            ExerciseStep.objects.create(
                exercise=self.object,
                step_number=step_data['step_number'],
                instruction=step_data['instruction'],
                image=step_data['image']
            )


class ExerciseUpdateView(LoginRequiredMixin, UpdateView):
    model = Exercise
    form_class = ExerciseForm
    template_name = 'exercises/exercise_form.html'
    success_url = reverse_lazy('exercises:exercise_library')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['existing_steps'] = self.object.steps.all().order_by('step_number')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Delete existing steps and create new ones
        self.object.steps.all().delete()
        self._save_exercise_steps()
        
        return response
    
    def _save_exercise_steps(self):
        """Save exercise steps from form data"""
        steps_data = []
        i = 0
        while f'step_{i}_instruction' in self.request.POST:
            instruction = self.request.POST.get(f'step_{i}_instruction', '').strip()
            if instruction:
                step_data = {
                    'step_number': i + 1,
                    'instruction': instruction,
                    'image': self.request.FILES.get(f'step_{i}_image')
                }
                steps_data.append(step_data)
            i += 1
        
        # Create exercise steps
        for step_data in steps_data:
            ExerciseStep.objects.create(
                exercise=self.object,
                step_number=step_data['step_number'],
                instruction=step_data['instruction'],
                image=step_data['image']
            )


class ExerciseDeleteView(LoginRequiredMixin, DeleteView):
    model = Exercise
    template_name = 'exercises/exercise_confirm_delete.html'
    success_url = reverse_lazy('exercises:exercise_library')


class CategoryListView(LoginRequiredMixin, ListView):
    model = ExerciseCategory
    template_name = 'exercises/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = ExerciseCategory
    template_name = 'exercises/category_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('exercises:category_list')


class EducationalMaterialListView(LoginRequiredMixin, ListView):
    model = EducationalMaterial
    template_name = 'exercises/material_list.html'
    context_object_name = 'materials'


class EducationalMaterialCreateView(LoginRequiredMixin, CreateView):
    model = EducationalMaterial
    template_name = 'exercises/material_form.html'
    fields = ['title', 'description', 'file', 'content_type']
    success_url = reverse_lazy('exercises:material_list')


class ExerciseSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'exercises/exercise_search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('q', '')
        
        if search_query:
            exercises = Exercise.objects.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(instructions__icontains=search_query),
                is_public=True
            ).prefetch_related('body_parts', 'categories', 'images')
        else:
            exercises = Exercise.objects.none()
            
        context['exercises'] = exercises
        context['search_query'] = search_query
        return context


class ExerciseFilterView(LoginRequiredMixin, TemplateView):
    template_name = 'exercises/exercise_filter.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ExerciseCategory.objects.all()
        context['body_parts'] = BodyPart.objects.all()
        context['difficulty_levels'] = DifficultyLevel.objects.all()
        return context
