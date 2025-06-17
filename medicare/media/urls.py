from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'files', views.MediaFileViewSet)

app_name = 'media'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Media file management
    path('', views.MediaLibraryView.as_view(), name='media_library'),
    path('upload/', views.FileUploadView.as_view(), name='upload_file'),
    path('upload/multiple/', views.MultipleFileUploadView.as_view(), name='upload_multiple'),
    path('<int:pk>/', views.MediaFileDetailView.as_view(), name='file_detail'),
    path('<int:pk>/edit/', views.MediaFileUpdateView.as_view(), name='file_edit'),
    path('<int:pk>/delete/', views.MediaFileDeleteView.as_view(), name='file_delete'),
    
    # Video processing
    path('video/<int:pk>/process/', views.ProcessVideoView.as_view(), name='process_video'),
    path('video/<int:pk>/status/', views.VideoProcessingStatusView.as_view(), name='video_status'),
    path('video/<int:pk>/thumbnail/', views.GenerateThumbnailView.as_view(), name='generate_thumbnail'),
    
    # File serving
    path('serve/<int:pk>/', views.ServeMediaFileView.as_view(), name='serve_file'),
    path('download/<int:pk>/', views.DownloadMediaFileView.as_view(), name='download_file'),
    path('stream/<int:pk>/', views.StreamVideoView.as_view(), name='stream_video'),
    
    # File organization
    path('search/', views.MediaSearchView.as_view(), name='search_media'),
    path('filter/', views.MediaFilterView.as_view(), name='filter_media'),
    path('bulk-action/', views.BulkMediaActionView.as_view(), name='bulk_action'),
    
    # Storage management
    path('storage/usage/', views.StorageUsageView.as_view(), name='storage_usage'),
    path('storage/cleanup/', views.CleanupStorageView.as_view(), name='cleanup_storage'),
]