from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.mail import send_mail_template

from pessoal import models as pessoalModel



"""class CourseManager(models.Manager):

    def search(self, query):
        return self.get_queryset().filter(
            models.Q(name__icontains=query) | \
            models.Q(description__icontains=query)
        )
"""

class Escala(models.Model):

    descricao = models.CharField('Descrição', max_length=40)
    ticado = models.BooleanField('Marcado?', blank=True, default=True)
    precedencia = models.IntegerField('Precedência',default=0)
    nrmilitaresnaescala = models.IntegerField('Nº Mil na Escala?', null=False, default=3)
    CIRCULO_CHOICES = [ (0, 'Oficial'), (1, 'ST/SGT'),(2, 'CB/SD'), (3, 'TODOS')]
    idcirculo = models.IntegerField('Círculo Hierárquico',null=False,
    choices=CIRCULO_CHOICES, blank=False)
    qtdporescala = models.IntegerField('Qtos escalados por dia?',null=False, default=1)
    CORRIDA_CHOICES= [(1, "SIM"), (0, "NÃO")]
    corrida = models.BooleanField('Escala Corrida?', choices= CORRIDA_CHOICES, default=0)
    folgaminima = models.IntegerField('Folga Mínima?',null=False, default=1)

    #objects = CourseManager()

    def __str__(self):
        return self.descricao

    class Meta:
        verbose_name = 'Escala'
        verbose_name_plural = 'Escalas'
        ordering = ['precedencia']
"""
    #@models.permalink
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('courses:details', args=[self.slug])

    def release_lessons(self):
        today = timezone.now().date()
        return self.lessons.filter(release_date__gte=today)

"""


# -- Cria a Tabela de controlar folgas
class ControlarFolgas(models.Model):
#    idmilitar = models.ForeignKey(pessoalModel.Militar,
#        verbose_name='Id Militar', related_name='idmilitar',
#        on_delete = models.CASCADE, blank=True, default=0
#        )

    idmilitar = models.IntegerField('Id Militar', blank=True, default=0)
    idcirculo = models.IntegerField('Id Círculo', blank=True, default=-1 )

    #ESCALA_CHOICES=Escala.objects.values_list('id', 'descricao')
    #idescala = models.IntegerField('Escala', blank=False, choices=ESCALA_CHOICES)
    idescala = models.IntegerField('Escala', blank=False)

    red = models.IntegerField('Folga Vermelha', null=True, blank=True, default=100)
    black = models.IntegerField('Folga Preta',  null=True, blank=True, default=100)
    realred = models.IntegerField('Folga Vermelha',  blank=False, default=100)
    realblack = models.IntegerField('Folga Preta', blank=False, default=100)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Folga'
        verbose_name_plural = 'Folgas'
        ordering = ['-id']


