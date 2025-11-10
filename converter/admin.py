from django.contrib import admin
from .models import Support

@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ('title', 'contact', 'created_at')
    search_fields = ('title', 'message', 'contact')
    readonly_fields = ('created_at',)

# Register your models here.
