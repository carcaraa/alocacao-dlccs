# -*- coding: utf-8 -*-
"""
Algoritmo Genético para alocação de DLCs
Dispositivos Limitadores de Corrente em sistema IEEE 9 barras
"""

# Preparação do ambiente

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as la
from pythonds.basic.stack import Stack

pd.plotting.register_matplotlib_converters()
print('Setup complete!')


# Funções auxiliares

def importar_dados(sheet, ax=0):
    """
    Importação de dados de arquivo formato .xlsx

    sheet: Planilha a ser selecionada
    """
    dados = pd.read_excel('15BusTestSystems.xlsx', sheet_name=f'{sheet}')
    dados = np.delete(dados.values, (0), axis=ax)
    return dados


def show(func, und='pu', dim=1):
    """
    Exibir resultados armazenados na função func

    func: dados a serem plotados

    und: unidade adotada (pu, A, V, ...)

    dim: quantidade de colunas de func
    """
    num = 0
    if dim > 1:
        for linha in func:
            num = 0
            for column in linha:
                num += 1
                if num < len(func):
                    print(
                        f'{np.absolute(column): .4f} |_ {np.angle(column) * 180 / np.pi: .4f}° {und}', end='\t')
                elif num == len(func):
                    print(
                        f'{np.absolute(column): .4f} |_ {np.angle(column) * 180 / np.pi: .4f}° {und}')
        print('')
    else:
        for linha in func:
            num += 1
            print(
                f'Barra {num}:\t{np.absolute(linha): .4f} |_{np.angle(linha) * 180 / np.pi: .4f}° {und}')


def show_dict(func):
    num = 1
    for dic in func:
        print(f'\nCurto na barra {num}:\n')
        for element, value in zip(dic.keys(), dic.values()):
            print(f'{element}:\t {value * 100: .4f}')
        num += 1


# Obtenção dos dados do problema

linhas = (importar_dados('Linhas')).tolist()
base = importar_dados('Base', 1)


# Criação do Sistema
# Objeto Sistema representará o sistema elétrico a ser trabalhado,
# bem como trará as funções aplicáveis aos mesmos.

class Sistema:

    def __init__(self, linhas, base):
        self.linhas = linhas
        self.base = base

    def zbarra(self):
        for i in range(len(self.linhas)):
            self.linhas[i][2] = complex(self.linhas[i][2])

        # Barras presentes no sistema
        self.barras = []
        for i in range(len(self.linhas)):
            self.barras.append(self.linhas[i][0])
            self.barras.append(self.linhas[i][1])

        self.barras = sorted(list(set(self.barras)))
        self.barras.pop(0)

        # Montagem da matriz YBARRA

        Y = np.zeros((len(self.barras), len(self.barras)), dtype=complex)

        for row, barra in enumerate(self.barras):
            for linha in self.linhas:
                if barra in linha:
                    Y[row][row] += 1 / linha[2]
                if 'N0' not in linha:
                    Y[self.barras.index(linha[0])][self.barras.index(
                        linha[1])] = - 1 / linha[2]
                    Y[self.barras.index(linha[1])][self.barras.index(
                        linha[0])] = - 1 / linha[2]

        # Montagem da Matriz Z_BARRA

        self.Z = la.inv(Y)

    # Curto Trifasico
    def curto_trifasico(self):
        """
        Cálculo do curto-circuito trifásico       
        Correntes: 
        """
        i_cc = np.zeros(len(self.barras), dtype=complex)
        for i in range(len(self.barras)):
            i_cc[i] = -1 / self.Z[i][i]

        # Tensões nas barras
        v = np.zeros((len(self.barras), len(self.barras)), dtype=complex)
        for index in range(len(self.barras)):
            for index2 in range(len(self.barras)):
                v[index2][index] = 1 - self.Z[index2][index] / self.Z[index][index]

        # Correntes nas linhas
        correntes = []
        for i in range(len(self.barras)):
            i_temp = {}
            for linha in self.linhas:
                if 'N0' in linha:
                    pass
                else:
                    i1 = self.barras.index(linha[0])
                    i2 = self.barras.index(linha[1])
                    i_temp[f'{linha[0]} - {linha[1]}'] = (
                        (self.Z[i2][i]-self.Z[i1][i])/(self.Z[i][i]))*(1/(linha[2]))
            correntes.append(i_temp)

        return i_cc, v, correntes


