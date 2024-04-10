import argparse
import heapq
import random

class Fila:
    def __init__(self, servidores, capacidade, intervalo_chegada, intervalo_servico):
        self.servidores = servidores
        self.capacidade = capacidade
        self.intervalo_chegada = intervalo_chegada
        self.intervalo_servico = intervalo_servico
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

    def processar_saida(self, tempo_atual, proxima_fila, escalonador):
        self.atualizar_tempos_acumulados(tempo_atual)
        if self.clientes > 0:
            self.clientes -= 1
            if proxima_fila:
                proxima_fila.processar_chegada(tempo_atual, escalonador)
            if self.clientes >= self.servidores:
                tempo_servico = tempo_atual + random.uniform(*self.intervalo_servico)
                escalonador.adicionar_evento(('SAIDA', tempo_servico, self))

    def calcular_probabilidades(self, tempo_total_simulacao):
        return {estado: (tempo / tempo_total_simulacao) * 100 for estado, tempo in enumerate(self.tempos_acumulados)}


class Escalonador:
    def __init__(self):
        self.eventos = []

    def adicionar_evento(self, evento):
        heapq.heappush(self.eventos, (evento[1], evento))

    def proximo_evento(self):
        return heapq.heappop(self.eventos)[1] if self.eventos else None


def simular(fila1, fila2, eventos_totais):
    escalonador = Escalonador()
    tempo_chegada_inicial = 1.5
    escalonador.adicionar_evento(('CHEGADA', tempo_chegada_inicial, fila1))

    while eventos_totais > 0:
        evento = escalonador.proximo_evento()
        tipo_evento, tempo_atual, fila = evento

        if tipo_evento == 'CHEGADA':
            fila.processar_chegada(tempo_atual, escalonador)
            proximo_tempo_chegada = tempo_atual + random.uniform(*fila1.intervalo_chegada)
            escalonador.adicionar_evento(('CHEGADA', proximo_tempo_chegada, fila1))
        elif tipo_evento == 'SAIDA':
            fila.processar_saida(tempo_atual, fila2 if fila is fila1 else None, escalonador)

        eventos_totais -= 1
    cont =1
    for q in [fila1, fila2]:
        print(f"\nfila {cont}:")
        print(f"\nperdas da fila: {q.perdas}")
        probabilidades = q.calcular_probabilidades(q.ultimo_evento_tempo)
        print("\ndistribuicao de probabilidades dos estados da fila:")
        for estado, probabilidade in probabilidades.items():
            print(f"estado {estado}: {probabilidade:.2f}%")
        print("\ntempos Acumulados para os Estados da Fila:")
        for estado, tempo in enumerate(q.tempos_acumulados):
            print(f"estado {estado}: {tempo:.2f} segundos")

        print(f"\ntempo total de simulacao para a fila: {q.ultimo_evento_tempo:.2f} segundos")
        cont+=1


def analisar_argumentos():
    analisador = argparse.ArgumentParser(description="simulacao de filas em tandem")
    analisador.add_argument("--eventos_totais", type=int, default=100000, help="numero total de eventos aleatorios para simular")
    args = analisador.parse_args()
    return args.eventos_totais

if __name__ == "__main__":
    eventos_totais = analisar_argumentos()
    fila1 = Fila(servidores=2, capacidade=3, intervalo_chegada=(1, 4), intervalo_servico=(3, 4))
    fila2 = Fila(servidores=1, capacidade=5, intervalo_chegada=None, intervalo_servico=(2, 3))
    simular(fila1, fila2, eventos_totais)