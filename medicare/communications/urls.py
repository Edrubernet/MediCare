from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'chat-rooms', views.ChatRoomViewSet)
router.register(r'chat-messages', views.ChatMessageViewSet)

app_name = 'communications'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Chat management views
    path('', views.ChatDashboardView.as_view(), name='chat_dashboard'),
    path('rooms/', views.ChatRoomListView.as_view(), name='chat_room_list'),
    path('rooms/create/', views.ChatRoomCreateView.as_view(), name='chat_room_create'),
    path('rooms/<int:pk>/', views.ChatRoomDetailView.as_view(), name='chat_room_detail'),
    
    # WebSocket chat interface
    path('chat/<int:room_id>/', views.ChatInterfaceView.as_view(), name='chat_interface'),
    path('chat/<int:room_id>/history/', views.ChatHistoryView.as_view(), name='chat_history'),
    
    # Message management
    path('messages/search/', views.MessageSearchView.as_view(), name='message_search'),
    path('messages/export/', views.ExportChatHistoryView.as_view(), name='export_chat'),
] 