# -- Cria a Tabela de designar escalas
class DesignarEscala(models.Model):
    idmilitar = models.IntegerField('Id Militar', blank=True, default=0)
    idcirculo = models.IntegerField('Id Círculo', blank=True, default=0)
    idescala = models.IntegerField('Id Escala', blank=True, default=0)
    preta = models.BooleanField('Preta', blank=True, default=True)
    vermelha = models.BooleanField('Vermelha', blank=True, default=True)
    seg = models.BooleanField('Seg', blank=True, default=True)
    ter = models.BooleanField('Ter', blank=True, default=True)
    qua = models.BooleanField('Qua', blank=True, default=True)
    qui = models.BooleanField('Qui', blank=True, default=True)
    sex = models.BooleanField('Sex', blank=True, default=True)
    sab = models.BooleanField('Sáb', blank=True, default=True)
    dom = models.BooleanField('Dom', blank=True, default=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Designar'
        verbose_name_plural = 'Designados'
        ordering = ['-id']

    def get_absolute_url(self):
        #print('passou no get_absolute_url de DesignarEscala')
        from django.urls import reverse
        return reverse('core:escalar', args=[self.idmilitar, self.idcirculo])

# -- Cria a Tabela de Dispensas
class Dispensas(models.Model):
    idmilitar = models.IntegerField('Id Militar')
    idcirculo = models.IntegerField('Id Círculo')
    datainicio = models.DateField('Início')
    datafim = models.DateField('Fim')
    motivo = models.CharField('Motivo', max_length=100)
    PREJUZO_CHOICES= [(1, "SIM"), (0, "NÃO")]
    prejuizo = models.BooleanField('Prejuízo da Escala?',
    blank=True, default=True, choices=PREJUZO_CHOICES)

    def __str__(self):
        return str(self.idmilitar)

    class Meta:
        verbose_name = 'Dispensa'
        verbose_name_plural = 'Dispensas'
        ordering = ['idmilitar']

# -- Cria a Tabela de Feriados
class Feriados(models.Model):
    data = models.DateField('Data', null=False, blank=False, max_length=10,)
    descricao = models.CharField('Feriado', max_length=60)
    dia = models.CharField('Dia da Semana', max_length=15, blank = True)

    def __str__(self):
        return self.descricao

    class Meta:
        verbose_name = 'Feriado'
        verbose_name_plural = 'Feriados'
        ordering = ['data']


"""class Lesson(models.Model):

    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True)
    number = models.IntegerField('Número (ordem)', blank=True, default=0)
    release_date = models.DateField('Data de Liberação', blank=True, null=True)

    course = models.ForeignKey(Course, verbose_name='Curso', related_name='lessons',
        on_delete = models.CASCADE,
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    def __str__(self):
        return self.name

    def is_available(self):
        if self.release_date:
            today = timezone.now().date()
            return self.release_date >= today
        return False

    class Meta:
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'
        ordering = ['number']


class Material(models.Model):

    name = models.CharField('Nome', max_length=100)
    embedded = models.TextField('Vídeo embedded', blank=True)
    file = models.FileField(upload_to='lessons/materials', blank=True, null=True)

    lesson = models.ForeignKey(Lesson, verbose_name='Aula', related_name='materials',
        on_delete = models.CASCADE,
    )

    def is_embedded(self):
        return bool(self.embedded)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Matérial'
        verbose_name_plural = 'Materiais'


class Enrollment(models.Model):

    STATUS_CHOICES = (
        (0, 'Pendente'),
        (1, 'Aprovado'),
        (2, 'Cancelado'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Usuário',
        related_name='enrollments', on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        Course, verbose_name='Curso', related_name='enrollments',
        on_delete=models.CASCADE,
    )
    status = models.IntegerField(
        'Situação', choices=STATUS_CHOICES, default=1, blank=True
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    def active(self):
        self.status = 1
        self.save()

    def is_approved(self):
        return self.status == 1

    class Meta:
        verbose_name = 'Inscrição'
        verbose_name_plural = 'Inscrições'
        unique_together = (('user', 'course'),)

class Announcement(models.Model):

    course = models.ForeignKey(
        Course, verbose_name='Curso', related_name='announcements',
        on_delete = models.CASCADE,
    )
    title = models.CharField('Título', max_length=100)
    content = models.TextField('Conteúdo')

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Anúncio'
        verbose_name_plural = 'Anúncios'
        ordering = ['-created_at']


class Comment(models.Model):

    announcement = models.ForeignKey(
        Announcement, verbose_name='Anúncio', related_name='comments',
        on_delete = models.CASCADE,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='usuário',
            on_delete = models.CASCADE,
    )
    comment = models.TextField('Comentário')

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['created_at']


def post_save_announcement(instance, created, **kwargs):
    if created:
        subject = instance.title
        context = {
            'announcement': instance
        }
        template_name = 'courses/announcement_mail.html'
        enrollments = Enrollment.objects.filter(
            course=instance.course, status=1
        )
        for enrollment in enrollments:
            recipient_list = [enrollment.user.email]
            send_mail_template(subject, template_name, context, recipient_list)

models.signals.post_save.connect(
    post_save_announcement, sender=Announcement,
    dispatch_uid='post_save_announcement'
)
"""
