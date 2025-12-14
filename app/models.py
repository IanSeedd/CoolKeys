from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    destaque = models.BooleanField(default=False)
    
    def __str__(self):
        return self.nome

class Jogo(models.Model):
    nome = models.CharField(max_length=200) 
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    descricao = models.TextField()
    deletado = models.BooleanField(default=False) # Soft delete
    desconto = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        null=True, 
        blank=True,
    )

    icone = models.ImageField(
        upload_to='icones/',
        default='icones/bobas.webp',
        null=True, 
        blank=True,
        # Por padrão, null=False e blank=False.
        # Você pode ser explícito, se preferir:
    )

    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL,  # ou models.PROTECT se preferir, se a categoria for deletada os jogos não são
        null=True, 
        blank=True,
        related_name='jogos'  # opcional: para acessar jogos de uma categoria
    )
    
    @property  # Função que pode ser acessada como atributo
    def preco_com_desconto(self):
        # Retoma o preço com desconto (se houver)
        if self.desconto:
            # Converte para Decimal para precisão
            desconto_decimal = Decimal(self.desconto) / Decimal(100)
            valor_desconto = self.preco * desconto_decimal
            return self.preco - valor_desconto
        return self.preco
    
    @property
    def valor_desconto(self):
        # Retoma o valor do desconto 
        if self.desconto:
            desconto_decimal = Decimal(self.desconto) / Decimal(100) #para contas mais precisas
            return self.preco * desconto_decimal
        return Decimal('0.00')
    
    def __str__(self):
        # Mostra preço com desconto se houver
        if self.desconto:
            return f"{self.nome} - R$ {self.preco_com_desconto} (↓{self.desconto}%)"
        return f"{self.nome} - R$ {self.preco}"



class Compra(models.Model): #representa transações em geral, ativas e inativas
    # Status da compra
    STATUS_CHOICES = [
        ('pendente', 'Pendente'), # Funciona como CARRINHO
        ('finalizada', 'Finalizada'), # Funciona como HISTÓRICO
        ('cancelado', 'Cancelado'),
    ]
    
    jogos = models.ManyToManyField(Jogo, through='ItemCompra', related_name='compras')  # Through especifica um modelo intermediário personalizado, no caso ItemCompra que da a quantidade e etc.. 
    data_compra = models.DateTimeField(auto_now_add=True) # literalmente só define a hora/data de quando o objeto/compra é criado
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente'  # Alterado default para 'pedente'(no caso carrinho)
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Caso o usuário seja deletado, todas as compras relacionadas também serão
        related_name='minhas_compras', # Para chamar usuario.minhas_compras.all()
        verbose_name='Client' # Nome amigável para adms (humanos)
    )
    
    def __str__(self):
        return f"Compra #{self.id} - {self.usuario}" # Apenas uma string para representar a compra
    
    def atualizar_total(self):
        # Soma dos valores...
        total = sum(item.subtotal() for item in self.itens.all()) # Itens é um related_name de ItemCompra
        self.valor_total = total
        self.save()

    def limpar_jogos_deletados(self):
        # Remover jogos deletados do carrinho/pendente
        if self.status != 'pendente':  # Só aplica para carrinhos (pendentes)
            return []
        
        jogos_removidos = [] # Se for pendente
        
        # Percorre todos os itens do carrinho
        for item in self.itens.all():
            # Se o jogo foi marcado como deletado (soft delete)
            if item.jogo and item.jogo.deletado:
                nome_jogo = item.jogo.nome
                item.delete()  # Remove o item do carrinho
                jogos_removidos.append(nome_jogo)
            
            # Se o jogo foi deletado fisicamente (jogo é NULL)
            elif item.jogo is None:
                item.delete()  # Remove o item do carrinho
                jogos_removidos.append("Jogo removido do sistema")
        
        # Atualiza o total do carrinho se removeu algum item
        if jogos_removidos:
            self.atualizar_total()
        
        return jogos_removidos
    
    def save(self, *args, **kwargs):
        # Limpar itens deletados automaticamente para assim atualizar de fato o carrinho sem usar o views
        
        # Se for um carrinho (pendente), limpa antes de salvar
        if self.status == 'pendente' and self.pk:  # self.pk significa que já existe no banco
            self.limpar_jogos_deletados()
        
        super().save(*args, **kwargs) # Salva a Compra
    
class ItemCompra(models.Model): # Intermediário entre Compra e Jogo
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='itens') 
    jogo = models.ForeignKey(Jogo, on_delete=models.SET_NULL, null=True, blank=True) # jogo fica com valor NULL caso seja deletado porém o objeto ItemCompra não é deletado(só perde o referencial), e o resto permite campos vazios
    quantidade = models.PositiveIntegerField(default=1) # Apenas controle de quantidade, pois ela não pode ser negativa e deve ser maior que 0
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2) # Armazena o preço do jogo mesmo após ele ser deletado
    
    # Snapshot de segurança (apenas para histórico, segurança de dados para caso de hard delete)
    nome_snapshot = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['compra', 'jogo']  # Um jogo só pode aparecer uma vez por compra, resumindo impede que opções iguais causem conflitos

    def save(self, *args, **kwargs):
        # snapshot automático ao finalizar a compra
        # Se NÃO é pendete e ainda não tem snapshot
        if self.compra and self.compra.status != 'pendente' and not self.nome_snapshot:
            if self.jogo:
                self.nome_snapshot = self.jogo.nome
            else:
                self.nome_snapshot = "Jogo Removido"
        
        super().save(*args, **kwargs) # Chama o save nativo do Django com parâmetros django

    def subtotal(self):
        # Logica para o valor se tornar 0 se for deletado e estiver no carrinho e se for aprovado nada muda
        # Caso 1: É pendente, jogo existe e está deletado
        if (self.compra and 
            self.compra.status == 'pendente' and 
            self.jogo and 
            self.jogo.deletado):
            return 0
        
        # Caso 2: Qualquer outro caso (histórico ou jogo não deletado)
        # Se tem jogo, usa preço COM desconto
        if self.jogo:
            return self.jogo.preco_com_desconto * self.quantidade
        # Se não tem jogo (histórico), usa preço salvo
        return self.preco_unitario * self.quantidade
    
    def esta_valido_no_carrinho(self):
        # Verifica se o item pode ser comprado
        if not self.compra or self.compra.status != 'pendente':
            return True  # No histórico, sempre é "válido"
        
        return self.jogo and not self.jogo.deletado
    
    def nome_para_exibicao(self):
        # Da um nome apropriado dependendo do estado do jogo
        if self.compra and self.compra.status == 'pendente':
            # No carrinho: mostra nome atual
            if self.jogo:
                return f"{self.jogo.nome} {'[DELETADO]' if self.jogo.deletado else ''}" # Para o soft delete
            return "Item inválido" # Apenas um recurso de ultima hora
        else:
            # No histórico: mostra snapshot ou nome atual
            if self.nome_snapshot: #Prioriza a snapshot
                return self.nome_snapshot
            elif self.jogo:
                return self.jogo.nome
            return "Jogo não encontrado" # Apenas um recurso de ultima hora
    
    def __str__(self):
        if self.jogo:
            return f"{self.quantidade}x {self.jogo.nome}"
        return f"{self.quantidade}x Jogo Removido" 
