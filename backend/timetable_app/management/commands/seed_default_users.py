"""
Django management command to seed default admin user for development/testing.
Usage: python manage.py seed_default_users
"""

from django.core.management.base import BaseCommand
from timetable_app.models import User


class Command(BaseCommand):
    help = 'Seed the database with default admin user for development'

    def handle(self, *args, **options):
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@admin.cuk.ac.ke',
                'password': 'admin123',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.Role.ADMIN,
            },
        ]

        created_count = 0
        for user_data in users_data:
            username = user_data['username']
            email = user_data['email']
            password = user_data.pop('password')

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'• User already exists: {username}')
                )
                continue

            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'• Email already registered: {email}')
                )
                continue

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                is_active=True,
            )

            # Set admin as superuser
            if user_data['role'] == User.Role.ADMIN:
                user.is_staff = True
                user.is_superuser = True
                user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created user: {username} | Role: {user.get_role_display()} | Password: {password}'
                )
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Completed! Created {created_count} new user(s).\n'
                f'\nDefault credentials:\n'
                f'  Admin:      admin / admin123       (admin@admin.cuk.ac.ke)'
            )
        )

