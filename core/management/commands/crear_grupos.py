"""
Comando de gestión para inicializar grupos (roles) y usuarios de prueba.

Uso:
    python manage.py crear_grupos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from decouple import config


class Command(BaseCommand):
    help = "Crea los grupos (admin, normal, viewer) y los usuarios de prueba con contraseñas desde .env"

    def handle(self, *args, **options):
        # 1. Crear grupos de roles
        for nombre in ("admin", "normal", "viewer"):
            grupo, creado = Group.objects.get_or_create(name=nombre)
            if creado:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{nombre}" creado.'))
            else:
                self.stdout.write(f'Grupo "{nombre}" ya existía.')

        # 2. Obtener contraseñas obligatoriamente desde .env (nunca hardcodeadas ni con defaults)
        pass_admin = config("PASS_ADMIN")
        pass_normal = config("PASS_NORMAL")
        try:
            pass_viewer = config("PASS_VIEWER")
        except Exception:
            pass_viewer = config("PASS_LECTOR")

        # 3. Crear o actualizar usuarios
        usuarios_config = [
            {"username": "admin1", "pass": pass_admin, "group": "admin", "is_super": True},
            {"username": "usuario1", "pass": pass_normal, "group": "normal", "is_super": False},
            {"username": "lector1", "pass": pass_viewer, "group": "viewer", "is_super": False},
            {"username": "lector", "pass": pass_viewer, "group": "viewer", "is_super": False},
        ]

        for u_data in usuarios_config:
            user, creado = User.objects.get_or_create(username=u_data["username"])
            user.set_password(u_data["pass"])
            if u_data["is_super"]:
                user.is_staff = True
                user.is_superuser = True
            user.save()

            grupo = Group.objects.get(name=u_data["group"])
            user.groups.add(grupo)

            estado_str = "creado" if creado else "actualizado"
            self.stdout.write(self.style.SUCCESS(
                f'Usuario "{user.username}" {estado_str} con rol [{u_data["group"]}].'
            ))

        self.stdout.write(self.style.SUCCESS("\n¡Roles y usuarios configurados exitosamente!"))
