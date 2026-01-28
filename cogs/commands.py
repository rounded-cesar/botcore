# cogs/commands.py
import discord # type: ignore
from discord import app_commands # type: ignore
from discord.ext import commands # type: ignore
from utils import create_config_embed, create_error_embed, create_success_embed, create_action_embed
from cogs.action_views import ActionView


class CommandsCog(commands.Cog):
    """Cog com todos os comandos do bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.action_service = bot.action_service
        self.config_service = bot.config_service
    
    @app_commands.command(name="configurar_canal_acoes", description="Define o canal onde as ações são anunciadas")
    @app_commands.describe(canal="Canal de origem das ações")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_canal_acoes(self, interaction: discord.Interaction, canal: discord.TextChannel):
        self.config_service.set_action_channel(interaction.guild.id, canal.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Canal de ações configurado: {canal.mention}"),
            ephemeral=True
        )
    
    @app_commands.command(name="configurar_canal_escalacoes", description="Define o canal onde as escalações serão gerenciadas")
    @app_commands.describe(canal="Canal de escalações")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_canal_escalacoes(self, interaction: discord.Interaction, canal: discord.TextChannel):
        self.config_service.set_escalation_channel(interaction.guild.id, canal.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Canal de escalações configurado: {canal.mention}"),
            ephemeral=True
        )
    
    @app_commands.command(name="configurar_canal_relatorios", description="Define o canal onde os relatórios serão enviados")
    @app_commands.describe(canal="Canal de relatórios")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_canal_relatorios(self, interaction: discord.Interaction, canal: discord.TextChannel):
        self.config_service.set_report_channel(interaction.guild.id, canal.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Canal de relatórios configurado: {canal.mention}"),
            ephemeral=True
        )
    
    @app_commands.command(name="adicionar_cargo_escalacao", description="Adiciona um cargo permitido para assumir escalações")
    @app_commands.describe(cargo="Cargo que poderá assumir escalações")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_role(self, interaction: discord.Interaction, cargo: discord.Role):
        self.config_service.add_escalation_role(interaction.guild.id, cargo.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {cargo.mention} adicionado à lista de escalação!"),
            ephemeral=True
        )
    
    @app_commands.command(name="remover_cargo_escalacao", description="Remove um cargo da lista de escalação")
    @app_commands.describe(cargo="Cargo a ser removido")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_role(self, interaction: discord.Interaction, cargo: discord.Role):
        self.config_service.remove_escalation_role(interaction.guild.id, cargo.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {cargo.mention} removido da lista de escalação!"),
            ephemeral=True
        )
    
    @app_commands.command(name="adicionar_cargo_admin", description="Adiciona um cargo com acesso administrativo")
    @app_commands.describe(cargo="Cargo admin")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_admin_role(self, interaction: discord.Interaction, cargo: discord.Role):
        self.config_service.add_admin_role(interaction.guild.id, cargo.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {cargo.mention} adicionado como admin!"),
            ephemeral=True
        )
    
    @app_commands.command(name="remover_cargo_admin", description="Remove um cargo admin")
    @app_commands.describe(cargo="Cargo a ser removido")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_admin_role(self, interaction: discord.Interaction, cargo: discord.Role):
        self.config_service.remove_admin_role(interaction.guild.id, cargo.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {cargo.mention} removido dos admins!"),
            ephemeral=True
        )
    
    @app_commands.command(name="configurar_inatividade", description="Define horas até marcar ação como inativa")
    @app_commands.describe(horas="Número de horas (padrão: 24)")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_inatividade(self, interaction: discord.Interaction, horas: int):
        if horas < 1 or horas > 168:  # Máximo 1 semana
            await interaction.response.send_message(
                embed=create_error_embed("Por favor, escolha um valor entre 1 e 168 horas!"),
                ephemeral=True
            )
            return
        
        self.config_service.set_inactivity_hours(interaction.guild.id, horas)
        await interaction.response.send_message(
            embed=create_success_embed(f"Inatividade automática configurada para {horas}h"),
            ephemeral=True
        )
    
    @app_commands.command(name="configurar_aviso_inatividade", description="Define horas até enviar aviso de inatividade")
    @app_commands.describe(horas="Número de horas (padrão: 20)")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_aviso(self, interaction: discord.Interaction, horas: int):
        if horas < 1 or horas > 168:
            await interaction.response.send_message(
                embed=create_error_embed("Por favor, escolha um valor entre 1 e 168 horas!"),
                ephemeral=True
            )
            return
        
        self.config_service.set_warning_hours(interaction.guild.id, horas)
        await interaction.response.send_message(
            embed=create_success_embed(f"Aviso de inatividade configurado para {horas}h"),
            ephemeral=True
        )
    
    @app_commands.command(name="ver_configuracoes", description="Visualiza as configurações atuais do servidor")
    async def ver_configs(self, interaction: discord.Interaction):
        config = self.config_service.get_server_config(interaction.guild.id)
        embed = create_config_embed(config, interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="listar_cargos_escalacao", description="Lista todos os cargos permitidos para escalação")
    async def list_roles(self, interaction: discord.Interaction):
        escalation_roles = self.config_service.get_escalation_roles(interaction.guild.id)
        
        embed = discord.Embed(
            title="🎖️ Cargos Permitidos para Escalação",
            description="Membros com estes cargos podem assumir escalações em ações que requerem cargo específico",
            color=discord.Color.gold()
        )
        
        if escalation_roles:
            role_list = []
            for role_id in escalation_roles:
                role = interaction.guild.get_role(role_id)
                if role:
                    role_list.append(f"• {role.mention}")
            
            if role_list:
                embed.add_field(name="Cargos Configurados", value="\n".join(role_list), inline=False)
            else:
                embed.add_field(name="Cargos Configurados", value="Nenhum cargo válido encontrado", inline=False)
        else:
            embed.add_field(name="Cargos Configurados", value="Nenhum cargo configurado ainda", inline=False)
            embed.add_field(
                name="Como configurar?",
                value="Use o comando `/adicionar_cargo_escalacao` para adicionar cargos",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="listar_tipos_acoes", description="Lista todos os tipos de ações configuradas")
    async def listar_acoes(self, interaction: discord.Interaction):
        action_types = self.config_service.action_types
        
        # Filtra ações
        actions = {k: v for k, v in action_types.items()}
        
        # Cria descrição em texto formatado
        description_lines = ["**Lista de todas as ações configuradas:**\n"]
        
        for action_key, config in actions.items():
            requires_roles = "🔒 Requer Cargo" if config.get('required_roles', False) else "🆓 Livre"
            call_p1 = "P1✅" if config.get('has_call_p1') else "P1❌"
            call_p2 = "P2✅" if config.get('has_call_p2') else "P2❌"
            
            description_lines.append(
                f"**🔹 {action_key}**\n"
                f"├ {config['display_name']} | "
                f"👥 {config['max_participants']} máx | "
                f"{call_p1} {call_p2} | "
                f"{requires_roles}\n"
            )
        
        embed = discord.Embed(
            title="📋 Tipos de Ações Configuradas",
            description="\n".join(description_lines),
            color=discord.Color.purple()
        )
        
        embed.set_footer(text="Use /listar_cargos_escalacao para ver os cargos configurados")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="criar_acao", description="Cria uma ação manualmente")
    @app_commands.describe(nome="Nome da ação")
    async def criar_acao(self, interaction: discord.Interaction, nome: str):
        config = self.config_service.get_server_config(interaction.guild.id)
        
        if not config['escalation_channel']:
            await interaction.response.send_message(
                embed=create_error_embed("Canal de escalações não configurado! Use `/configurar_canal_escalacoes`"),
                ephemeral=True
            )
            return
        
        channel = interaction.guild.get_channel(config['escalation_channel'])
        if not channel:
            await interaction.response.send_message(
                embed=create_error_embed("Canal de escalações não encontrado!"),
                ephemeral=True
            )
            return
        
        # Obtém config da ação
        action_type = self.config_service.get_action_type_key(nome)
        action_config = self.config_service.get_action_config(nome)
        
        # Cria embed
        embed = discord.Embed(
            title="🚨 Nova Ação Criada",
            description=f"**{nome}**",
            color=discord.Color.red()
        )
        embed.add_field(name="Status", value="🟢 ABERTA", inline=False)
        embed.add_field(name="Criada por", value=interaction.user.mention, inline=False)
        
        # Envia mensagem
        view = ActionView(self.bot, "temp")  # Temporário
        message = await channel.send(embed=embed, view=view)
        
        # Cria ação no service
        action = await self.action_service.create_action(
            guild_id=interaction.guild.id,
            action_name=nome,
            action_type=action_type,
            config=action_config,
            channel_id=channel.id,
            message_id=message.id
        )
        
        # Atualiza view com ID correto
        final_view = ActionView(self.bot, action.action_id)
        self.bot.add_view(final_view)
        
        # Atualiza mensagem com embed e view corretos
        final_embed = create_action_embed(action, interaction.guild)
        await message.edit(embed=final_embed, view=final_view)
        
        await interaction.response.send_message(
            embed=create_success_embed(f"Ação **{nome}** criada com sucesso!"),
            ephemeral=True
        )
    
    @app_commands.command(name="listar_acoes_ativas", description="Lista todas as ações ativas do servidor")
    async def listar_acoes_ativas(self, interaction: discord.Interaction):
        actions = self.action_service.get_guild_actions(interaction.guild.id, include_closed=False)
        
        if not actions:
            await interaction.response.send_message(
                embed=create_error_embed("Não há ações ativas no momento."),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📋 Ações Ativas",
            description=f"Total: {len(actions)} ações",
            color=discord.Color.blue()
        )
        
        for action in actions[:25]:  # Limita a 25
            escalator = f"<@{action.escalator_id}>" if action.escalator_id else "Sem escalador"
            embed.add_field(
                name=f"🚨 {action.action_name}",
                value=f"Escalador: {escalator}\n"
                      f"Participantes: {len(action.participant_ids)}/{action.max_participants}\n"
                      f"ID: `{action.action_id}`",
                inline=False
            )
        
        if len(actions) > 25:
            embed.set_footer(text=f"Mostrando 25 de {len(actions)} ações")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))