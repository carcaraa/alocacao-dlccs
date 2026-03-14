# Alocação Ótima de Dispositivos Limitadores de Corrente via Algoritmo Genético Multiobjetivo

## Descrição

Implementação de um algoritmo genético multiobjetivo baseado no NSGA-II para alocação ótima de Dispositivos Limitadores de Corrente (DLCs) em sistemas elétricos de potência. O algoritmo busca minimizar simultaneamente as correntes de curto-circuito trifásico e o custo de instalação dos dispositivos.

Trabalho desenvolvido como Trabalho de Conclusão de Curso (TCC) em 2019.

## Metodologia

O sistema elétrico é modelado a partir da matriz de impedância de barra (Zbarra), obtida pela inversão da matriz de admitância (Ybarra). A análise de curto-circuito trifásico é realizada para todas as barras do sistema, calculando correntes de falta, tensões nas barras e correntes nas linhas.

A otimização é conduzida por um algoritmo genético com as seguintes características:

- **Codificação:** Binária, com 12 bits por indivíduo (3 grupos de 4 bits), cada grupo representando um DLC candidato em uma barra específica.
- **Funções objetivo:**
  - f1: Minimização da corrente total de curto-circuito.
  - f2: Minimização do custo total dos DLCs.
- **Seleção:** Torneio binário baseado em frente de dominância e distância de agrupamento.
- **Cruzamento:** Uniforme, utilizando máscara binária aleatória.
- **Mutação:** Bit-flip em indivíduo selecionado aleatoriamente.
- **Frentes de Pareto:** Classificação por não-dominância.
- **Distância de agrupamento:** Preservação da diversidade na fronteira de Pareto.

## Sistema Teste

Sistema IEEE 15 barras, com dados de impedância e topologia definidos no arquivo `15BusTestSystems.xlsx`.

## Estrutura do Repositório

```
alocacao-dlcs/
├── nsgaii.py                # Código principal do algoritmo genético
├── 15BusTestSystems.xlsx    # Dados do sistema elétrico (linhas, impedâncias, base)
└── README.md
```

## Dependências

- Python 3.x
- NumPy
- Pandas
- Matplotlib
- pythonds

## Execução

```bash
pip install numpy pandas matplotlib pythonds
python nsgaii.py
```

## Saídas

- `saida.xlsx`: Impedâncias dos DLCs alocados para cada indivíduo da população final.
- `final.xlsx`: Soluções filtradas pelas restrições do problema (f1 > 30, 0 < f2 < 80).
- Gráfico de dispersão da fronteira de Pareto (f1 × f2).

## Referências

- Deb, K. et al. *A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II*. IEEE Transactions on Evolutionary Computation, 2002.
