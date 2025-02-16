import os
import django

# Django-Umgebung initialisieren
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "videostore.settings")  # Ersetze "dein_projektname" mit deinem Projektnamen
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Test-Upload
thumbnail_name = "Water_thumbnail.jpg"
with open(thumbnail_name, 'rb') as thumbnail_file:
    file_content = thumbnail_file.read()
    default_storage.save('test_upload.jpg', ContentFile(file_content))

print("Test-Upload erfolgreich!")
