from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import UserProfile
from .services import get_or_create_default_game_profile


@receiver(user_signed_up)
def create_user_profile(sender, request, user, **kwargs):
    """Создать UserProfile и один игровой профиль при регистрации."""
    UserProfile.objects.get_or_create(user=user)
    get_or_create_default_game_profile(user)
