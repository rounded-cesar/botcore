# utils/embeds.py
import discord
from datetime import datetime
from models.action import ActionData, ActionStatus
from typing import Optional


def get_status_color(status: str) -> discord.Color:
    """Retorna cor baseada no status"""
    if status == ActionStatus.ABERTA.value:
        return discord.Color.red()
    elif status == ActionStatus.FECHADA.value:
        return discord.Color.orange()
    elif status == ActionStatus.VITORIA.value:
        return discord.Color.green()
    elif status == ActionStatus.DERROTA.value:
        return discord.Color.dark_gray()
    elif status == ActionStatus.INATIVIDADE.value:
        return discord.Color.dark_purple()
    elif status == ActionStatus.CANCELADA.value:
        return discord.Color.light_gray()
    return discord.Color.blue()


def get_status_emoji(status: str) -> str:
    """Retorna emoji baseado no status"""
    if status == ActionStatus.ABERTA.value:
        return "🟢"
    elif status == ActionStatus.FECHADA.value:
        return "🔒"
    elif status == ActionStatus.VITORIA.value:
        return "🏆"
    elif status == ActionStatus.DERROTA.value:
        return "💀"
    elif status == ActionStatus.INATIVIDADE.value:
        return "⏰"
    elif status == ActionStatus.CANCELADA.value:
        return "❌"
    return "📋"


def get_status_text(status: str) -> str:
    """Retorna texto do status"""
    if status == ActionStatus.ABERTA.value:
        return "ABERTA"
    elif status == ActionStatus.FECHADA.value:
        return "FECHADA"
    elif status == ActionStatus.VITORIA.value:
        return "VITÓRIA"
    elif status == ActionStatus.DERROTA.value:
        return "DERROTA"
    elif status == ActionStatus.INATIVIDADE.value:
        return "INATIVIDADE"
    elif status == ActionStatus.CANCELADA.value:
        return "CANCELADA"
    return "DESCONHECIDO"


def create_action_embed(action: ActionData, guild: discord.Guild) -> discord.Embed:
    """Cria embed da ação com todas as informações"""
    emoji = get_status_emoji(action.status)
    color = get_status_color(action.status)
    status_text = get_status_text(action.status)
    
    embed = discord.Embed(
        title=f"🚨 {action.display_name}",
        description=f"**{action.action_name}**",
        color=color,
        timestamp=datetime.fromisoformat(action.created_at)
    )
    
    # Status
    embed.add_field(
        name="Status",
        value=f"{emoji} **{status_text}**",
        inline=True
    )
    
    # Horário de criação
    created_dt = datetime.fromisoformat(action.created_at)
    embed.add_field(
        name="Criada em",
        value=f"<t:{int(created_dt.timestamp())}:R>",
        inline=True
    )
    
    # Indica se requer cargos
    if action.required_roles:
        embed.add_field(
            name="🎖️ Requisitos",
            value="Requer cargo específico",
            inline=True
        )
    
    # Escalador
    escalator_text = "Aguardando..."
    if action.escalator_id:
        escalator_text = f"<@{action.escalator_id}>"
    embed.add_field(name="📋 Escalador", value=escalator_text, inline=True)
    
    # Calls - mostra baseado na configuração
    if action.has_call_p1 and action.has_call_p2:
        # Tem P1 e P2 - mostra ambos
        call_p1_text = f"<@{action.call_p1_id}>" if action.call_p1_id else "Aguardando..."
        embed.add_field(name="📞 Call P1", value=call_p1_text, inline=True)
        
        call_p2_text = f"<@{action.call_p2_id}>" if action.call_p2_id else "Aguardando..."
        embed.add_field(name="📞 Call P2", value=call_p2_text, inline=True)
    elif action.has_call_p1 and not action.has_call_p2:
        # Tem apenas P1 - mostra como "Call" genérico
        call_text = f"<@{action.call_p1_id}>" if action.call_p1_id else "Aguardando..."
        embed.add_field(name="📞 Call", value=call_text, inline=True)
    
    # Participantes
    participants_text = f"**{len(action.participant_ids)}/{action.max_participants}**"
    if action.participant_ids:
        # Mostra TODOS os participantes, separados por quebra de linha
        participants_list = "\n".join([f"<@{uid}>" for uid in action.participant_ids])
        participants_text += f"\n{participants_list}"
    
    embed.add_field(name="👥 Participantes", value=participants_text, inline=False)
    
    # Informações adicionais para ações fechadas/finalizadas
    if action.closed_at:
        closed_dt = datetime.fromisoformat(action.closed_at)
        embed.add_field(
            name="Fechada em",
            value=f"<t:{int(closed_dt.timestamp())}:R>",
            inline=True
        )
    
    if action.finished_at:
        finished_dt = datetime.fromisoformat(action.finished_at)
        embed.add_field(
            name="Finalizada em",
            value=f"<t:{int(finished_dt.timestamp())}:R>",
            inline=True
        )
    
    embed.set_footer(text=f"ID: {action.action_id}")
    
    return embed


