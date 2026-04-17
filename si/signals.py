from django.db.models.signals import pre_delete
from django.db.models.fields.files import FileField
from django.dispatch import receiver
from pathlib import Path


@receiver(pre_delete)
def delete_files_on_model_delete(sender, instance, **kwargs):
    """
    Удаляет все файлы ImageField/FileField с диска при удалении экземпляра модели.
    Работает для всех моделей, у которых есть FileField или ImageField.
    """
    for field in instance._meta.fields:
        if isinstance(field, FileField):
            file_field = getattr(instance, field.name)
            if file_field and file_field.name:
                try:
                    file_path = Path(file_field.path)
                    if file_path.exists():
                        file_path.unlink()
                except Exception:
                    pass