# Sistema Z
# Sistema IEEE 9 barras original

Z = Sistema(linhas, base)
Z.zbarra()
i_cc, v, correntes = Z.curto_trifasico()

soumteste = 0
for i in i_cc:
    soumteste += i
print(f'Total corrente de curto (sistema original):{soumteste}\n')


# DLCs
# Dispositivos a serem inseridos no sistema visando mitigar as correntes de curto

dlcs = pd.DataFrame([[0, 16.8, 20.2, 21.5, 23.5, 25.5, 26.9, 30.2, 33.6, 38.4, 43.1, 47.6],
                      [0, 5*1j, 10*1j, 12*1j, 15*1j, 18*1j, 20*1j, 25*1j, 30*1j, 37*1j, 43*1j, 49*1j]/Z.base[2]], 
        columns=['0000','0001','0010','0011','0100','0101','0110','0111', '1000', '1001', '1010', '1011'])


#_________________________Algoritmo Genético_________________________#


# Função auxiliar de conversão de base

def baseConverter(decNumber,base):
    digits = "0123456789ABCDEF"

    remstack = Stack()

    while decNumber > 0:
        rem = decNumber % base
        remstack.push(rem)
        decNumber = decNumber // base

    newString = ""
    while not remstack.isEmpty():
        newString = newString + digits[remstack.pop()]
    while len(newString) < 4:
        newString = '0' + newString
    return newString


# Função criadora de indivíduos
# Cada indivíduo é composto por uma cadeia de 12 bits, divididos em 3 grupos de 4 bits.
# Cada grupo corresponde a uma determinada barra na qual pode ser inserido um DLC.
# A cada cadeia de 4 bits está associado um DLC da variável dlcs.

def novo_individuo():
    """
    Cria um indivíduo formado por 12 bits XXXXYYYYZZZZ, onde:
    XXXX: DLC da barra 1,
    YYYY: DLC da barra 2,
    ZZZZ: DLC da barra 3.
    """
    ind = ''
    for i in range(3):
        individuo = np.random.randint(11)
        temp = baseConverter(int(individuo),2)
        ind+=temp
    
    return ind


# Função de descriptografia
# A partir de um dado individuo, obtém informações acerca de custo e impedância do dlc.

def barras_info(individuo, indice):
    """
    Extrai informações a partir dos bits indivíduo:
    0 - Extrai o custo do DLC;
    1 - Extrai a impedância do DLC;
    """
    b_imp = []
    for i in range(3):
        i = 4*i
        b_imp.append(dlcs.loc[indice, individuo[i:i+4]])
    return np.array(b_imp)


# População
# Gera a população inicial a ser utilizada como ponto de partida do algoritmo genético.

def populacao(size):
    """
    Gera uma população com size indivíduos.
    """
    A = []
    for i in range(size):
        A.append(novo_individuo())
    A = np.array(A)
    return A


# Linhas atualizadas
# Responsável por gerar nova matriz com informações atualizadas das linhas do sistema.

def atualizar_linhas(populacao):
    """
    Atualiza a matriz Zbarra
    """
    linhas_temp = np.array(Z.linhas)
    temp = []
    for i in range(len(Z.linhas)):
        temp.append([linhas_temp[i,0], linhas_temp[i,1], complex(linhas_temp[i,2])])

    for i in range(-3, 0, 1):
        temp[i][2]+=populacao[i]
    return temp


# Sistemas teste

