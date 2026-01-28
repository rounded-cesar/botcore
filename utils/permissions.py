# utils/permissions.py
import discord
from typing import List


def has_any_role(member: discord.Member, role_ids: List[int]) -> bool:
    """Verifica se o membro tem algum dos cargos especificados"""
    if not role_ids:
        return False
    member_role_ids = [role.id for role in member.roles]
    return any(role_id in member_role_ids for role_id in role_ids)


def is_escalator(member: discord.Member, action, config_service) -> bool:
    """Verifica se o membro é o escalador da ação"""
    return action.escalator_id == member.id


def can_escalate(member: discord.Member, guild_id: int, action, config_service) -> bool:
    """Verifica se o membro pode assumir a escalação"""
    # Verifica se a ação requer cargos específicos
    if not action.required_roles:
        return True
    
    # Obtém cargos permitidos
    allowed_roles = config_service.get_escalation_roles(guild_id)
    if not allowed_roles:
        return True  # Se não há cargos configurados, qualquer um pode
    
    return has_any_role(member, allowed_roles)


def is_admin(member: discord.Member, guild_id: int, config_service) -> bool:
    """Verifica se o membro é admin (tem cargo admin ou é administrador do servidor)"""
    # Administrador do Discord sempre tem acesso
    if member.guild_permissions.administrator:
        return True
    
    # Verifica cargos admin configurados
    admin_roles = config_service.get_admin_roles(guild_id)
    if not admin_roles:
        # Se não há cargos configurados, apenas admins do Discord tem acesso
        return False
    
    return has_any_role(member, admin_roles)


def can_manage_action(member: discord.Member, guild_id: int, action, config_service) -> bool:
    """Verifica se o membro pode gerenciar a ação (escalador ou admin)"""
    return (is_escalator(member, action, config_service) or 
            is_admin(member, guild_id, config_service))


def get_missing_roles_text(member: discord.Member, guild_id: int, config_service) -> str:
    """Retorna texto explicando quais cargos são necessários"""
    allowed_role_ids = config_service.get_escalation_roles(guild_id)
    
    if not allowed_role_ids:
        return "Nenhum cargo foi configurado para escalação"
    
    role_names = []
    for role_id in allowed_role_ids:
        role = member.guild.get_role(role_id)
        if role:
            role_names.append(role.name)
    
    if not role_names:
        return "Cargos configurados não foram encontrados"
    
    return f"Você precisa ter um dos seguintes cargos: **{', '.join(role_names)}**"