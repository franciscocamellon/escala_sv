from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect,get_object_or_404
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


#para gerar o dict_dados
from collections import defaultdict
from itertools import chain


from .forms import *
from .models import *
from servico.models import Servicos
from pessoal.models import Militar
from core.models import *
#from core.forms import FormPrevisao arranquei do core

#usado para fazer uma conexão direta com o banco de dados
from django.db import connection

# Create your views here.
def data_valida(data):
    try:
        datetime.strptime(data, '%Y/%m/%d')
        return True
    except ValueError:
        return False
#retorna verdadeiro se a data passda for feriado
def feriado(diaEscala):

    queryset = Feriados.objects.raw('''SELECT id, data FROM core_feriados
            WHERE data=%s''', [diaEscala])

    return len(list(queryset))>0

#retorna verdadeiro se for sábado weekday = 5 ou Domingo weekday = 6
#ou, ainda, feriado, retornado através da função feriado.
def vermelha(diaEscala):
    vermelha = ((diaEscala.weekday()==5) | # 5 é sábado e 6 Domingo
            (diaEscala.weekday()==6) |
            (feriado(diaEscala)))
    #print('é escala vermelha? ', vermelha)
    return vermelha

#retorna verdadeiro se o militar está dispensado no dia da escala e
#soma mais um dia, para fins de não ser escalado no dia de sua
#apresentação pronto para o Serviço.
def dispensado(idmilitar,idcirculo,diaescala):

    #queryset = Dispensas.objects.filter(idmilitar=idmilitar, idcirculo=idcirculo)
    #só estará dispensado se, além de as datas estarem dentro da do intervalo
    #fornecido, a dispensa for com prejuízo da escala, campo prejuizo
    queryset = Dispensas.objects.raw('''SELECT id, datainicio, datafim FROM
                core_dispensas WHERE idmilitar=%s AND idcirculo=%s AND
                prejuizo=True ORDER BY datafim DESC''',
                [idmilitar, idcirculo])


    #print(diaescala)
    #print(next_day)
    dispensado = False
    for disp in queryset:
        #foi comentado esse 'datainicio' para poder fazer o que está logo embaixo
        #que garante que o militar não será escalado na véspera das férias, para
        #não começar as férias saindo de serviço
        #datainicio = disp.datainicio #faz while para passar para próxima data preta.
        # subtrai um dia para não escalar o militar na véspera de sua dispensa
        datainicio = disp.datainicio - timedelta(1)
        proximadata = disp.datafim + timedelta(1)
        #faz while para passar para próxima data preta.
        while (vermelha(proximadata)):
            proximadata = proximadata + timedelta(1)
        dispensado = ((diaescala>=datainicio) & (diaescala <= proximadata))

    return dispensado

#esse método verifica se o militar está concorrendo à esquala a que corresponde
# o dia da escala repassado pelo parâmetro diaEscala
def concorreVerPretaDiasSemana(idmilitar,idcirculo, idescala,diaEscala):
    queryset = DesignarEscala.objects.filter(idmilitar=idmilitar,
    idcirculo=idcirculo, idescala=idescala)
    if queryset.count()==0:
        return False

    #tipoEscala é usado para verificar se o militar concorre ao tipo, essa
    #verificação é feita no banco passando o nome do campo que na tabela é
    #preta e vermelha
    dia = False
    concorr_tipoescala = False
    tipoEscala = "preta"
    DIAS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom']

    for designado in queryset:
        if vermelha(diaEscala):
            tipoEscala ="vermelha"
        if (tipoEscala)== "vermelha":
            concorr_tipoescala = designado.vermelha
        elif (tipoEscala)== "preta":
            concorr_tipoescala = designado.preta


        if DIAS[diaEscala.weekday()]=="seg":
            dia = designado.seg
        elif DIAS[diaEscala.weekday()]=="ter":
            dia = designado.ter
        elif DIAS[diaEscala.weekday()]=="qua":
            dia = designado.qua
        elif DIAS[diaEscala.weekday()]=="qui":
            dia = designado.qui
        elif DIAS[diaEscala.weekday()]=="sex":
            dia = designado.sex
        elif DIAS[diaEscala.weekday()]=="sab":
            dia = designado.sab
        elif DIAS[diaEscala.weekday()]=="dom":
            dia = designado.dom
    #print('concorre? ', concorr_tipoescala, dia)
    return (concorr_tipoescala & dia)