def sistemas_teste(populacao, base, size):
    Z_temp = np.empty(size, dtype=Sistema)
    custos = np.empty([size], dtype=complex)
    for i, individuo_i in enumerate(populacao):
        custos[i] = np.sum(barras_info(individuo_i, 0))
        Z_temp[i] = Sistema(atualizar_linhas(barras_info(individuo_i, 1)), base)
        Z_temp[i].zbarra()
    return Z_temp, custos


# Função fitness
# Retorna os valores atualizados das funções objetivo do problema.

def fitness(Z, custos, size):
    # f1:
    f1 = np.empty(size, dtype=complex)
    for i, sistema in enumerate(Z):
        i_cc_temp, v_temp, correntes_temp = sistema.curto_trifasico()
        f1[i] = np.sum(i_cc_temp)
    # f2:
    f2 = custos
    return f1, f2


# Determinar as frentes de não-dominância

def pareto(f1, f2):
    domination_count = np.zeros([1,len(f1)])
    elementos = []
    for i in range(len(f1)):
        elementos.append([f1[i], f2[i]])
    
    for i1, fx in enumerate(elementos):
        for i2, fy in enumerate(elementos):
            if i1 != i2:
                if (fx[0] <= fy[0] and fx[1] < fy[1]) or (fx[0] < fy[0] and fx[1] <= fy[1]):
                    domination_count[0, i2] += 1

    return domination_count, elementos


# Plotagem das frentes de não dominância

def plotagem(data):
    for i in data:
        plt.scatter(x=i['f1'], y=i['f2'])
    plt.show()


# Cálculo da distância de agrupamento

def dag(individuos, count, populacao):  
    individuos['dag'] = np.zeros([1, (individuos['f1']).shape[0]])[0]

    P = [sorted(np.abs(individuos['f1'])), sorted(np.abs(individuos['f2']))]

    for i, j in enumerate(P[0]):
        index = np.where(np.abs(individuos['f1']) == j)[0][0]
        if (i == 0) or (i == len(P[0])-1):    
            individuos['dag'][index] = individuos['dag'][index] + 10000
        else:
            individuos['dag'][index] = individuos['dag'][index] + (P[0][i+1]-P[0][i-1])/(max(P[0])-min(P[0]))

    for i, j in enumerate(P[1]):
        index = np.where(np.abs(individuos['f2']) == j)[0][0]
        if (i == 0) or (i == len(P[1])-1):    
            individuos['dag'][index] = individuos['dag'][index] + 10000
        else:
            individuos['dag'][index] = individuos['dag'][index] + (P[1][i+1]-P[1][i-1])/(max(P[1])-min(P[1]))
    
    frente = []
    novos = list(set(sorted(count[0])))
    for i in count[0]:
        frente.append(f'F{np.where(novos==i)[0][0]}')
    individuos['frentes'] = frente

    individuos['populacao'] = populacao

    return individuos


# Seleção de pais

def selecao_pais(individuos, size):    
    frentes = []
    for i in individuos['frentes']:
        if i not in frentes:
            frentes.append(int(i[1:]))
    frentes = list(set(frentes))
    frentes.sort()

    pais = []
    for i in range(int(len(populacao)/2)):
        pais_temp = []
        index = []
        for j in range(2):
            index.append(np.random.randint(size))
            pais_temp.append(individuos['frentes'][index[-1]])
        if int(pais_temp[0][1:]) == int(pais_temp[1][1:]):
            if individuos['dag'][index[0]] > individuos['dag'][index[1]]:
                pais.append(individuos['populacao'][index[0]])
            else:
                pais.append(individuos['populacao'][index[1]])
        else:
            x1 = int(pais_temp[0][1:])
            x2 = int(pais_temp[1][1:])
            if x1 < x2:
                pais.append(individuos['populacao'][index[0]])
            else:
                pais.append(individuos['populacao'][index[1]])
    return pais


# Cruzamento

