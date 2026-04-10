from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Отправляем письмо с подтверждением только при регистрации, не при входе."""

    def should_send_confirmation_mail(self, request, email_address, signup):
        # Только при регистрации (signup=True). При входе (signup=False) письмо не отправляем.
        return signup