#retorna o dia da sema weekday retorna um inteiro de 0 a 6
#0 corresponde a segunda-feira e assim sucessivamente
def diadaSemana(diaEscala):
    DIAS = [
        'Segunda-feira',
        'Terça-feira',
        'Quarta-feira',
        'Quinta-feira',
        'Sexta-feira',
        'Sábado',
        'Domingo'
    ]
    return DIAS[diaEscala.weekday()]

#retorna o Posto/Graduação
def getPostoGraduacao(idPosto):
    POSTO = [(5, "Cel"), (6, "T Cel"), (7, "Maj"),
    (8, "Cap"), (9, "1º Ten"), (10, "2º Ten"), (11, "Asp"),
    (12, "S Ten"), (13, "1º Sgt"), (14, "2º Sgt"), (15, "3º Sgt"),
    (16, "Cb"),  (17, "SD")]
    #O primeiro elemento da lista é 0, (5,"Cel"), faz-se necessário subtarir 5 pq no banco
    #o idPosto desse elemento é cinco, porém, como estamos acessando uma lista, precisamos
    #do índice correto, que é zero, já para pegar o posto, propriamente dito, que está em
    #uma tupla, precisamos apenas passar o índice do posto, que aqui SEMPRE será 1, vez que
    #só temos os dois elementos idposto e posto, idPosto está no índice zero da dupla e o posto,
    #propriamente dito, está no índice 1, daí porque usar o 1 no retorno da função!
    id = idPosto-5
    return POSTO[id][1]

#verifica se o critério de folga mínima é obdecido, caso contrário,
#não escala o militar
def folgaMinima(idmilitar,idcirculo,idescala,diaescala):
#    queryset = Escala.objects.all().filter(id=idescala)
#    folgaminima = queryset['folgaminima']
    queryset = Escala.objects.raw('''SELECT id, folgaminima FROM
                core_escala WHERE id=%s''', [idescala])
    folgaminima = 0
    for folgas in queryset:
        folgaminima = folgas.folgaminima

    #print('a folga mínima é: ', folgaminima)
    #cria uma variável diaescala - folgamínima, para procurar nas
    #tabelas previsao e serviços se o diaescala real obedece à folga mínima
    #estabelecida na escala.
    diadaEscala = diaescala - timedelta(folgaminima)
    queryset_previsao = Previsao.objects.raw('''SELECT a.id, a.data FROM
        previsao_previsao a, core_escala b WHERE a.idmilitar =%s AND
        a.idcirculo =%s AND b.id=a.idescala AND a.data>=%s''',
        [idmilitar, idcirculo, diadaEscala])

    queryset_servico = Servicos.objects.raw('''SELECT a.id, a.data FROM
        servico_servicos a, core_escala b WHERE a.idmilitar =%s AND
        a.idcirculo =%s AND b.id=a.idescala AND a.data>=%s''',
        [idmilitar, idcirculo, diadaEscala])

    deservico = len(list(queryset_servico))
    previsto  = len(list(queryset_previsao))
    tem_folga = (deservico==0) & (previsto==0)
 
    #print('militar de servico? ', deservico, '  militar previsto? ', previsto)
    #print('tem folga? ', tem_folga)
    #se serviço ou previsão tiver algum registro, retorna falso,
    #caso contrário, retorna verdadeiro
    return tem_folga

    #trecho abaixo comentado por usar sql puro
    """with connection.cursor() as cursor:
        query = '''SELECT a.data, FROM previsao_previsao a,
            core_escala b WHERE a.idmilitar =%s AND a.idcirculo =%s
            AND b.id=a.idescala AND a.data>=%s'''
        cursor.execute(query, [idmilitar, idcirculo, diadaEscala])
        if cursor.rowcount>0:
            return False
        query = '''SELECT a.data, FROM servico_servicos a,
            core_escala b WHERE a.idmilitar =%s AND a.idcirculo =%s
            AND b.id=a.idescala AND a.data>=%s  '''
        cursor.execute(query, [idmilitar, idcirculo, diadaEscala])
        if cursor.rowcount>0:
            return False"""

    #return True

#toda vez que manda fazer uma previsão, a atual é limpa para
#evitar o erro da folga
def limparPrevisao():
    #executa um Update na tabela folgas
    sql_controlarfolgas = ControlarFolgas.objects.all()
    for folgas in sql_controlarfolgas:
        realred = folgas.realred
        realblack = folgas.realblack
        ControlarFolgas.objects.filter(id=folgas.id).update(red=realred, black=realblack)
    #Executa um Delete na tabela previsao
    Previsao.objects.all().delete()
    return

