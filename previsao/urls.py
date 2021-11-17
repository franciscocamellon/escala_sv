from django.urls import re_path, include
from django.contrib import admin
from . import views

app_name = 'previsao'
urlpatterns = [
       re_path(r'^previsao', (views.previsao), name='previsao'),
       re_path(r'^imprimr-escala/', (views.GeneratePDF), name='GeneratePDF'),
       re_path(r'^trocar/(?P<idprevisao>\d+)/(?P<pagina>\d+)',
              (views.trocar_servico), name='trocar_servico'),
       re_path(r'^filtrar',(views.filtrar), name='filtrar'),
       re_path(r'', (views.salvarServico), name='salvarServico'),

]
