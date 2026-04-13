"""
Django management command to populate the database with default schools and departments.
Usage: python manage.py populate_schools
"""

from django.core.management.base import BaseCommand
from timetable_app.models import School, Department


class Command(BaseCommand):
    help = 'Populate the database with default schools and departments'

    def handle(self, *args, **options):
        schools_data = [
            {
                'name': 'School of Computing and Mathematics',
                'code': 'SCM',
                'description': 'Faculty focused on computer science, mathematics, information technology and software engineering',
                'departments': [
                    {'name': 'Computer Science', 'code': 'CS'},
                    {'name': 'Information Technology', 'code': 'IT'},
                    {'name': 'Mathematics', 'code': 'MTH'},
                    {'name': 'Software Engineering', 'code': 'SE'},
                ]
            },
            {
                'name': 'School of Business and Economics',
                'code': 'SBE',
                'description': 'Faculty dedicated to business administration, economics, accounting and finance education',
                'departments': [
                    {'name': 'Business Administration', 'code': 'BA'},
                    {'name': 'Economics', 'code': 'ECON'},
                    {'name': 'Accounting', 'code': 'ACC'},
                    {'name': 'Finance', 'code': 'FIN'},
                ]
            },
            {
                'name': 'School of Engineering and Technology',
                'code': 'ENG',
                'description': 'Faculty providing engineering and technological education programs',
                'departments': [
                    {'name': 'Civil Engineering', 'code': 'CE'},
                    {'name': 'Electrical Engineering', 'code': 'EE'},
                    {'name': 'Mechanical Engineering', 'code': 'ME'},
                    {'name': 'Electronics and Communication', 'code': 'ECE'},
                ]
            },
            {
                'name': 'School of Arts and Social Sciences',
                'code': 'ARTS',
                'description': 'Faculty offering programs in humanities, languages, and social sciences',
                'departments': [
                    {'name': 'English and Literature', 'code': 'ENG-LIT'},
                    {'name': 'Psychology', 'code': 'PSY'},
                    {'name': 'Sociology', 'code': 'SOC'},
                    {'name': 'History and Philosophy', 'code': 'HIS'},
                ]
            },
            {
                'name': 'School of Health Sciences',
                'code': 'HEALTH',
                'description': 'Faculty dedicated to health professions education',
                'departments': [
                    {'name': 'Medicine', 'code': 'MED'},
                    {'name': 'Nursing', 'code': 'NUR'},
                    {'name': 'Public Health', 'code': 'PH'},
                    {'name': 'Pharmacy', 'code': 'PHM'},
                ]
            }
        ]

        created_schools = 0
        created_departments = 0

        for school_data in schools_data:
            departments = school_data.pop('departments')
            
            school, created = School.objects.get_or_create(
                code=school_data['code'],
                defaults={
                    'name': school_data['name'],
                    'description': school_data['description']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created school: {school.name}')
                )
                created_schools += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'• School already exists: {school.name}')
                )
            
            for dept_data in departments:
                department, dept_created = Department.objects.get_or_create(
                    code=dept_data['code'],
                    defaults={
                        'name': dept_data['name'],
                        'school': school
                    }
                )
                
                if dept_created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created department: {department.name}')
                    )
                    created_departments += 1
                else:
                    # Update school if not already assigned
                    if not department.school:
                        department.school = school
                        department.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Updated department school: {department.name}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  • Department already exists: {department.name}')
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Completed! Created {created_schools} schools and {created_departments} departments.'
            )
        )