def cruzamento(pais):
    filhos = []
    for a in np.linspace(0,int(size/2),int(size/4),endpoint=False,dtype=int):
        mascara = novo_individuo()
        descendente1 = ''
        for i, j in enumerate(mascara):
            if j == '1':
                descendente1 += pais[a][i]
            else:
                descendente1 += pais[a+1][i]
        filhos.append(descendente1)
        descendente2 = ''
        for i, j in enumerate(mascara):
            if j == '1':
                descendente2 += pais[a+1][i]
            else:
                descendente2 += pais[a][i]
        filhos.append(descendente2)
    return filhos


# Mutação

def mutacao(individuos, size):
    descendentes = []
    for i in range(int(len(individuos)/2)):
        desc_temp = ''
        desc_temp_list = []
        selecao = np.random.randint(size)
        bit = int(np.random.randint(12))
        for j in individuos['populacao'][selecao]:
            desc_temp_list.append(j)
        if desc_temp_list[bit] == '1':
            desc_temp_list[bit] = '0'
        else:
            desc_temp_list[bit] = '1'
        for z in desc_temp_list:
            desc_temp += z
        descendentes.append(desc_temp)
    return descendentes


# Recontagem

def recontagem(individuos):
    final = []
    for individuo in individuos:
        atualizado = ''
        atualizado_list = []
        restos = []
        index = []
        
        for i in range(3):
            a = i
            a = 4*a
            temp = individuo[a:a+4]

            if int(temp) > 1011:
                z = 4
                dec = 0
                for j in temp:
                    dec += int(j)*2**(z-1)
                    z -= 1
                resto = dec - 11
                resto_bin = str(baseConverter(resto, 2))
                resto_bin_str = str(resto_bin)
                if len(str(resto_bin)) < 4:
                    while len(str(resto_bin)) < 4:
                        resto_bin_str = '0' +resto_bin_str
                resto_bin = resto_bin_str
                index.append(i)
                restos.append(resto_bin)
        b = 0
        for i in range(3):
            if i in index:
                for j in range(4):
                    atualizado_list.append(restos[b][j])
                b += 1
            else:
                i = 4*i
                for j in range(4):
                    atualizado_list.append(individuo[i+j])
        for i in atualizado_list:
            atualizado += i
        final.append(atualizado)
    return final


# Algoritmo genético
# Inicialização da população inicial de tamanho -> size

size = 100
populacao_inicial = populacao(size)
populacao = populacao_inicial
iteracoes = 20

for q in range(iteracoes):
    
    for v in range(2):
        Z_populacao, custos = sistemas_teste(populacao, base, (v+1)*size)
        f1, f2 = fitness(Z_populacao, custos, (v+1)*size)
        count, elementos = pareto(f1,f2)
        individuos = pd.DataFrame({'f1':np.abs(np.array(elementos)[:,0]), 'f2':np.abs(np.array(elementos)[:,1])})
        individuos = dag(individuos, count, populacao)

        if v == 0:
            pais = selecao_pais(individuos, size)
            filhos = cruzamento(pais)
            novos_filhos = mutacao(individuos, size)
            filhos.extend(novos_filhos)
            descendentes = recontagem(filhos)
            populacao = list(populacao)
            populacao.extend(descendentes)
        else:
            populacaof = individuos.sort_values(['frentes'])[:size]
            populacao = []
            for individuo in populacaof['populacao']:
                populacao.append(individuo)


# Saída de resultados

saida = []
for i in populacaof['populacao']:
    saida.append(barras_info(i, 1))

# Restricoes
final = []
for i in populacaof.values:
    if (i[0] > 30 and i[1] < 80) and i[1] > 0 :
        final.append([i[0], i[1], i[4]])

df = pd.DataFrame(saida)
df.to_excel('saida.xlsx')
df = pd.DataFrame(final)
df.to_excel('final.xlsx')

final_novo = pd.DataFrame(final)
print(final_novo)
plt.scatter(final_novo[0], final_novo[1])
plt.show()racoes = 20