def podeSalvarServico():
   # len(Previsao.objects.raw('SELECT DISTINCT(data), id FROM previsao_previsao GROUP BY data, id'))<=3
    
    #trecho abaixo comentado por usar sql puro
    with connection.cursor() as cursor:
        query = 'SELECT DISTINCT(data) FROM previsao_previsao GROUP BY data'
        cursor.execute(query)
        if cursor.rowcount>3:
            return False
    return True

#salva os serviços de acordo com a previsão
def salvarServico(request):
    #pega todos os objetos de previsão para inserir em serviços
    queryset_previsao = Previsao.objects.raw(
        '''SELECT * FROM previsao_previsao GROUP BY idmilitar, id'''
    ) #aqui resolve o problema identificado abaixo
    #queryset = Previsao.objects.all() #aqui pega todos, inclusive ID, tenho que resolver isso
    for queryset in queryset_previsao:
        insert_servicos = Servicos(
            idmilitar=queryset.idmilitar,idcirculo=queryset.idcirculo,
            idescala=queryset.idescala,#precedencia=queryset.precedencia,
            idsubstituto=queryset.idsubstituto,nomeguerra=queryset.nomeguerra,
            folga=queryset.folga,data=queryset.data,dia=queryset.dia,
            vermelha=queryset.vermelha, nomesubstituto=queryset.nomesubstituto
        ) 
        # em princípio é pra funcionar
        insert_servicos.save()
    #executa um Update na tabela folgas
    sql_controlarfolgas = ControlarFolgas.objects.all()
    for folgas in sql_controlarfolgas:
        ControlarFolgas.objects.filter(id=folgas.id).update(realred=folgas.red, realblack=folgas.black)
    #ControlarFolgas.objects.update(realred=red, realblack=black)
    #Executa um Delete na tabela previsao
    Previsao.objects.all().delete()

    return redirect('servico:servicos')

