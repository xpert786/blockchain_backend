from django.core.management.base import BaseCommand
from users.models import Sector, Geography


class Command(BaseCommand):
    help = 'Populate the database with common sectors and geographies'

    def handle(self, *args, **options):
        self.stdout.write('Populating sectors and geographies...')
        
        # Common sectors
        sectors_data = [
            {'name': 'Technology', 'description': 'Software, hardware, and technology services'},
            {'name': 'Artificial Intelligence', 'description': 'AI/ML companies and solutions'},
            {'name': 'Blockchain', 'description': 'Cryptocurrency, DeFi, and blockchain technology'},
            {'name': 'SaaS', 'description': 'Software as a Service companies'},
            {'name': 'Fintech', 'description': 'Financial technology and digital banking'},
            {'name': 'Healthcare', 'description': 'Medical devices, pharmaceuticals, and health tech'},
            {'name': 'Biotech', 'description': 'Biotechnology and life sciences'},
            {'name': 'Clean Energy', 'description': 'Renewable energy and sustainability'},
            {'name': 'Real Estate', 'description': 'Property development and real estate tech'},
            {'name': 'E-commerce', 'description': 'Online retail and marketplace platforms'},
            {'name': 'Cybersecurity', 'description': 'Information security and data protection'},
            {'name': 'Edtech', 'description': 'Educational technology and online learning'},
            {'name': 'Gaming', 'description': 'Video games and interactive entertainment'},
            {'name': 'Media', 'description': 'Digital media and content creation'},
            {'name': 'Transportation', 'description': 'Mobility and logistics technology'},
        ]
        
        # Common geographies
        geographies_data = [
            # North America
            {'name': 'United States', 'region': 'North America', 'country_code': 'USA'},
            {'name': 'Canada', 'region': 'North America', 'country_code': 'CAN'},
            {'name': 'Mexico', 'region': 'North America', 'country_code': 'MEX'},
            
            # Europe
            {'name': 'United Kingdom', 'region': 'Europe', 'country_code': 'GBR'},
            {'name': 'Germany', 'region': 'Europe', 'country_code': 'DEU'},
            {'name': 'France', 'region': 'Europe', 'country_code': 'FRA'},
            {'name': 'Netherlands', 'region': 'Europe', 'country_code': 'NLD'},
            {'name': 'Switzerland', 'region': 'Europe', 'country_code': 'CHE'},
            {'name': 'Ireland', 'region': 'Europe', 'country_code': 'IRL'},
            {'name': 'Spain', 'region': 'Europe', 'country_code': 'ESP'},
            {'name': 'Italy', 'region': 'Europe', 'country_code': 'ITA'},
            {'name': 'Sweden', 'region': 'Europe', 'country_code': 'SWE'},
            {'name': 'Denmark', 'region': 'Europe', 'country_code': 'DNK'},
            {'name': 'Norway', 'region': 'Europe', 'country_code': 'NOR'},
            
            # Asia-Pacific
            {'name': 'Singapore', 'region': 'Asia-Pacific', 'country_code': 'SGP'},
            {'name': 'Hong Kong', 'region': 'Asia-Pacific', 'country_code': 'HKG'},
            {'name': 'Japan', 'region': 'Asia-Pacific', 'country_code': 'JPN'},
            {'name': 'South Korea', 'region': 'Asia-Pacific', 'country_code': 'KOR'},
            {'name': 'Australia', 'region': 'Asia-Pacific', 'country_code': 'AUS'},
            {'name': 'New Zealand', 'region': 'Asia-Pacific', 'country_code': 'NZL'},
            {'name': 'India', 'region': 'Asia-Pacific', 'country_code': 'IND'},
            {'name': 'China', 'region': 'Asia-Pacific', 'country_code': 'CHN'},
            {'name': 'Taiwan', 'region': 'Asia-Pacific', 'country_code': 'TWN'},
            {'name': 'Thailand', 'region': 'Asia-Pacific', 'country_code': 'THA'},
            {'name': 'Malaysia', 'region': 'Asia-Pacific', 'country_code': 'MYS'},
            {'name': 'Indonesia', 'region': 'Asia-Pacific', 'country_code': 'IDN'},
            {'name': 'Philippines', 'region': 'Asia-Pacific', 'country_code': 'PHL'},
            {'name': 'Vietnam', 'region': 'Asia-Pacific', 'country_code': 'VNM'},
            
            # Middle East & Africa
            {'name': 'United Arab Emirates', 'region': 'Middle East', 'country_code': 'ARE'},
            {'name': 'Saudi Arabia', 'region': 'Middle East', 'country_code': 'SAU'},
            {'name': 'Israel', 'region': 'Middle East', 'country_code': 'ISR'},
            {'name': 'South Africa', 'region': 'Africa', 'country_code': 'ZAF'},
            {'name': 'Nigeria', 'region': 'Africa', 'country_code': 'NGA'},
            {'name': 'Kenya', 'region': 'Africa', 'country_code': 'KEN'},
            {'name': 'Egypt', 'region': 'Africa', 'country_code': 'EGY'},
            
            # South America
            {'name': 'Brazil', 'region': 'South America', 'country_code': 'BRA'},
            {'name': 'Argentina', 'region': 'South America', 'country_code': 'ARG'},
            {'name': 'Chile', 'region': 'South America', 'country_code': 'CHL'},
            {'name': 'Colombia', 'region': 'South America', 'country_code': 'COL'},
            {'name': 'Peru', 'region': 'South America', 'country_code': 'PER'},
        ]
        
        # Create sectors
        sectors_created = 0
        for sector_data in sectors_data:
            sector, created = Sector.objects.get_or_create(
                name=sector_data['name'],
                defaults={'description': sector_data['description']}
            )
            if created:
                sectors_created += 1
                self.stdout.write(f'Created sector: {sector.name}')
        
        # Create geographies
        geographies_created = 0
        for geo_data in geographies_data:
            geography, created = Geography.objects.get_or_create(
                name=geo_data['name'],
                defaults={
                    'region': geo_data['region'],
                    'country_code': geo_data['country_code']
                }
            )
            if created:
                geographies_created += 1
                self.stdout.write(f'Created geography: {geography.name} ({geography.region})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated {sectors_created} new sectors and {geographies_created} new geographies'
            )
        )