for q in range(iteracoes):
    
    for v i# -*- coding: utf-8 -*-
"""
Algoritmo Genético para alocação de DLCs
Dispositivos Limitadores de Corrente em sistema IEEE 9 barras
"""

# Preparação do ambiente

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as la
from pythonds.basic.stack import Stack

pd.plotting.register_matplotlib_converters()
print('Setup complete!')


# Funções auxiliares

def importar_dados(sheet, ax=0):
    """
    Importação de dados de arquivo formato .xlsx

    sheet: Planilha a ser selecionada
    """
    dados = pd.read_excel('15BusTestSystems.xlsx', sheet_name=f'{sheet}')
    dados = np.delete(dados.values, (0), axis=ax)
    return dados


def show(func, und='pu', dim=1):
    """
    Exibir resultados armazenados na função func

    func: dados a serem plotados

    und: unidade adotada (pu, A, V, ...)

    dim: quantidade de colunas de func
    """
    num = 0
    if dim > 1:
        for linha in func:
            num = 0
            for column in linha:
                num += 1
                if num < len(func):
                    print(
                        f'{np.absolute(column): .4f} |_ {np.angle(column) * 180 / np.pi: .4f}° {und}', end='\t')
                elif num == len(func):
                    print(
                        f'{np.absolute(column): .4f} |_ {np.angle(column) * 180 / np.pi: .4f}° {und}')
        print('')
    else:
        for linha in func:
            num += 1
            print(
                f'Barra {num}:\t{np.absolute(linha): .4f} |_{np.angle(linha) * 180 / np.pi: .4f}° {und}')


def show_dict(func):
    num = 1
    for dic in func:
        print(f'\nCurto na barra {num}:\n')
        for element, value in zip(dic.keys(), dic.values()):
            print(f'{element}:\t {value * 100: .4f}')
        num += 1


# Obtenção dos dados do problema

linhas = (importar_dados('Linhas')).tolist()
base = importar_dados('Base', 1)


# Criação do Sistema
# Objeto Sistema representará o sistema elétrico a ser trabalhado,
# bem como trará as funções aplicáveis aos mesmos.

class Sistema:

    def __init__(self, linhas, base):
        self.linhas = linhas
        self.base = base

    def zbarra(self):
        for i in range(len(self.linhas)):
            self.linhas[i][2] = complex(self.linhas[i][2])

        # Barras presentes no sistema
        self.barras = []
        for i in range(len(self.linhas)):
            self.barras.append(self.linhas[i][0])
            self.barras.append(self.linhas[i][1])

        self.barras = sorted(list(set(self.barras)))
        self.barras.pop(0)

        # Montagem da matriz YBARRA

        Y = np.zeros((len(self.barras), len(self.barras)), dtype=complex)

        for row, barra in enumerate(self.barras):
            for linha in self.linhas:
                if barra in linha:
                    Y[row][row] += 1 / linha[2]
                if 'N0' not in linha:
                    Y[self.barras.index(linha[0])][self.barras.index(
                        linha[1])] = - 1 / linha[2]
                    Y[self.barras.index(linha[1])][self.barras.index(
                        linha[0])] = - 1 / linha[2]

        # Montagem da Matriz Z_BARRA

        self.Z = la.inv(Y)

    # Curto Trifasico
    def curto_trifasico(self):
        """
        Cálculo do curto-circuito trifásico       
        Correntes: 
        """
        i_cc = np.zeros(len(self.barras), dtype=complex)
        for i in range(len(self.barras)):
            i_cc[i] = -1 / self.Z[i][i]

        # Tensões nas barras
        v = np.zeros((len(self.barras), len(self.barras)), dtype=complex)
        for index in range(len(self.barras)):
            for index2 in range(len(self.barras)):
                v[index2][index] = 1 - self.Z[index2][index] / self.Z[index][index]

        # Correntes nas linhas
        correntes = []
        for i in range(len(self.barras)):
            i_temp = {}
            for linha in self.linhas:
                if 'N0' in linha:
                    pass
                else:
                    i1 = self.barras.index(linha[0])
                    i2 = self.barras.index(linha[1])
                    i_temp[f'{linha[0]} - {linha[1]}'] = (
                        (self.Z[i2][i]-self.Z[i1][i])/(self.Z[i][i]))*(1/(linha[2]))
            correntes.append(i_temp)

        return i_cc, v, correntes