#rodar previsaão da escala
def rodaprevisao(dataInicio,dataFim):
    diaEscala = dataInicio
    diaFim = dataFim
    
    queryset_servico = Servicos.objects.all().order_by('data').last()
    if queryset_servico!=None:
        data = queryset_servico.data
        diaEscala = data + timedelta(1)

    intervalo = 0
    while (diaEscala <= diaFim):
        query_escala_fazer = Escala.objects.raw('''
            SELECT id, qtdporescala, corrida FROM core_escala
            WHERE ticado=True ORDER BY idcirculo,
            precedencia DESC
        ''')
        tipofolga="black"
        escvermelha = vermelha(diaEscala)
        if(escvermelha):
            tipofolga="red"

        #print('o tipo de folga é: ', tipofolga)

        for escalas in query_escala_fazer:
            #print('a escala é: ', escalas)
            idEscala = escalas.id
            nrmilporescala = escalas.qtdporescala
            escalacorrida = escalas.corrida
            while (nrmilporescala>0):
                sql_pessoal = ""
                if tipofolga == "black":
                    sql_pessoal='''SELECT a.id,a.idcirculo,a.nome_guerra,
                    b.idescala, c.black FROM pessoal_militar a,
    				core_designarescala b,core_controlarfolgas c WHERE
                    (a.id=b.idmilitar AND a.idcirculo=b.idcirculo AND
                    c.idmilitar=b.idmilitar AND c.idcirculo=b.idcirculo
                    AND b.idescala=%s AND
                    c.idescala=%s AND a.pronto=True)
    				ORDER BY a.idcirculo, a.antiguidade'''

                elif tipofolga == "red":
                    sql_pessoal='''SELECT a.id,a.idcirculo,a.nome_guerra,
                    b.idescala, c.red FROM pessoal_militar a,
    				core_designarescala b,core_controlarfolgas c WHERE
                    (a.id=b.idmilitar AND a.idcirculo=b.idcirculo AND
                    c.idmilitar=b.idmilitar AND c.idcirculo=b.idcirculo
                    AND b.idescala=%s AND
                    c.idescala=%s AND a.pronto=True)
    				ORDER BY a.idcirculo, a.antiguidade'''
                    #print ("o Sql é de escala vermelha:", sql_pessoal)

                array_pessoa = Militar.objects.raw(sql_pessoal,
                    [idEscala, idEscala]
                )
                #print(len(list(array_pessoa)))
                folga = 0
                idmilitar = 0
                idcirculo = -1
                nomeguerra = ""
                #print(array_pessoa)
                for pessoal in array_pessoa:
                    idmil = pessoal.id
                    idcirc = pessoal.idcirculo
                    idesc = pessoal.idescala

                    estadispensado = dispensado(idmil,idcirc,diaEscala)
                    concorre = concorreVerPretaDiasSemana(idmil,idcirc,idesc,diaEscala)
                    estafolgado = folgaMinima(idmil,idcirc,idesc,diaEscala)
                    #print('está dispensado? ',estadispensado)
                    #print('concorre? ',concorre)
                    #print('está folgado? ',estafolgado)
                    if tipofolga =="black":
                        maisfolgado = (pessoal.black>=folga)
                        if (maisfolgado & (not estadispensado) & concorre & estafolgado):
                            folga = pessoal.black
                            idmilitar = pessoal.id
                            idcirculo = pessoal.idcirculo
                            nomeguerra = pessoal.nome_guerra

                    elif tipofolga == "red":
                        #print(pessoal.red, folga)
                        maisfolgado = (pessoal.red>=folga)
                        if (maisfolgado & (not estadispensado) & concorre & estafolgado):
                            folga = pessoal.red
                            idmilitar = pessoal.id
                            idcirculo = pessoal.idcirculo
                            nomeguerra = pessoal.nome_guerra
                            #print('a folga vermelha desse militar é: ',folga)

                if (folga>0):
                    #valores_previsao = [idmilitar, idcirculo, idEscala,
                    #    nomeguerra, folga, diaEscala]
                    insert_previsao=Previsao(idmilitar=idmilitar, idcirculo=idcirculo,
                        idescala=idEscala,nomeguerra=nomeguerra,folga=folga,
                        data=diaEscala, dia=diadaSemana(diaEscala), vermelha=escvermelha)
                    insert_previsao.save()
                    if(escalacorrida):
                        ControlarFolgas.objects.filter(idmilitar=idmilitar,
                        idcirculo=idcirculo, idescala=idEscala ).update(red=0, black=0)
                    else:
                        if (tipofolga=="red"):
                            #print('zerando a folga de: ', pessoal.nome_guerra)
                            ControlarFolgas.objects.filter(idmilitar=idmilitar,
                            idcirculo=idcirculo, idescala=idEscala ).update(red=0)
                        elif tipofolga == "black":
                            ControlarFolgas.objects.filter(idmilitar=idmilitar,
                            idcirculo=idcirculo, idescala=idEscala ).update(black=0)
                nrmilporescala -=1 # decrementa um ao nrmilporescala

            atualizarfolgas = ControlarFolgas.objects.filter(idcirculo=idcirculo,
                    idescala=idEscala)
            for atualizar in atualizarfolgas:
                #print(atualizar.idmilitar, atualizar.red, atualizar.black)
                red = atualizar.red
                black = atualizar.black
                sql_atualizarFolgas = ControlarFolgas.objects.filter(id=atualizar.id)
                if(escalacorrida):
                    sql_atualizarFolgas.update(red=red+1, black=black+1)
                else:
                    if (tipofolga=="red"):
                        sql_atualizarFolgas.update(red=red+1)

                    #ControlarFolgas.objects.filter(idcirculo=idcirculo,
                    #    idescala=idEscala ).update(red=pessoal.red+1)
                    else:
                        sql_atualizarFolgas.update(black=black+1)
                    #ControlarFolgas.objects.filter(idcirculo=idcirculo,
                    #    idescala=idEscala ).update(black+=1)
        diaEscala = diaEscala + timedelta(1)
        intervalo +=1
    return intervalo

