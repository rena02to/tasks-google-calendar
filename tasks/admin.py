from django.contrib import admin
from .models import Task
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserCreationForm, UserChangeForm
from .models import User, Task, OAUTHToken


class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = ('name', 'email', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ('name', 'email')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'User list'
        return super(UserAdmin, self).changelist_view(request, extra_context=extra_context)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'date', 'time', 'created_at', 'update_at')
    search_fields = ('title', 'description', 'date', 'time')

@admin.register(OAUTHToken)
class OAUTHTokenAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user',)


admin.site.register(User, UserAdmin)
admin.site.site_title = 'Tasks from Google Calendar'
admin.site.index_title = 'Administrative Area'
admin.site.site_header = 'Administrative Area'