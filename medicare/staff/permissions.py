from rest_framework import permissions


class IsAdminOrSelf(permissions.BasePermission):
    """
    Дозволяє доступ тільки адміністраторам або користувачу об'єкта.
    """
    
    def has_object_permission(self, request, view, obj):
        # Адміністраторам дозволено все
        if request.user.is_staff or request.user.user_type == 'admin':
            return True
            
        # Дозволено доступ до свого власного об'єкта
        return obj == request.user


class IsAdminOrOwner(permissions.BasePermission):
    """
    Дозволяє доступ тільки адміністраторам або власнику профілю.
    """
    
    def has_object_permission(self, request, view, obj):
        # Адміністраторам дозволено все
        if request.user.is_staff or request.user.user_type == 'admin':
            return True
            
        # Перевіряємо, чи є об'єкт StaffProfile
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # Для WorkSchedule або Certificate
        if hasattr(obj, 'staff'):
            return obj.staff.user == request.user
            
        return False


class IsAdminOrDoctor(permissions.BasePermission):
    """
    Allows access only to admin or doctor users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               (request.user.user_type == 'admin' or request.user.user_type == 'doctor')


class IsDoctor(permissions.BasePermission):
    """
    Allows access only to users with the 'doctor' user type.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'doctor'