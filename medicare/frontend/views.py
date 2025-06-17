from django.shortcuts import render

# NOTE: @login_required is removed because auth is now handled by
# the JWT token and the logic in static/frontend/js/auth.js

def index(request):
    """Головна сторінка"""
    return render(request, 'frontend/index.html')

def login_view(request):
    """Сторінка входу - тепер рендерить тільки шаблон."""
    return render(request, 'frontend/login.html')

def logout_view(request):
    """Вихід з системи. Рендерить шаблон, JS очистить localStorage."""
    return render(request, 'frontend/logout.html')

def register(request):
    """Сторінка реєстрації"""
    return render(request, 'frontend/register.html')

def dashboard(request):
    """
    This view now acts as a loader.
    It renders a template with JS that fetches the user's role
    and redirects to the correct dashboard.
    """
    return render(request, 'frontend/dashboard.html')

# --- Role-specific dashboard views ---

def patient_dashboard_view(request):
    """Renders the patient's dashboard."""
    context = {}
    
    # Додаємо лічильники для завдань і повідомлень
    if hasattr(request, 'user') and request.user.is_authenticated:
        context.update(get_patient_dashboard_counts(request.user))
    
    return render(request, 'frontend/patient_dashboard.html', context)

def get_patient_dashboard_counts(user):
    """Отримати кількість завдань і повідомлень для пацієнта"""
    from survey.models import SurveyAssignment
    from communications.models import Conversation, Message
    from datetime import date
    
    counts = {
        'task_count': 0,
        'message_count': 0
    }
    
    try:
        if user.user_type == 'patient':
            # Підраховуємо незавершені завдання (опитування)
            pending_surveys = SurveyAssignment.objects.filter(
                patient__user=user,
                status='pending',
                due_date__gte=date.today()
            ).count()
            
            # Підраховуємо непрочитані повідомлення
            unread_messages = Message.objects.filter(
                conversation__participants=user,
                is_read=False
            ).exclude(sender=user).count()
            
            counts.update({
                'task_count': pending_surveys,
                'message_count': unread_messages
            })
    except Exception:
        # У разі помилки повертаємо нулі
        pass
    
    return counts

def doctor_dashboard_view(request):
    """Renders the doctor's dashboard."""
    return render(request, 'frontend/doctor_dashboard.html')
    
def admin_dashboard_view(request):
    """Renders the admin's dashboard."""
    return render(request, 'frontend/admin_dashboard.html')

# --- Other views ---

def profile(request):
    """Профіль користувача"""
    # This might need similar role-based logic on the frontend
    return render(request, 'frontend/profile.html')

def patient_list(request):
    """Список пацієнтів (для лікарів)"""
    return render(request, 'frontend/patient_list.html')

def patient_detail(request, patient_id):
    """Деталі пацієнта (для лікарів)"""
    return render(request, 'frontend/patient_detail.html', {'patient_id': patient_id})

def schedule(request):
    """Розклад роботи (для лікарів)"""
    return render(request, 'frontend/schedule.html')

def my_programs(request):
    """Програми реабілітації пацієнта"""
    return render(request, 'frontend/my_programs.html')

def program_detail(request, program_id):
    """Деталі програми реабілітації"""
    return render(request, 'frontend/program_detail.html', {'program_id': program_id})

def my_doctors(request):
    """Лікарі пацієнта"""
    return render(request, 'frontend/my_doctors.html')