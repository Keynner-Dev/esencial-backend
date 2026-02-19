from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_groups(sender, **kwargs):
    # Evita correr para apps no relacionadas (pero no pasa nada si corre)
    try:
        from django.contrib.auth.models import Group, Permission
    except Exception:
        return

    admin_group, _ = Group.objects.get_or_create(name="ADMIN")
    Group.objects.get_or_create(name="SELLER")

    # Asignar permiso can_refund a ADMIN si ya existe
    perm = Permission.objects.filter(codename="can_refund").first()
    if perm:
        admin_group.permissions.add(perm)