def create_config_embed(config: dict, guild: discord.Guild) -> discord.Embed:
    """Cria embed de configurações"""
    embed = discord.Embed(
        title="⚙️ Configurações do Servidor",
        color=discord.Color.blue()
    )
    
    # Canais
    action_ch = f"<#{config['action_channel']}>" if config['action_channel'] else "Não configurado"
    escalation_ch = f"<#{config['escalation_channel']}>" if config['escalation_channel'] else "Não configurado"
    report_ch = f"<#{config['report_channel']}>" if config['report_channel'] else "Não configurado"
    
    embed.add_field(name="📢 Canal de Ações", value=action_ch, inline=False)
    embed.add_field(name="📋 Canal de Escalações", value=escalation_ch, inline=False)
    embed.add_field(name="📊 Canal de Relatórios", value=report_ch, inline=False)
    
    # Cargos de escalação
    escalation_roles = config.get('escalation_roles', [])
    if escalation_roles:
        role_mentions = [f"<@&{rid}>" for rid in escalation_roles if guild.get_role(rid)]
        roles_text = " ".join(role_mentions) if role_mentions else "Nenhum cargo válido"
    else:
        roles_text = "Nenhum cargo configurado"
    embed.add_field(name="🎖️ Cargos para Escalação", value=roles_text, inline=False)
    
    # Cargos admin
    admin_roles = config.get('admin_roles', [])
    if admin_roles:
        role_mentions = [f"<@&{rid}>" for rid in admin_roles if guild.get_role(rid)]
        roles_text = " ".join(role_mentions) if role_mentions else "Nenhum cargo válido"
    else:
        roles_text = "Apenas administradores do Discord"
    embed.add_field(name="👑 Cargos Admin", value=roles_text, inline=False)
    
    # Configurações de tempo
    warning_h = config.get('warning_hours', 20)
    inactivity_h = config.get('inactivity_hours', 24)
    auto_close_h = config.get('auto_close_hours')
    
    embed.add_field(name="⏰ Aviso de Inatividade", value=f"{warning_h}h", inline=True)
    embed.add_field(name="⏱️ Inatividade Automática", value=f"{inactivity_h}h", inline=True)
    embed.add_field(
        name="🔒 Fechamento Automático",
        value=f"{auto_close_h}h" if auto_close_h else "Desabilitado",
        inline=True
    )
    
    return embed


def create_error_embed(message: str, title: str = "Erro") -> discord.Embed:
    """Cria embed de erro"""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=message,
        color=discord.Color.red()
    )
    return embed


def create_success_embed(message: str, title: str = "Sucesso") -> discord.Embed:
    """Cria embed de sucesso"""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=message,
        color=discord.Color.green()
    )
    return embed


def create_warning_embed(message: str, title: str = "Aviso") -> discord.Embed:
    """Cria embed de aviso"""
    embed = discord.Embed(
        title=f"⚠️ {title}",
        description=message,
        color=discord.Color.orange()
    )
    return embed