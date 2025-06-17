from django.contrib import admin
from .models import Report, ReportExport


class ReportExportInline(admin.TabularInline):
    model = ReportExport
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'created_by', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'description', 'created_by__first_name', 'created_by__last_name')
    inlines = [ReportExportInline]
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ('report', 'format', 'file', 'created_at')
    list_filter = ('format', 'created_at')
    search_fields = ('report__title',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
