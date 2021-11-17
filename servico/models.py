from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.mail import send_mail_template

from pessoal import models as pessoalModel

# Create your models here.
class Servicos(models.Model):
    idmilitar = models.IntegerField('Id Militar',null=False)
    idcirculo = models.IntegerField('Círculo',null=False)
    idescala = models.IntegerField('Id Escala',null=False)
    #precedencia = models.IntegerField('Prioridade',null=True)
    idsubstituto = models.IntegerField('Id Militar Substituto',null=True)
    nomeguerra = models.CharField('Nome de Guerra', max_length=40)
    nomesubstituto = models.CharField('Nome de Guerra', max_length=40, null=True)
    folga = models.IntegerField('Folga Preta',null=False)
    data = models.DateField('Data')
    dia = models.CharField('Dia da Semana', max_length=15)
    vermelha = models.BooleanField('Vermelha', default=False)


    #objects = CourseManager()

    def __str__(self):
        return str(self.idmilitar)

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['data']
