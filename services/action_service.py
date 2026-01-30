# services/action_service.py
import json
import os
from typing import Optional, List, Dict
from datetime import datetime
import asyncio
from models.action import ActionData, ActionStatus


class ActionService:
    """
    Service Layer para gerenciamento de ações
    Responsável por toda a lógica de negócio e persistência
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.active_file = os.path.join(data_dir, "active_actions.json")
        self.history_file = os.path.join(data_dir, "actions_history.json")
        self.active_actions: Dict[str, ActionData] = {}
        self._lock = asyncio.Lock()
        
        # Cria diretório de dados se não existir
        os.makedirs(data_dir, exist_ok=True)
        
        # Carrega ações ativas
        self.load_active_actions()
    
    def load_active_actions(self):
        """Carrega ações ativas do arquivo"""
        if os.path.exists(self.active_file):
            try:
                with open(self.active_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for action_id, action_dict in data.items():
                        self.active_actions[action_id] = ActionData.from_dict(action_dict)
                print(f"✅ {len(self.active_actions)} ações ativas carregadas")
            except Exception as e:
                print(f"❌ Erro ao carregar ações ativas: {e}")
    
    def save_active_actions(self):
        """Salva ações ativas no arquivo"""
        try:
            data = {action_id: action.to_dict() 
                   for action_id, action in self.active_actions.items()}
            with open(self.active_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao salvar ações ativas: {e}")
    
    def save_to_history(self, action: ActionData):
        """Salva ação no histórico"""
        try:
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Atualiza ou adiciona
            action_dict = action.to_dict()
            existing_idx = next((i for i, h in enumerate(history) 
                               if h['action_id'] == action.action_id), None)
            
            if existing_idx is not None:
                history[existing_idx] = action_dict
            else:
                history.append(action_dict)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao salvar no histórico: {e}")
    
    def load_history(self, days: Optional[int] = None) -> List[ActionData]:
        """Carrega histórico de ações"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            actions = [ActionData.from_dict(h) for h in history]
            
            # Filtra por data se especificado
            if days:
                cutoff = datetime.now().timestamp() - (days * 24 * 3600)
                actions = [a for a in actions 
                          if datetime.fromisoformat(a.created_at).timestamp() >= cutoff]
            
            return actions
        except Exception as e:
            print(f"❌ Erro ao carregar histórico: {e}")
            return []
    
    async def create_action(self, guild_id: int, action_name: str, 
                           action_type: str, config: Dict,
                           channel_id: int, message_id: int) -> ActionData:
        """Cria uma nova ação"""
        async with self._lock:
            # Gera ID único
            action_id = f"{guild_id}_{int(datetime.now().timestamp() * 1000)}"
            
            # Cria objeto ActionData
            action = ActionData(
                action_id=action_id,
                guild_id=guild_id,
                action_name=action_name,
                action_type=action_type,
                channel_id=channel_id,
                message_id=message_id,
                max_participants=config.get('max_participants', 10),
                has_call_p1=config.get('has_call_p1', True),
                has_call_p2=config.get('has_call_p2', False),
                required_roles=config.get('required_roles', False),
                display_name=config.get('display_name', action_name)
            )
            
            # Adiciona às ações ativas
            self.active_actions[action_id] = action
            
            # Salva
            self.save_active_actions()
            self.save_to_history(action)
            
            return action
    
    def get_action(self, action_id: str) -> Optional[ActionData]:
        """Retorna uma ação pelo ID"""
        return self.active_actions.get(action_id)
    
    def get_guild_actions(self, guild_id: int, 
                         include_closed: bool = False) -> List[ActionData]:
        """Retorna todas as ações de um servidor"""
        actions = [a for a in self.active_actions.values() 
                  if a.guild_id == guild_id]
        
        if not include_closed:
            actions = [a for a in actions if a.is_open()]
        
        return actions
    
    async def set_escalator(self, action_id: str, user_id: int) -> bool:
        """Define o escalador da ação"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or action.escalator_id:
                return False
            
            action.escalator_id = user_id
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def set_call_p1(self, action_id: str, user_id: int) -> bool:
        """Define o Call P1"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or action.call_p1_id or not action.has_call_p1:
                return False
            
            action.call_p1_id = user_id
            # NÃO adiciona automaticamente aos participantes
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def set_call_p2(self, action_id: str, user_id: int) -> bool:
        """Define o Call P2"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or action.call_p2_id or not action.has_call_p2:
                return False
            
            action.call_p2_id = user_id
            # NÃO adiciona automaticamente aos participantes
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def add_participant(self, action_id: str, user_id: int) -> bool:
        """Adiciona participante"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or not action.is_open():
                return False
            
            success = action.add_participant(user_id)
            if success:
                self.save_active_actions()
                self.save_to_history(action)
            return success
    
    async def remove_participant(self, action_id: str, user_id: int) -> bool:
        """Remove participante"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action:
                return False
            
            success = action.remove_participant(user_id)
            if success:
                self.save_active_actions()
                self.save_to_history(action)
            return success
    
    async def close_action(self, action_id: str, closed_by_id: int) -> bool:
        """Fecha a ação"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or not action.is_open():
                return False
            
            action.status = ActionStatus.FECHADA.value
            action.closed_at = datetime.now().isoformat()
            action.closed_by_id = closed_by_id
            
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def reopen_action(self, action_id: str) -> bool:
        """Reabre uma ação fechada"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or action.has_result():
                return False
            
            action.status = ActionStatus.ABERTA.value
            action.closed_at = None
            action.closed_by_id = None
            
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def set_result(self, action_id: str, result: str, 
                        set_by_id: int) -> bool:
        """Define resultado da ação"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or not action.can_set_result():
                return False
            
            if result == "victory":
                action.status = ActionStatus.VITORIA.value
            elif result == "defeat":
                action.status = ActionStatus.DERROTA.value
            else:
                return False
            
            action.finished_at = datetime.now().isoformat()
            action.result_set_by_id = set_by_id
            
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def force_result(self, action_id: str, result: str, 
                          set_by_id: int) -> bool:
        """Força resultado mesmo sem estar fechada (admin)"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or action.has_result():
                return False
            
            # Fecha primeiro se estiver aberta
            if action.is_open():
                action.status = ActionStatus.FECHADA.value
                action.closed_at = datetime.now().isoformat()
                action.closed_by_id = set_by_id
            
            # Define resultado
            if result == "victory":
                action.status = ActionStatus.VITORIA.value
            elif result == "defeat":
                action.status = ActionStatus.DERROTA.value
            else:
                return False
            
            action.finished_at = datetime.now().isoformat()
            action.result_set_by_id = set_by_id
            
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def set_inactivity(self, action_id: str) -> bool:
        """Define ação como inativa"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action or action.has_result():
                return False
            
            action.status = ActionStatus.INATIVIDADE.value
            action.finished_at = datetime.now().isoformat()
            
            self.save_active_actions()
            self.save_to_history(action)
            return True
    
    async def mark_inactivity_warning(self, action_id: str) -> bool:
        """Marca que o aviso de inatividade foi enviado"""
        async with self._lock:
            action = self.get_action(action_id)
            if not action:
                return False
            
            action.inactivity_warned_at = datetime.now().isoformat()
            self.save_active_actions()
            return True
    
    async def delete_action(self, action_id: str) -> bool:
        """Remove ação das ações ativas"""
        async with self._lock:
            if action_id in self.active_actions:
                del self.active_actions[action_id]
                self.save_active_actions()
                return True
            return False
    
    def get_actions_needing_inactivity_check(self, hours: float = 20) -> List[ActionData]:
        """Retorna ações que precisam de aviso de inatividade"""
        actions = []
        for action in self.active_actions.values():
            # Ignora ações já finalizadas
            if action.has_result():
                continue
            
            # Verifica se está aberta há mais de X horas
            if action.get_hours_since_creation() >= hours:
                # Se já foi avisado, ignora
                if action.inactivity_warned_at:
                    continue
                actions.append(action)
        
        return actions
    
    def get_actions_needing_inactivity_close(self, hours: float = 24) -> List[ActionData]:
        """Retorna ações que devem ser fechadas por inatividade"""
        actions = []
        for action in self.active_actions.values():
            # Ignora ações já finalizadas
            if action.has_result():
                continue
            
            # Verifica se está aberta há mais de X horas
            if action.get_hours_since_creation() >= hours:
                actions.append(action)
        
        return actions