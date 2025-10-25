from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Address


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1
    fields = ['address_type', 'street', 'city',
              'state', 'country', 'zip_code', 'is_default']


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, AddressInline)
    list_display = ('email', 'username', 'role', 'phone',
                    'email_verified', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'email_verified')
    search_fields = ('email', 'username', 'phone')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('phone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'email_verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone', 'role', 'password1', 'password2', 'is_active', 'is_staff')}
         ),
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'created_at')
    search_fields = ('user__email', 'user__username')
    list_filter = ('created_at',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_type', 'city',
                    'state', 'country', 'is_default')
    list_filter = ('address_type', 'country', 'is_default')
    search_fields = ('user__email', 'street', 'city', 'state')
    list_editable = ('is_default',)


# Register the custom User model
admin.site.register(User, CustomUserAdmin)
