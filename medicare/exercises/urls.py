from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'exercises', views.ExerciseViewSet)
router.register(r'categories', views.ExerciseCategoryViewSet)
router.register(r'body-parts', views.BodyPartViewSet)
router.register(r'difficulty-levels', views.DifficultyLevelViewSet)
router.register(r'educational-materials', views.EducationalMaterialViewSet)

app_name = 'exercises'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Exercise management views
    path('', views.ExerciseLibraryView.as_view(), name='exercise_library'),
    path('create/', views.ExerciseCreateView.as_view(), name='exercise_create'),
    path('<int:pk>/', views.ExerciseDetailView.as_view(), name='exercise_detail'),
    path('<int:pk>/edit/', views.ExerciseUpdateView.as_view(), name='exercise_update'),
    path('<int:pk>/delete/', views.ExerciseDeleteView.as_view(), name='exercise_delete'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    
    # Educational materials
    path('materials/', views.EducationalMaterialListView.as_view(), name='material_list'),
    path('materials/create/', views.EducationalMaterialCreateView.as_view(), name='material_create'),
    
    # Search and filtering
    path('search/', views.ExerciseSearchView.as_view(), name='exercise_search'),
    path('filter/', views.ExerciseFilterView.as_view(), name='exercise_filter'),
]