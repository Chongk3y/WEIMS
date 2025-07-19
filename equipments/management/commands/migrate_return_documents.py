from django.core.management.base import BaseCommand
from equipments.models import Equipment, ReturnDocument


class Command(BaseCommand):
    help = 'Migrate existing return documents from Equipment to ReturnDocument model'

    def handle(self, *args, **options):
        migrated = 0
        equipments_with_docs = Equipment.objects.filter(
            return_document__isnull=False, 
            is_returned=True
        ).exclude(return_document='')

        for equipment in equipments_with_docs:
            # Check if this document already exists in ReturnDocument
            existing = ReturnDocument.objects.filter(
                equipment=equipment,
                document=equipment.return_document.name
            ).first()

            if not existing:
                ReturnDocument.objects.create(
                    equipment=equipment,
                    document=equipment.return_document,
                    original_filename=equipment.return_document.name.split('/')[-1],
                    uploaded_by=equipment.updated_by
                )
                migrated += 1
                self.stdout.write(
                    f'Migrated document for equipment: {equipment.item_name}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully migrated {migrated} return documents'
            )
        )
