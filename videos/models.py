from django.db.models import Model, DateField, CharField, ImageField


class Video(Model):
    created_at = DateField(auto_now_add=True)
    title = CharField(max_length=80)
    description = CharField(max_length=500)
    thumbnail = ImageField(upload_to="thumbnails/")

    def __str__(self):
        return self.title