# Sistema Z
# Sistema IEEE 9 barras original

Z = Sistema(linhas, base)
Z.zbarra()
i_cc, v, correntes = Z.curto_trifasico()

soumteste = 0
for i in i_cc:
    soumteste += i
print(f'Total corrente de curto (sistema original):{soumteste}\n')


# DLCs
# Dispositivos a serem inseridos no sistema visando mitigar as correntes de curto

dlcs = pd.DataFrame([[0, 16.8, 20.2, 21.5, 23.5, 25.5, 26.9, 30.2, 33.6, 38.4, 43.1, 47.6],
                      [0, 5*1j, 10*1j, 12*1j, 15*1j, 18*1j, 20*1j, 25*1j, 30*1j, 37*1j, 43*1j, 49*1j]/Z.base[2]], 
        columns=['0000','0001','0010','0011','0100','0101','0110','0111', '1000', '1001', '1010', '1011'])


#_________________________Algoritmo Genético_________________________#


# Função auxiliar de conversão de base

def baseConverter(decNumber,base):
    digits = "0123456789ABCDEF"

    remstack = Stack()

    while decNumber > 0:
        rem = decNumber % base
        remstack.push(rem)
        decNumber = decNumber // base

    newString = ""
    while not remstack.isEmpty():
        newString = newString + digits[remstack.pop()]
    while len(newString) < 4:
        newString = '0' + newString
    return newString


# Função criadora de indivíduos
# Cada indivíduo é composto por uma cadeia de 12 bits, divididos em 3 grupos de 4 bits.
# Cada grupo corresponde a uma determinada barra na qual pode ser inserido um DLC.
# A cada cadeia de 4 bits está associado um DLC da variável dlcs.

def novo_individuo():
    """
    Cria um indivíduo formado por 12 bits XXXXYYYYZZZZ, onde:
    XXXX: DLC da barra 1,
    YYYY: DLC da barra 2,
    ZZZZ: DLC da barra 3.
    """
    ind = ''
    for i in range(3):
        individuo = np.random.randint(11)
        temp = baseConverter(int(individuo),2)
        ind+=temp
    
    return ind


# Função de descriptografia
# A partir de um dado individuo, obtém informações acerca de custo e impedância do dlc.

def barras_info(individuo, indice):
    """
    Extrai informações a partir dos bits indivíduo:
    0 - Extrai o custo do DLC;
    1 - Extrai a impedância do DLC;
    """
    b_imp = []
    for i in range(3):
        i = 4*i
        b_imp.append(dlcs.loc[indice, individuo[i:i+4]])
    return np.array(b_imp)


# População
# Gera a população inicial a ser utilizada como ponto de partida do algoritmo genético.

def populacao(size):
    """
    Gera uma população com size indivíduos.
    """
    A = []
    for i in range(size):
        A.append(novo_individuo())
    A = np.array(A)
    return A


# Linhas atualizadas
# Responsável por gerar nova matriz com informações atualizadas das linhas do sistema.

def atualizar_linhas(populacao):
    """
    Atualiza a matriz Zbarra
    """
    linhas_temp = np.array(Z.linhas)
    temp = []
    for i in range(len(Z.linhas)):
        temp.append([linhas_temp[i,0], linhas_temp[i,1], complex(linhas_temp[i,2])])

    for i in range(-3, 0, 1):
        temp[i][2]+=populacao[i]
    return temp


# Sistemas teste

