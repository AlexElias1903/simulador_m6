import argparse
import heapq
import yaml 

a = 1664525
c = 101390422
M = 2**32
seeds = [1]

class Random:
    def __init__(self):
        self.current_index = 0
        
    def random(self):
        if (self.current_index >= len(seeds)):
            self.current_index = 0
        x = seeds[self.current_index]
        seeds[self.current_index] = (a * x + c) % M
        value = seeds[self.current_index] / M
        self.current_index += 1
        return value
    
    def uniform(self, a, b):
        return a + (b - a) * self.random()
        

random = Random()
class Fila:
    def __init__(self, id, servidores, capacidade, intervalo_chegada, intervalo_servico, roteamento=None):
        self.id = id
        self.servidores = servidores
        self.capacidade = capacidade
        self.intervalo_chegada = intervalo_chegada
        self.intervalo_servico = intervalo_servico
        self.roteamento = roteamento if roteamento else {}
        self.clientes = 0
        self.perdas = 0
        self.tempos_acumulados = [0.0 for _ in range(capacidade + 1)]
        self.ultimo_evento_tempo = 0.0

    def atualizar_tempos_acumulados(self, tempo_atual):
        tempo_desde_ultimo_evento = tempo_atual - self.ultimo_evento_tempo
        self.tempos_acumulados[self.clientes] += tempo_desde_ultimo_evento
        self.ultimo_evento_tempo = tempo_atual

    def processar_chegada(self, tempo_atual, escalonador):
        self.atualizar_tempos_acumulados(tempo_atual)
        if self.clientes < self.capacidade:
            self.clientes += 1
            if self.clientes <= self.servidores:
                tempo_servico = tempo_atual + random.uniform(*self.intervalo_servico)
                escalonador.adicionar_evento(('SAIDA', tempo_servico, self))
        else:
            self.perdas += 1

    def processar_saida(self, tempo_atual, filas, escalonador):
        self.atualizar_tempos_acumulados(tempo_atual)
        if self.clientes > 0:
            self.clientes -= 1
            id_proxima_fila = self.escolher_proxima_fila()
            if id_proxima_fila:
                filas[id_proxima_fila].processar_chegada(tempo_atual, escalonador)
            if self.clientes >= self.servidores:
                tempo_servico = tempo_atual + random.uniform(*self.intervalo_servico)
                escalonador.adicionar_evento(('SAIDA', tempo_servico, self))

    def escolher_proxima_fila(self):
        valor_aleatorio = random.random()
        probabilidade_acumulada = 0
        for id_fila, probabilidade in self.roteamento.items():
            probabilidade_acumulada += probabilidade
            if valor_aleatorio < probabilidade_acumulada:
                return id_fila
        return None

    def calcular_probabilidades(self, tempo_total_simulacao):
        return {estado: (tempo / tempo_total_simulacao) * 100 for estado, tempo in enumerate(self.tempos_acumulados)}

class Escalonador:
    def __init__(self):
        self.eventos = []

    def adicionar_evento(self, evento):
        heapq.heappush(self.eventos, (evento[1], evento))

    def proximo_evento(self):
        return heapq.heappop(self.eventos)[1] if self.eventos else None

def simular(filas, total_eventos,arrivals):
    escalonador = Escalonador()
    tempo_chegada_inicial = 2.0  # Tempo da primeira chegada

    for queue_name, tempo_chegada_inicial in arrivals.items():
        escalonador.adicionar_evento(('CHEGADA', tempo_chegada_inicial, filas[queue_name]))

    while total_eventos > 0:
        evento = escalonador.proximo_evento()
        tipo_evento, tempo_atual, fila = evento

        if tipo_evento == 'CHEGADA':
            fila.processar_chegada(tempo_atual, escalonador)
            if fila.intervalo_chegada:
                proximo_tempo_chegada = tempo_atual + random.uniform(*fila.intervalo_chegada)
                escalonador.adicionar_evento(('CHEGADA', proximo_tempo_chegada, fila))
        elif tipo_evento == 'SAIDA':
            fila.processar_saida(tempo_atual, filas, escalonador)

        total_eventos -= 1

    for id_fila, fila in filas.items():
        print(f"\nFila {id_fila}:")
        print(f"Perdas: {fila.perdas}")
        probabilidades = fila.calcular_probabilidades(fila.ultimo_evento_tempo)
        print("\nDistribuição de probabilidades dos estados:")
        for estado, probabilidade in probabilidades.items():
            if (probabilidade == 0):
                continue
            print(f"Estado {estado}: {probabilidade:.2f}%")
        print("\nTempos acumulados para os estados:")
        for estado, tempo in enumerate(fila.tempos_acumulados):
            if (tempo == 0):
                continue
            print(f"Estado {estado}: {tempo:.2f} segundos")
        print(f"Tempo total de simulação: {fila.ultimo_evento_tempo:.2f} segundos")

def carregar_configuracoes(filepath):
    global seeds
    with open(filepath, 'r') as file:
        data = yaml.safe_load(file)

    filas = {}
    roteamentos = {k: {} for k in data['queues'].keys()}

    if (data['seeds']):
        seeds = data['seeds']

    for network in data['network']:
        roteamentos[network['source']][network['target']] = network['probability']

    for id, config in data['queues'].items():
        filas[id] = Fila(id, config['servers'], config['capacity'], [config.get('minArrival'), config.get('maxArrival')], [config.get('minService'), config.get('maxService')], roteamentos[id])

    return filas, data['arrivals'], data['rndnumbersPerSeed']


def main():
    filepath = 'config.yml' 
    filas,arrivals,total_eventos  = carregar_configuracoes(filepath)

    simular(filas, total_eventos,arrivals)


if __name__ == "__main__":
    main()