def listar_previsao(request, pagina=1, nrporpagina=15, descricao=None, nomeguerra=None):
    teste = "SELECT b.id, a.id as idmilitar, a.posto,a.antiguidade,\
            b.nomeguerra, b.folga,b.data,b.dia, b.nomesubstituto,\
            b.vermelha, c.descricao FROM pessoal_militar a, previsao_previsao b,\
            core_escala c WHERE a.id=b.idmilitar AND c.id=b.idescala AND\
            a.idcirculo=b.idcirculo ORDER BY b.data, c.precedencia, b.idcirculo,\
            a.antiguidade"

    sqlmilitar="SELECT b.id, a.id as idmilitar, a.posto, a.antiguidade,\
    b.nomeguerra, b.folga, b.data, b.dia, b.nomesubstituto, b.vermelha,\
    c.descricao FROM pessoal_militar a, previsao_previsao b, core_escala c\
    WHERE a.id=b.idmilitar AND c.id=b.idescala AND a.idcirculo=b.idcirculo\
    "
    previsao_list=[]
    if (descricao!=None) & (descricao!=""):
        #criterio = descricao+'%'
        sqlmilitar += "AND c.descricao LIKE %s ORDER BY b.data,\
        c.precedencia, b.idcirculo, a.antiguidade"
        previsao_list = Militar.objects.raw(sqlmilitar,[descricao])
    elif (nomeguerra!=None) & (nomeguerra!=""):
        #criterio = '%'+nomeguerra+'%'
        sqlmilitar += "AND a.nome_guerra LIKE %s ORDER BY b.data,\
        c.precedencia, b.idcirculo, a.antiguidade"

        previsao_list = Militar.objects.raw(sqlmilitar,[nomeguerra])
    else:
        sqlmilitar +=" ORDER BY b.data, c.precedencia, b.idcirculo,\
        a.antiguidade"
        previsao_list = Militar.objects.raw(sqlmilitar)

    page = request.GET.get('page', pagina)

    paginator = Paginator(previsao_list, nrporpagina)
    try:
        previstos = paginator.page(page)
    except PageNotAnInteger:
        previstos = paginator.page(1)
    except EmptyPage:
        previstos = paginator.page(paginator.num_pages)
    
    return previstos

#@login_required
def previsao(request):
    podeSalvar = False

    inicio = datetime.today()
    final = inicio + timedelta(1)
    
    template_name = 'previsao.html'
    if request.method == 'POST':
        form = FormPrevisao(request.POST)
        if form.is_valid():
            dataInicio = form.cleaned_data['dataInicio']
            dataFim = form.cleaned_data['dataFim']
            if (dataInicio!=None) & (dataFim!=None):
                limparPrevisao()
                rodaprevisao(dataInicio,dataFim)
                print('passou aqui')
            return redirect('previsao:previsao')
    else:
        sql = Servicos.objects.last()
        if (sql!=None):
            inicio = sql.data + + timedelta(1)
            final = inicio + timedelta(1)
        form = FormPrevisao()

    previstos = listar_previsao(request)
    #podeSalvar = len(Previsao.objects.raw('SELECT DISTINCT(data), id FROM previsao_previsao GROUP BY data'))<=3
    podeSalvar = podeSalvarServico()
    context = {'form': form, 'previstos': previstos, 'podeSalvar': podeSalvar, 'inicio':inicio, 'final':final}

    return render(request, template_name, context)

def filtrar(request):
    template_name = 'previsao.html'
    if(request.method=='POST'):
        form = FormPrevisao(request.POST)
    else:
        form = FormPrevisao()

    filtroEscala = form['searchEscala'].value()
    filtroMilitar = form['searchMilitar'].value()
    previstos = listar_previsao(request,1,15,filtroEscala,filtroMilitar)

    context = {'form': form, 'previstos': previstos}

    return render(request, template_name, context)

@login_required
def listar_militares(request, idmilitar, idcirculo, idsubstituto=None):
    sqlMilitar = '''SELECT a.* FROM pessoal_militar a, core_designarescala b
    WHERE a.idcirculo=%s AND a.id=b.idmilitar AND a.id<>%s ORDER BY
    a.antiguidade'''

    if (idsubstituto != None):
        sqlMilitar = '''SELECT a.* FROM pessoal_militar a, core_designarescala b
        WHERE a.idcirculo=%s AND a.id=b.idmilitar AND a.id<>%s AND a.id<>%s ORDER BY
        a.antiguidade'''
        militares = Militar.objects.raw(sqlMilitar, [idcirculo, idmilitar, idsubstituto])
    else:
        militares = Militar.objects.raw(sqlMilitar, [idcirculo, idmilitar])

    return militares

