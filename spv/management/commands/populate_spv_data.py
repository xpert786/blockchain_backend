from django.core.management.base import BaseCommand
from spv.models import CompanyStage, IncorporationType


class Command(BaseCommand):
    help = 'Populate the database with common company stages and incorporation types'

    def handle(self, *args, **options):
        self.stdout.write('Populating company stages and incorporation types...')
        
        # Common company stages (in order)
        company_stages_data = [
            {'name': 'Pre-seed', 'description': 'Very early stage, idea/concept phase', 'order': 1},
            {'name': 'Seed', 'description': 'Early stage funding, product development', 'order': 2},
            {'name': 'Series A', 'description': 'First significant round of venture capital', 'order': 3},
            {'name': 'Series B', 'description': 'Second round of funding, scaling phase', 'order': 4},
            {'name': 'Series C', 'description': 'Later stage funding, expansion', 'order': 5},
            {'name': 'Series D+', 'description': 'Advanced funding rounds', 'order': 6},
            {'name': 'Bridge', 'description': 'Bridge financing between rounds', 'order': 7},
            {'name': 'Growth', 'description': 'Growth stage funding', 'order': 8},
            {'name': 'Pre-IPO', 'description': 'Pre-initial public offering', 'order': 9},
        ]
        
        # Common incorporation types
        incorporation_types_data = [
            {'name': 'C-Corporation', 'description': 'Standard C-Corp structure (US)'},
            {'name': 'S-Corporation', 'description': 'S-Corp structure (US)'},
            {'name': 'LLC', 'description': 'Limited Liability Company'},
            {'name': 'Limited Company', 'description': 'UK Limited Company'},
            {'name': 'Public Limited Company (PLC)', 'description': 'UK PLC'},
            {'name': 'Private Limited Company', 'description': 'Private Ltd (UK/Commonwealth)'},
            {'name': 'Corporation', 'description': 'General corporation structure'},
            {'name': 'Partnership', 'description': 'General or limited partnership'},
            {'name': 'Sole Proprietorship', 'description': 'Sole proprietorship'},
            {'name': 'B.V. (Besloten Vennootschap)', 'description': 'Dutch private limited company'},
            {'name': 'GmbH', 'description': 'German limited liability company'},
            {'name': 'SARL', 'description': 'French limited liability company'},
            {'name': 'Pte Ltd', 'description': 'Singapore private limited company'},
            {'name': 'Ltd', 'description': 'Limited company (various jurisdictions)'},
        ]
        
        # Create company stages
        stages_created = 0
        for stage_data in company_stages_data:
            stage, created = CompanyStage.objects.get_or_create(
                name=stage_data['name'],
                defaults={
                    'description': stage_data['description'],
                    'order': stage_data['order']
                }
            )
            if created:
                stages_created += 1
                self.stdout.write(f'Created company stage: {stage.name}')
        
        # Create incorporation types
        types_created = 0
        for type_data in incorporation_types_data:
            inc_type, created = IncorporationType.objects.get_or_create(
                name=type_data['name'],
                defaults={'description': type_data['description']}
            )
            if created:
                types_created += 1
                self.stdout.write(f'Created incorporation type: {inc_type.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated {stages_created} new company stages and {types_created} new incorporation types'
            )
        )

