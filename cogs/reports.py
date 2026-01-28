# cogs/reports.py
import discord # type: ignore
from discord import app_commands # type: ignore
from discord.ext import commands # type: ignore
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
from models.action import ActionStatus


class ReportsCog(commands.Cog):
    """Cog para geração de relatórios"""
    
    def __init__(self, bot):
        self.bot = bot
        self.action_service = bot.action_service
        self.config_service = bot.config_service
    
    def calculate_statistics(self, actions: List, guild_id: int) -> Dict:
        """Calcula estatísticas das ações"""
        stats = {
            'total_actions': len(actions),
            'completed_actions': 0,
            'victories': 0,
            'defeats': 0,
            'inactivities': 0,
            'participant_count': defaultdict(int),
            'victory_count': defaultdict(int),
            'escalator_count': defaultdict(int),
            'call_p1_count': defaultdict(int),
            'call_p2_count': defaultdict(int)
        }
        
        for action in actions:
            # Filtra apenas ações com resultado
            if not action.has_result():
                continue
            
            stats['completed_actions'] += 1
            
            if action.status == ActionStatus.VITORIA.value:
                stats['victories'] += 1
            elif action.status == ActionStatus.DERROTA.value:
                stats['defeats'] += 1
            elif action.status == ActionStatus.INATIVIDADE.value:
                stats['inactivities'] += 1
            
            # Contabiliza participações
            for participant_id in action.participant_ids:
                stats['participant_count'][participant_id] += 1
                
                # Contabiliza vitórias
                if action.status == ActionStatus.VITORIA.value:
                    stats['victory_count'][participant_id] += 1
            
            # Contabiliza escalações
            if action.escalator_id:
                stats['escalator_count'][action.escalator_id] += 1
            
            # Contabiliza calls
            if action.call_p1_id:
                stats['call_p1_count'][action.call_p1_id] += 1
            
            if action.call_p2_id:
                stats['call_p2_count'][action.call_p2_id] += 1
        
        return stats
    
    def create_report_embed(self, guild_id: int, stats: Dict, 
                           title: str, description: str, 
                           color: discord.Color) -> discord.Embed:
        """Cria embed de relatório"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        
        # Resumo geral
        embed.add_field(
            name="📈 Resumo Geral",
            value=f"**Total de Ações**: {stats['total_actions']}\n"
                  f"**Ações Finalizadas**: {stats['completed_actions']}\n"
                  f"**Vitórias**: {stats['victories']} 🏆\n"
                  f"**Derrotas**: {stats['defeats']} 💀\n"
                  f"**Inatividades**: {stats['inactivities']} ⏰",
            inline=False
        )
        
        # Taxa de vitória
        if stats['completed_actions'] > 0:
            # Remove inatividades do cálculo de taxa de vitória
            completed_with_result = stats['victories'] + stats['defeats']
            if completed_with_result > 0:
                win_rate = (stats['victories'] / completed_with_result) * 100
                embed.add_field(
                    name="📊 Taxa de Vitória",
                    value=f"{win_rate:.1f}%",
                    inline=True
                )
            
            # Média de participantes por ação
            total_participations = sum(stats['participant_count'].values())
            if stats['completed_actions'] > 0:
                avg_participants = total_participations / stats['completed_actions']
                embed.add_field(
                    name="👥 Média de Participantes",
                    value=f"{avg_participants:.1f} por ação",
                    inline=True
                )
        
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        
        # Top participantes
        if stats['participant_count']:
            sorted_participants = sorted(
                stats['participant_count'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            participant_lines = []
            for rank, (user_id, count) in enumerate(sorted_participants, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}º"
                participant_lines.append(f"{medal} <@{user_id}>: {count} ações")
            
            embed.add_field(
                name="👥 Top Participantes",
                value="\n".join(participant_lines),
                inline=False
            )
        
        # Top vitórias
        if stats['victory_count']:
            sorted_victories = sorted(
                stats['victory_count'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            victory_lines = []
            for rank, (user_id, count) in enumerate(sorted_victories, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}º"
                victory_lines.append(f"{medal} <@{user_id}>: {count} vitórias")
            
            embed.add_field(
                name="🏆 Top Vitórias",
                value="\n".join(victory_lines),
                inline=False
            )
        
        # Top escaladores
        if stats['escalator_count']:
            sorted_escalators = sorted(
                stats['escalator_count'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            escalator_lines = []
            for rank, (user_id, count) in enumerate(sorted_escalators, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}º"
                escalator_lines.append(f"{medal} <@{user_id}>: {count} escalações")
            
            embed.add_field(
                name="📋 Top Escaladores",
                value="\n".join(escalator_lines),
                inline=False
            )
        
        embed.set_footer(text="Relatório gerado automaticamente")
        
        return embed
    
    async def generate_daily_report(self, guild_id: int) -> discord.Embed:
        """Gera relatório diário"""
        # Carrega ações das últimas 24h
        history = self.action_service.load_history(days=1)
        
        # Filtra ações do servidor
        actions = [a for a in history if a.guild_id == guild_id]
        
        stats = self.calculate_statistics(actions, guild_id)
        
        return self.create_report_embed(
            guild_id,
            stats,
            "📊 Relatório Diário",
            "Estatísticas das últimas 24 horas",
            discord.Color.blue()
        )
    
    async def generate_weekly_report(self, guild_id: int) -> discord.Embed:
        """Gera relatório semanal"""
        # Carrega ações dos últimos 7 dias
        history = self.action_service.load_history(days=7)
        
        # Filtra ações do servidor
        actions = [a for a in history if a.guild_id == guild_id]
        
        stats = self.calculate_statistics(actions, guild_id)
        
        return self.create_report_embed(
            guild_id,
            stats,
            "📊 Relatório Semanal",
            "Estatísticas dos últimos 7 dias",
            discord.Color.gold()
        )
    
    async def generate_custom_report(self, guild_id: int, days: int) -> discord.Embed:
        """Gera relatório personalizado"""
        # Carrega ações do período especificado
        history = self.action_service.load_history(days=days)
        
        # Filtra ações do servidor
        actions = [a for a in history if a.guild_id == guild_id]
        
        stats = self.calculate_statistics(actions, guild_id)
        
        return self.create_report_embed(
            guild_id,
            stats,
            f"📊 Relatório Personalizado ({days} dias)",
            f"Estatísticas dos últimos {days} dias",
            discord.Color.purple()
        )
    
    @app_commands.command(name="relatorio_diario", description="Gera um relatório das ações do dia")
    async def relatorio_diario(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = await self.generate_daily_report(interaction.guild.id)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="relatorio_semanal", description="Gera um relatório das ações da semana")
    async def relatorio_semanal(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = await self.generate_weekly_report(interaction.guild.id)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="relatorio_personalizado", description="Gera um relatório personalizado")
    @app_commands.describe(dias="Número de dias para analisar")
    async def relatorio_personalizado(self, interaction: discord.Interaction, dias: int):
        if dias < 1 or dias > 365:
            await interaction.response.send_message(
                "⚠️ Por favor, escolha um período entre 1 e 365 dias.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        embed = await self.generate_custom_report(interaction.guild.id, dias)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReportsCog(bot))