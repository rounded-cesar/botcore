# services/config_service.py
import json
import os
from typing import Dict, List, Optional


class ConfigService:
    """
    Service para gerenciar configurações dos servidores
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "server_config.json")
        self.action_types_file = os.path.join(data_dir, "action_types.json")
        
        os.makedirs(data_dir, exist_ok=True)
        
        self.server_configs = self._load_configs()
        self.action_types = self._load_action_types()
    
    def _load_configs(self) -> Dict:
        """Carrega configurações dos servidores"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_configs(self):
        """Salva configurações dos servidores"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.server_configs, f, indent=2, ensure_ascii=False)
    
    def _load_action_types(self) -> Dict:
        """Carrega tipos de ações"""
        if os.path.exists(self.action_types_file):
            with open(self.action_types_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Configuração padrão se não existir
        default_actions = {
            "ASSALTO_BANCO": {
                "max_participants": 10,
                "has_call_p1": True,
                "has_call_p2": True,
                "display_name": "Assalto ao Banco",
                "required_roles": True
            },
            "ROUBO_CARRO": {
                "max_participants": 6,
                "has_call_p1": True,
                "has_call_p2": False,
                "display_name": "Roubo de Carro",
                "required_roles": False
            },
            "OPERACAO_ESPECIAL": {
                "max_participants": 15,
                "has_call_p1": True,
                "has_call_p2": True,
                "display_name": "Operação Especial",
                "required_roles": True
            },
            "PATRULHAMENTO": {
                "max_participants": 8,
                "has_call_p1": False,
                "has_call_p2": False,
                "display_name": "Patrulhamento",
                "required_roles": False
            }
        }
        
        with open(self.action_types_file, 'w', encoding='utf-8') as f:
            json.dump(default_actions, f, indent=2, ensure_ascii=False)
        
        return default_actions
    
    def get_server_config(self, guild_id: int) -> Dict:
        """Retorna configuração do servidor"""
        guild_key = str(guild_id)
        if guild_key not in self.server_configs:
            self.server_configs[guild_key] = {
                "action_channel": None,
                "escalation_channel": None,
                "report_channel": None,
                "escalation_roles": [],
                "admin_roles": [],  # Cargos com acesso ao painel admin
                "inactivity_hours": 24,  # Horas até marcar como inativa
                "warning_hours": 20,  # Horas até avisar sobre inatividade
                "auto_close_hours": None  # Horas até fechar automaticamente (None = desabilitado)
            }
            self._save_configs()
        return self.server_configs[guild_key]
    
    def set_action_channel(self, guild_id: int, channel_id: int):
        """Define canal de ações"""
        config = self.get_server_config(guild_id)
        config["action_channel"] = channel_id
        self._save_configs()
    
    def set_escalation_channel(self, guild_id: int, channel_id: int):
        """Define canal de escalações"""
        config = self.get_server_config(guild_id)
        config["escalation_channel"] = channel_id
        self._save_configs()
    
    def set_report_channel(self, guild_id: int, channel_id: int):
        """Define canal de relatórios"""
        config = self.get_server_config(guild_id)
        config["report_channel"] = channel_id
        self._save_configs()
    
    def add_escalation_role(self, guild_id: int, role_id: int):
        """Adiciona cargo permitido para escalação"""
        config = self.get_server_config(guild_id)
        if role_id not in config["escalation_roles"]:
            config["escalation_roles"].append(role_id)
            self._save_configs()
    
    def remove_escalation_role(self, guild_id: int, role_id: int):
        """Remove cargo da lista de escalação"""
        config = self.get_server_config(guild_id)
        if role_id in config["escalation_roles"]:
            config["escalation_roles"].remove(role_id)
            self._save_configs()
    
    def get_escalation_roles(self, guild_id: int) -> List[int]:
        """Retorna lista de IDs de cargos permitidos para escalação"""
        config = self.get_server_config(guild_id)
        return config.get("escalation_roles", [])
    
    def add_admin_role(self, guild_id: int, role_id: int):
        """Adiciona cargo admin"""
        config = self.get_server_config(guild_id)
        if role_id not in config["admin_roles"]:
            config["admin_roles"].append(role_id)
            self._save_configs()
    
    def remove_admin_role(self, guild_id: int, role_id: int):
        """Remove cargo admin"""
        config = self.get_server_config(guild_id)
        if role_id in config["admin_roles"]:
            config["admin_roles"].remove(role_id)
            self._save_configs()
    
    def get_admin_roles(self, guild_id: int) -> List[int]:
        """Retorna lista de IDs de cargos admin"""
        config = self.get_server_config(guild_id)
        return config.get("admin_roles", [])
    
    def set_inactivity_hours(self, guild_id: int, hours: int):
        """Define horas até inatividade"""
        config = self.get_server_config(guild_id)
        config["inactivity_hours"] = hours
        self._save_configs()
    
    def set_warning_hours(self, guild_id: int, hours: int):
        """Define horas até aviso"""
        config = self.get_server_config(guild_id)
        config["warning_hours"] = hours
        self._save_configs()
    
    def set_auto_close_hours(self, guild_id: int, hours: Optional[int]):
        """Define horas até fechamento automático"""
        config = self.get_server_config(guild_id)
        config["auto_close_hours"] = hours
        self._save_configs()
    
    def get_action_config(self, action_name: str) -> Dict:
        """Retorna configuração de um tipo de ação"""
        if not action_name:
            # Retorna configuração padrão
            return {
                "max_participants": 30,
                "has_call_p1": True,
                "has_call_p2": True,
                "display_name": "Ação Policial",
                "required_roles": False
            }
        
        action_key = action_name.upper().strip().replace(" ", "_")
        
        # Busca exata
        if action_key in self.action_types:
            return self.action_types[action_key]
        
        # Busca parcial
        for key, value in self.action_types.items():
            if key in action_key or action_key in key:
                return value
        
        # Retorna padrão se não encontrar
        return {
            "max_participants": 30,
            "has_call_p1": True,
            "has_call_p2": True,
            "display_name": action_name,
            "required_roles": False
        }
    
    def get_action_type_key(self, action_name: str) -> str:
        """Retorna a chave do tipo de ação"""
        if not action_name:
            return "DEFAULT"
        
        action_key = action_name.upper().strip().replace(" ", "_")
        
        if action_key in self.action_types:
            return action_key
        
        for key in self.action_types.keys():
            if key in action_key or action_key in key:
                return key
        
        return "DEFAULT"