def sistemas_teste(populacao, base, size):
    Z_temp = np.empty(size, dtype=Sistema)
    custos = np.empty([size], dtype=complex)
    for i, individuo_i in enumerate(populacao):
        custos[i] = np.sum(barras_info(individuo_i, 0))
        Z_temp[i] = Sistema(atualizar_linhas(barras_info(individuo_i, 1)), base)
        Z_temp[i].zbarra()
    return Z_temp, custos


# Função fitness
# Retorna os valores atualizados das funções objetivo do problema.

def fitness(Z, custos, size):
    # f1:
    f1 = np.empty(size, dtype=complex)
    for i, sistema in enumerate(Z):
        i_cc_temp, v_temp, correntes_temp = sistema.curto_trifasico()
        f1[i] = np.sum(i_cc_temp)
    # f2:
    f2 = custos
    return f1, f2


# Determinar as frentes de não-dominância

def pareto(f1, f2):
    domination_count = np.zeros([1,len(f1)])
    elementos = []
    for i in range(len(f1)):
        elementos.append([f1[i], f2[i]])
    
    for i1, fx in enumerate(elementos):
        for i2, fy in enumerate(elementos):
            if i1 != i2:
                if (fx[0] <= fy[0] and fx[1] < fy[1]) or (fx[0] < fy[0] and fx[1] <= fy[1]):
                    domination_count[0, i2] += 1

    return domination_count, elementos


# Plotagem das frentes de não dominância

def plotagem(data):
    for i in data:
        plt.scatter(x=i['f1'], y=i['f2'])
    plt.show()


# Cálculo da distância de agrupamento

def dag(individuos, count, populacao):  
    individuos['dag'] = np.zeros([1, (individuos['f1']).shape[0]])[0]

    P = [sorted(np.abs(individuos['f1'])), sorted(np.abs(individuos['f2']))]

    for i, j in enumerate(P[0]):
        index = np.where(np.abs(individuos['f1']) == j)[0][0]
        if (i == 0) or (i == len(P[0])-1):    
            individuos['dag'][index] = individuos['dag'][index] + 10000
        else:
            individuos['dag'][index] = individuos['dag'][index] + (P[0][i+1]-P[0][i-1])/(max(P[0])-min(P[0]))

    for i, j in enumerate(P[1]):
        index = np.where(np.abs(individuos['f2']) == j)[0][0]
        if (i == 0) or (i == len(P[1])-1):    
            individuos['dag'][index] = individuos['dag'][index] + 10000
        else:
            individuos['dag'][index] = individuos['dag'][index] + (P[1][i+1]-P[1][i-1])/(max(P[1])-min(P[1]))
    
    frente = []
    novos = list(set(sorted(count[0])))
    for i in count[0]:
        frente.append(f'F{np.where(novos==i)[0][0]}')
    individuos['frentes'] = frente

    individuos['populacao'] = populacao

    return individuos


# Seleção de pais

def selecao_pais(individuos, size):    
    frentes = []
    for i in individuos['frentes']:
        if i not in frentes:
            frentes.append(int(i[1:]))
    frentes = list(set(frentes))
    frentes.sort()

    pais = []
    for i in range(int(len(populacao)/2)):
        pais_temp = []
        index = []
        for j in range(2):
            index.append(np.random.randint(size))
            pais_temp.append(individuos['frentes'][index[-1]])
        if int(pais_temp[0][1:]) == int(pais_temp[1][1:]):
            if individuos['dag'][index[0]] > individuos['dag'][index[1]]:
                pais.append(individuos['populacao'][index[0]])
            else:
                pais.append(individuos['populacao'][index[1]])
        else:
            x1 = int(pais_temp[0][1:])
            x2 = int(pais_temp[1][1:])
            if x1 < x2:
                pais.append(individuos['populacao'][index[0]])
            else:
                pais.append(individuos['populacao'][index[1]])
    return pais


# Cruzamento

