from django.db import models

# Create your models here.
import re

from django.db import models
from django.core import validators
from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin,
    UserManager)
from django.conf import settings


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        'Nome de Usuário', max_length=30, unique=True,
        validators=[validators.RegexValidator(re.compile('^[\w.@+-]+$'),
            'O nome de usuário só pode conter letras, digitos ou os '
            'seguintes caracteres: @/./+/-/_', 'invalid')]
    )
    email = models.EmailField('E-mail', unique=True)
    nome = models.CharField('Nome Completo', max_length=100, null=True, blank=True)
    cpf = models.CharField(
        'CPF', max_length=11, null=True,
        validators=[validators.RegexValidator(re.compile(r"[0-9]"),
            'CPF só pode conter digitos de 0 a 9', 'invalid')],
    )
    nome_guerra = models.CharField('Nome de Guerra', null=True, max_length=40, blank=True)

    #o índice começa em 5 aqui para mantar
    #uma correspondência com todos os postos
    #existentes no Exército, assim teríamos
    # 1 - Marechal, 2 - Gen de Exército
    # 3 - Gen de Divisão, 4 - Gen Brigada
    # e os demais, conforme abaixo enumerados:
    POSTO_CHOICES = (  (5, "Cel"), (6, "T Cel"), (7, "Maj"),
        (8, "Cap"), (9, "1º Ten"), (10, "2º Ten"), (11, "Asp"),
        (12, "S Ten"), (13, "1º Sgt"), (14, "2º Sgt"),
        (15, "3º Sgt"), (16, "Cb"),  (17, "SD"),
    )
    posto = models.IntegerField('Posto/Graduação', null=True, choices = POSTO_CHOICES, blank=True)
    GENDER_CHOICES =((1, "Masculino"), (2, "Feminino"), )
    sexo = models.IntegerField('Gênero', null=True, choices=GENDER_CHOICES, blank=True)
    tel1 = models.CharField('Telefone 1', max_length=15, null=True, blank=True)
    tel2 = models.CharField('Telefone 2', max_length=15, null=True, blank=True)
    data_nasc = models.DateField('Data Nascimento', null=True, blank=True)
    data_praca = models.DateField('Data de Praça',null=True, blank=True)
    is_active = models.BooleanField('Está ativo?', blank=True, default=True)
    is_staff = models.BooleanField('É da equipe?', blank=True, default=False)
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.nome or self.username

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return str(self)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class PasswordReset(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Usuário',
        related_name='resets', on_delete=models.CASCADE,
    )
    key = models.CharField('Chave', max_length=100, unique=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    confirmed = models.BooleanField('Confirmado?', default=False, blank=True)

    def __str__(self):
        return '{0} em {1}'.format(self.user, self.created_at)

    class Meta:
        verbose_name = 'Nova Senha'
        verbose_name_plural = 'Novas Senhas'
        ordering = ['-created_at']
