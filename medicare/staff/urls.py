from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'staff-profiles', views.StaffProfileViewSet)
router.register(r'certificates', views.CertificateViewSet)
router.register(r'work-schedules', views.WorkScheduleViewSet)
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')

app_name = 'staff'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Authentication
    path('api/token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/register/', views.RegisterView.as_view(), name='register'),
    
    # Staff management views
    path('', views.StaffDashboardView.as_view(), name='staff_home'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    
    # Staff profiles
    path('profiles/', views.StaffProfileListView.as_view(), name='staff_profile_list'),
    path('profiles/<int:pk>/', views.StaffProfileDetailView.as_view(), name='staff_profile_detail'),
    path('profiles/<int:pk>/edit/', views.StaffProfileUpdateView.as_view(), name='staff_profile_edit'),
    path('profiles/create/', views.StaffProfileCreateView.as_view(), name='staff_profile_create'),
    
    # Work schedules
    path('schedule/', views.WorkScheduleListView.as_view(), name='work_schedule'),
    path('schedule/create/', views.WorkScheduleCreateView.as_view(), name='work_schedule_create'),
    path('schedule/<int:pk>/edit/', views.WorkScheduleUpdateView.as_view(), name='work_schedule_edit'),
    
    # Certificates
    path('certificates/', views.CertificateListView.as_view(), name='certificate_list'),
    path('certificates/add/', views.CertificateCreateView.as_view(), name='certificate_add'),
    path('certificates/<int:pk>/', views.CertificateDetailView.as_view(), name='certificate_detail'),
    
    # Profile management
    path('profile/', views.MyProfileView.as_view(), name='my_profile'),
    path('profile/edit/', views.MyProfileUpdateView.as_view(), name='my_profile_edit'),
    
    # Appointments
    path('appointments/', views.AppointmentListView.as_view(), name='appointment_list'),
]