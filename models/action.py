# models/action.py
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class ActionStatus(Enum):
    """Status possíveis de uma ação"""
    ABERTA = "aberta"
    FECHADA = "fechada"
    VITORIA = "vitoria"
    DERROTA = "derrota"
    INATIVIDADE = "inatividade"
    CANCELADA = "cancelada"


@dataclass
class ActionData:
    """
    Modelo de dados de uma ação
    IMPORTANTE: Armazena apenas IDs, não objetos do Discord
    """
    action_id: str
    guild_id: int
    action_name: str
    action_type: str
    
    # IDs de usuários/canais/mensagens
    escalator_id: Optional[int] = None
    call_p1_id: Optional[int] = None
    call_p2_id: Optional[int] = None
    participant_ids: List[int] = field(default_factory=list)
    
    # IDs de mensagens e canais
    message_id: Optional[int] = None
    channel_id: Optional[int] = None
    
    # Status e datas
    status: str = ActionStatus.ABERTA.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    closed_at: Optional[str] = None
    finished_at: Optional[str] = None
    inactivity_warned_at: Optional[str] = None
    
    # Configuração da ação
    max_participants: int = 10
    has_call_p1: bool = True
    has_call_p2: bool = False
    required_roles: bool = False
    display_name: str = "Ação Policial"
    
    # Metadados
    closed_by_id: Optional[int] = None  # Quem fechou
    result_set_by_id: Optional[int] = None  # Quem definiu o resultado
    
    def to_dict(self) -> Dict:
        """Converte para dicionário para salvar em JSON"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActionData':
        """Cria ActionData a partir de dicionário"""
        # Garante que participant_ids seja uma lista
        if 'participant_ids' not in data:
            data['participant_ids'] = []
        return cls(**data)
    
    def is_open(self) -> bool:
        """Verifica se a ação está aberta"""
        return self.status == ActionStatus.ABERTA.value
    
    def is_closed(self) -> bool:
        """Verifica se a ação está fechada"""
        return self.status in [ActionStatus.FECHADA.value, ActionStatus.VITORIA.value, 
                               ActionStatus.DERROTA.value, ActionStatus.INATIVIDADE.value]
    
    def has_result(self) -> bool:
        """Verifica se já tem resultado definido"""
        return self.status in [ActionStatus.VITORIA.value, ActionStatus.DERROTA.value, 
                               ActionStatus.INATIVIDADE.value]
    
    def can_set_result(self) -> bool:
        """Verifica se pode definir resultado"""
        return self.status == ActionStatus.FECHADA.value
    
    def is_full(self) -> bool:
        """Verifica se atingiu o número máximo de participantes"""
        return len(self.participant_ids) >= self.max_participants
    
    def add_participant(self, user_id: int) -> bool:
        """Adiciona participante. Retorna True se adicionado com sucesso"""
        if user_id in self.participant_ids:
            return False
        if self.is_full():
            return False
        self.participant_ids.append(user_id)
        return True
    
    def remove_participant(self, user_id: int) -> bool:
        """Remove participante. Retorna True se removido com sucesso"""
        if user_id not in self.participant_ids:
            return False
        self.participant_ids.remove(user_id)
        # Remove também de calls se for o caso
        if self.call_p1_id == user_id:
            self.call_p1_id = None
        if self.call_p2_id == user_id:
            self.call_p2_id = None
        return True
    
    def get_hours_since_creation(self) -> float:
        """Retorna horas desde a criação"""
        created = datetime.fromisoformat(self.created_at)
        now = datetime.now()
        delta = now - created
        return delta.total_seconds() / 3600
    
    def get_hours_since_closed(self) -> float:
        """Retorna horas desde o fechamento"""
        if not self.closed_at:
            return 0
        closed = datetime.fromisoformat(self.closed_at)
        now = datetime.now()
        delta = now - closed
        return delta.total_seconds() / 3600