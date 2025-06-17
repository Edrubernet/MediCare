from django.contrib import admin
from .models import (
    BodyPart, ExerciseCategory, DifficultyLevel, Exercise, 
    ExerciseImage, ExerciseStep, EducationalMaterial
)


class ExerciseImageInline(admin.TabularInline):
    model = ExerciseImage
    extra = 0


class ExerciseStepInline(admin.TabularInline):
    model = ExerciseStep
    extra = 0
    fields = ('step_number', 'instruction', 'image')
    readonly_fields = ('created_at',)


@admin.register(BodyPart)
class BodyPartAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ExerciseCategory)
class ExerciseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(DifficultyLevel)
class DifficultyLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')
    list_editable = ('value',)
    ordering = ('value',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'is_public', 'created_by', 'created_at')
    list_filter = ('difficulty', 'is_public', 'categories', 'created_at')
    search_fields = ('title', 'description', 'instructions')
    filter_horizontal = ('body_parts', 'categories')
    inlines = [ExerciseStepInline, ExerciseImageInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'instructions', 'precautions')
        }),
        ('Classification', {
            'fields': ('body_parts', 'categories', 'difficulty')
        }),
        ('Media', {
            'fields': ('video', 'video_thumbnail')
        }),
        ('Settings', {
            'fields': ('is_public', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ExerciseImage)
class ExerciseImageAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'caption', 'image')
    list_filter = ('exercise',)
    search_fields = ('exercise__title', 'caption')


@admin.register(ExerciseStep)
class ExerciseStepAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'step_number', 'instruction_preview', 'image', 'created_at')
    list_filter = ('exercise', 'created_at')
    search_fields = ('exercise__title', 'instruction')
    ordering = ('exercise', 'step_number')

    def instruction_preview(self, obj):
        return obj.instruction[:50] + '...' if len(obj.instruction) > 50 else obj.instruction
    instruction_preview.short_description = 'Instruction Preview'


@admin.register(EducationalMaterial)
class EducationalMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'created_by', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('related_exercises',)
    readonly_fields = ('created_at',)
