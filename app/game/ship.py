from ast import List

class Ship:
    def __init__(self, nome, tamanho, posicoes=None, tamanho_grid=None):
        self.nome = nome
        self.tamanho = tamanho
        self.posicoes = posicoes or []
        self.hits = set()
        self.tamanho_grid = tamanho_grid

    def __eq__(self, other):
        if not isinstance(other, Ship):
            return False
        return self.nome == other.nome and self.tamanho == other.tamanho and self.posicoes == other.posicoes

    def get_alcance(self):
        alcanceBarco = None
        posInicio = self.posicoes[0]
        if self.posicoes[1] == "v":
            inicio = posInicio[0]
            fim = inicio + self.tamanho
            alcanceBarco = [(linha, posInicio[1]) for linha in range(inicio, fim)]
        else:
            inicio = posInicio[1]
            fim = inicio + self.tamanho
            alcanceBarco = [(posInicio[0], coluna) for coluna in range(inicio, fim)]
        return alcanceBarco
    
    def esta_fora_do_mapa(self) -> bool:
        pos = self.posicoes[0]
        tamanho = self.tamanho
        if self.posicoes[1] == "v":
            if pos[0] + tamanho > self.tamanho_grid or pos[0] < 0:
                return True
        else:
            if pos[1] + tamanho > self.tamanho_grid or pos[1] < 0:
                return True
            
        return False

    def colide_com(self, outro_barco) -> bool:
        if not isinstance(outro_barco, Ship):
            raise ValueError("O argumento deve ser uma instância da classe Ship.")
        return set(self.get_alcance()).intersection(set(outro_barco.get_alcance())) != set()

    def pode_posicionar(self, barcos: List) -> bool:
        if not isinstance(barcos, list):
            raise ValueError("O argumento deve ser uma lista de instâncias da classe Ship.")
        if not all(isinstance(barco, Ship) for barco in barcos):
            raise ValueError("Todos os elementos da lista devem ser instâncias da classe Ship.")
        if self.esta_fora_do_mapa():
            print("O barco está fora do mapa.\n")
            return False
        for i, outro_barco in enumerate(barcos):
            if outro_barco != self:
                if self.colide_com(outro_barco):
                    print("O barco colide com outro barco.\n")
                    return False
        return True

    def foi_destruido(self):
        return len(self.hits) == self.tamanho