@login_required
def trocar_servico(request, idprevisao, pagina):
    idprevisao=idprevisao
    queryset = Previsao.objects.filter(id=idprevisao)
    idcirculo = queryset[0].idcirculo
    idmilitar = queryset[0].idmilitar
    nomeguerra = queryset[0].nomeguerra
    idsubstituto = queryset[0].idsubstituto
    nomesubstituto = queryset[0].nomesubstituto
    data = queryset[0].data
    escalado = get_object_or_404(Militar, id=idmilitar, idcirculo=idcirculo)
    posto = escalado.posto

    dados = {'idmilitar': idmilitar, 'idcirculo': idcirculo,
    'nome_guerra': nomeguerra, 'posto': posto, 'idsubstituto': idsubstituto,
    'nomesubstituto': nomesubstituto, 'data': data}

    template_name = 'trocar_servicos.html'

    if request.method == 'POST':
        sqltrocar = Previsao.objects.filter(id=idprevisao)
        if (sqltrocar.count()>0):
            idsubstituto = request.POST.get('idsubstituto')
            nomesubstituto = Militar.objects.filter(id=idsubstituto)[0].nome_guerra
            sqltrocar.update(idsubstituto=idsubstituto,nomesubstituto=nomesubstituto)

            return redirect('previsao:previsao')
    else:
        form = MilitarEscaladoForm(dados)

    previstos = listar_previsao(request, pagina, 9)

    list_substituto = []
    if nomesubstituto!= None:
        substituto = Militar.objects.filter(id=idsubstituto).last()
        list_substituto={'id':idsubstituto,'nome':nomesubstituto, 'posto':substituto.get_posto_display()}
        militares = listar_militares(request, idmilitar,idcirculo,substituto.id)
    else:
        list_substituto={'id':"",'nome':"Selecione um militar"}

        militares = listar_militares(request, idmilitar,idcirculo)



    context = {'form': form, 'militares': militares,
    'previstos': previstos, 'substituto': list_substituto}

    return render(request, template_name, context)

#função que gera pdf
def GeneratePDF(request):
    #para gerar pdf
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.colors import black, red
    from django.http import FileResponse


    sqlmilitar = "SELECT a.id, a.posto,a.antiguidade,b.nomeguerra,\
    b.folga,b.data,b.dia, b.folga,c.descricao FROM pessoal_militar a, \
    previsao_previsao b, core_escala c WHERE a.id=b.idmilitar AND \
    c.id=b.idescala AND a.idcirculo=b.idcirculo \
    ORDER BY b.data, c.precedencia, b.idcirculo, a.antiguidade"

    previsao_list = Militar.objects.raw(sqlmilitar)
    #previsao_list = Previsao.objects.raw(sqlmilitar)
    data = previsao_list[0].data
    dia = previsao_list[0].dia
    fontColor = "black"
    if vermelha(data):
        fontColor="red"

    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    #p.drawString(100, 100, "Hello world.")

    p.setTitle('Previsão da Escala de Serviço')
    p.setFont("Helvetica-Bold", 14)
    p.drawString(245,780, 'Previsão da Escala de Serviço')
    subtitle = 'Para o dia: '+data.strftime("%d/%m/%Y")+' - '+dia
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(fontColor)
    p.drawString(45,760, subtitle)
    p.setFillColor(black)
    p.setFont("Helvetica", 12)
    #pdf.drawString(45,750, 'Escala             Posto/Grad          Militar')
    x = 750
    for escalado in previsao_list:
        if(escalado.data!=data):
            x -=20
            data = escalado.data
            dia = escalado.dia
            fontColor = "black"
            if vermelha(data):
                fontColor="red"

            subtitle = 'Para o dia: '+data.strftime("%d/%m/%Y")+' - '+dia
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(fontColor)
            p.drawString(45,x, subtitle)
            p.setFont("Helvetica", 12)
            p.setFillColor(black)
            x -=5

        if x<40:
            x = 750
            #adiciona uma nova página para continuar listando a escala
            p.showPage()
            p.setFont("Helvetica-Bold", 14)
            p.drawString(245,780, 'Previsão da Escala de Serviço')
            subtitle = 'Para o dia: '+data.strftime("%d/%m/%Y")+' - '+dia
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(fontColor)
            p.drawString(45,760, subtitle)
            p.setFont("Helvetica", 12)
            p.setFillColor(black)
            #pdf.drawString(45,750, 'Escala             Posto/Grad          Militar')
        
        x -= 15
        p.drawString(47,x, '{}: {} - {}'.
        format(escalado.descricao, getPostoGraduacao(escalado.posto), escalado.nomeguerra))

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename='escalaSV.pdf')