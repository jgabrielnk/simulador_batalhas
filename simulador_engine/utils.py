import math

def calcular_distancia(ponto1, ponto2):
  """Calcula a distância euclidiana entre dois pontos (tuplas ou listas)."""
  return math.sqrt((ponto1[0] - ponto2[0])**2 + (ponto1[1] - ponto2[1])**2)

def normalizar_vetor(vetor):
    """Normaliza um vetor (tupla ou lista) para ter magnitude 1."""
    mag = math.sqrt(vetor[0]**2 + vetor[1]**2)
    if mag == 0:
        return (0, 0)
    return (vetor[0] / mag, vetor[1] / mag)

def limitar_valor(valor, minimo, maximo):
    """Garante que um valor esteja dentro de um intervalo."""
    return max(minimo, min(valor, maximo))