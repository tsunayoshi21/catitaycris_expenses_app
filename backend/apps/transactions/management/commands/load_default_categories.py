from django.core.management.base import BaseCommand
from apps.transactions.models import Category


DEFAULT_CATEGORIES = [
    ('comida', 'Comida y restaurantes'),
    ('supermercado', 'Supermercado'),
    ('transporte', 'Transporte'),
    ('entretenimiento', 'Entretenimiento'),
    ('salud', 'Salud y farmacia'),
    ('educacion', 'Educacion'),
    ('ropa', 'Ropa y accesorios'),
    ('viajes', 'Viajes y alojamiento'),
    ('servicios', 'Servicios y suscripciones'),
    ('regalos', 'Regalos y donaciones'),
    ('hogar', 'Hogar y equipamiento'),
    ('tecnologia', 'Tecnologia y electronica'),
    ('otros', 'Otros'),
]


class Command(BaseCommand):
    help = 'Load default transaction categories'

    def handle(self, *args, **options):
        created = 0
        for name, label in DEFAULT_CATEGORIES:
            _, was_created = Category.objects.get_or_create(
                name=name,
                owner=None,
                defaults={'label': label, 'is_default': True},
            )
            if was_created:
                created += 1
        self.stdout.write(
            f'Categorias cargadas: {created} nuevas, {len(DEFAULT_CATEGORIES) - created} ya existian.'
        )
