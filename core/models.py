from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, UserManager
from django.conf import settings
import uuid
import os


def recipe_image_file_path(instance, filename):
    """Genera path para imagenes"""
    # print("filename :",filename)
    # print("instance :",instance)
    ext = filename.rsplit('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join(f'uploads/recipe/{filename}')


class UserManager(BaseUserManager):
    """Para manager de creacion de user"""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda nuevo usuario"""
        if not email:
            raise ValueError('Users must have an email')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Crear super usuario"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Modelo personalizado de usuario que soporta hacer login con Email en vez de Usuario"""
    email: str = models.EmailField(max_length=255, unique=True)
    name: str = models.CharField(max_length=255)
    is_active: bool = models.BooleanField(default=True)
    is_staff: bool = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Tag(models.Model):
    """ Modelo del tag para la receta"""
    name: str = models.CharField(max_length=255, unique=True)
    user: User = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Modelo de los ingredientes para la receta"""
    name: str = models.CharField(max_length=255, unique=True)
    user: User = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Modelo para la receta"""
    user: User = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, unique=True)
    ingredients = models.ManyToManyField('Ingredient')
    tags = models.ManyToManyField('Tag')
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    image = models.ImageField(null=True, upload_to=recipe_image_file_path, blank=True)

    def __str__(self) -> str:
        return self.title