def cruzamento(pais):
    filhos = []
    for a in np.linspace(0,int(size/2),int(size/4),endpoint=False,dtype=int):
        mascara = novo_individuo()
        descendente1 = ''
        for i, j in enumerate(mascara):
            if j == '1':
                descendente1 += pais[a][i]
            else:
                descendente1 += pais[a+1][i]
        filhos.append(descendente1)
        descendente2 = ''
        for i, j in enumerate(mascara):
            if j == '1':
                descendente2 += pais[a+1][i]
            else:
                descendente2 += pais[a][i]
        filhos.append(descendente2)
    return filhos


# Mutação

def mutacao(individuos, size):
    descendentes = []
    for i in range(int(len(individuos)/2)):
        desc_temp = ''
        desc_temp_list = []
        selecao = np.random.randint(size)
        bit = int(np.random.randint(12))
        for j in individuos['populacao'][selecao]:
            desc_temp_list.append(j)
        if desc_temp_list[bit] == '1':
            desc_temp_list[bit] = '0'
        else:
            desc_temp_list[bit] = '1'
        for z in desc_temp_list:
            desc_temp += z
        descendentes.append(desc_temp)
    return descendentes


# Recontagem

def recontagem(individuos):
    final = []
    for individuo in individuos:
        atualizado = ''
        atualizado_list = []
        restos = []
        index = []
        
        for i in range(3):
            a = i
            a = 4*a
            temp = individuo[a:a+4]

            if int(temp) > 1011:
                z = 4
                dec = 0
                for j in temp:
                    dec += int(j)*2**(z-1)
                    z -= 1
                resto = dec - 11
                resto_bin = str(baseConverter(resto, 2))
                resto_bin_str = str(resto_bin)
                if len(str(resto_bin)) < 4:
                    while len(str(resto_bin)) < 4:
                        resto_bin_str = '0' +resto_bin_str
                resto_bin = resto_bin_str
                index.append(i)
                restos.append(resto_bin)
        b = 0
        for i in range(3):
            if i in index:
                for j in range(4):
                    atualizado_list.append(restos[b][j])
                b += 1
            else:
                i = 4*i
                for j in range(4):
                    atualizado_list.append(individuo[i+j])
        for i in atualizado_list:
            atualizado += i
        final.append(atualizado)
    return final


# Algoritmo genético
# Inicialização da população inicial de tamanho -> size

size = 100
populacao_inicial = populacao(size)
populacao = populacao_inicial
iteracoes = 20

for q in range(iteracoes):
    
    for v in range(2):
        Z_populacao, custos = sistemas_teste(populacao, base, (v+1)*size)
        f1, f2 = fitness(Z_populacao, custos, (v+1)*size)
        count, elementos = pareto(f1,f2)
        individuos = pd.DataFrame({'f1':np.abs(np.array(elementos)[:,0]), 'f2':np.abs(np.array(elementos)[:,1])})
        individuos = dag(individuos, count, populacao)

        if v == 0:
            pais = selecao_pais(individuos, size)
            filhos = cruzamento(pais)
            novos_filhos = mutacao(individuos, size)
            filhos.extend(novos_filhos)
            descendentes = recontagem(filhos)
            populacao = list(populacao)
            populacao.extend(descendentes)
        else:
            populacaof = individuos.sort_values(['frentes'])[:size]
            populacao = []
            for individuo in populacaof['populacao']:
                populacao.append(individuo)


# Saída de resultados

saida = []
for i in populacaof['populacao']:
    saida.append(barras_info(i, 1))

# Restricoes
final = []
for i in populacaof.values:
    if (i[0] > 30 and i[1] < 80) and i[1] > 0 :
        final.append([i[0], i[1], i[4]])

df = pd.DataFrame(saida)
df.to_excel('saida.xlsx')
df = pd.DataFrame(final)
df.to_excel('final.xlsx')

final_novo = pd.DataFrame(final)
print(final_novo)
plt.scatter(final_novo[0], final_novo[1])
plt.show()