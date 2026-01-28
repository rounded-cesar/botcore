import discord
from discord.ui import View, button, select, Modal, TextInput
from utils import (
    create_success_embed,
    create_error_embed,
    create_config_embed
)

# =========================
# VIEW PRINCIPAL
# =========================

class ConfigMainView(View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.config_service = bot.config_service

    @button(label="📺 Canais", style=discord.ButtonStyle.primary)
    async def canais(self, interaction: discord.Interaction, _):
        embed = discord.Embed(
            title="📺 Configuração de Canais",
            description="Selecione abaixo qual canal deseja configurar.",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigChannelView(self.bot)
        )

    @button(label="🎖️ Cargos", style=discord.ButtonStyle.primary)
    async def cargos(self, interaction: discord.Interaction, _):
        embed = discord.Embed(
            title="🎖️ Configuração de Cargos",
            description="Gerencie cargos de escalação e administrativos.",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigRoleView(self.bot)
        )

    @button(label="⏱️ Tempos", style=discord.ButtonStyle.primary)
    async def tempos(self, interaction: discord.Interaction, _):
        embed = discord.Embed(
            title="⏱️ Configuração de Tempos",
            description="Configure inatividade e avisos automáticos.",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigTimeView(self.bot)
        )

    @button(label="📄 Ver Configurações", style=discord.ButtonStyle.secondary)
    async def ver(self, interaction: discord.Interaction, _):
        config = self.config_service.get_server_config(interaction.guild.id)
        embed = create_config_embed(config, interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)


# =========================
# CANAIS
# =========================

class ConfigChannelView(View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.config_service = bot.config_service

    @select(
        placeholder="📢 Canal de Ações",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def canal_acoes(self, interaction: discord.Interaction, select):
        canal = select.values[0]
        self.config_service.set_action_channel(interaction.guild.id, canal.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Canal de ações configurado: {canal.mention}"),
            ephemeral=True
        )

    @select(
        placeholder="📋 Canal de Escalações",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def canal_escalacoes(self, interaction: discord.Interaction, select):
        canal = select.values[0]
        self.config_service.set_escalation_channel(interaction.guild.id, canal.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Canal de escalações configurado: {canal.mention}"),
            ephemeral=True
        )

    @select(
        placeholder="📑 Canal de Relatórios",
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text]
    )
    async def canal_relatorios(self, interaction: discord.Interaction, select):
        canal = select.values[0]
        self.config_service.set_report_channel(interaction.guild.id, canal.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Canal de relatórios configurado: {canal.mention}"),
            ephemeral=True
        )

    @button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary)
    async def voltar(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚙️ Painel de Configurações",
                description="Escolha uma categoria abaixo.",
                color=discord.Color.blurple()
            ),
            view=ConfigMainView(self.bot)
        )


# =========================
# CARGOS
# =========================

class ConfigRoleView(View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        self.config_service = bot.config_service

    @select(
        placeholder="➕ Adicionar cargo de escalação",
        cls=discord.ui.RoleSelect
    )
    async def add_escalation_role(self, interaction: discord.Interaction, select):
        role = select.values[0]
        self.config_service.add_escalation_role(interaction.guild.id, role.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {role.mention} adicionado à escalação."),
            ephemeral=True
        )

    @select(
        placeholder="➖ Remover cargo de escalação",
        cls=discord.ui.RoleSelect
    )
    async def remove_escalation_role(self, interaction: discord.Interaction, select):
        role = select.values[0]
        self.config_service.remove_escalation_role(interaction.guild.id, role.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {role.mention} removido da escalação."),
            ephemeral=True
        )

    @select(
        placeholder="⭐ Adicionar cargo admin",
        cls=discord.ui.RoleSelect
    )
    async def add_admin_role(self, interaction: discord.Interaction, select):
        role = select.values[0]
        self.config_service.add_admin_role(interaction.guild.id, role.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {role.mention} adicionado como admin."),
            ephemeral=True
        )

    @select(
        placeholder="❌ Remover cargo admin",
        cls=discord.ui.RoleSelect
    )
    async def remove_admin_role(self, interaction: discord.Interaction, select):
        role = select.values[0]
        self.config_service.remove_admin_role(interaction.guild.id, role.id)
        await interaction.response.send_message(
            embed=create_success_embed(f"Cargo {role.mention} removido dos admins."),
            ephemeral=True
        )

    @button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary)
    async def voltar(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚙️ Painel de Configurações",
                description="Escolha uma categoria abaixo.",
                color=discord.Color.blurple()
            ),
            view=ConfigMainView(self.bot)
        )


# =========================
# TEMPOS
# =========================

class ConfigTimeView(View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @button(label="⏳ Inatividade", style=discord.ButtonStyle.primary)
    async def inactivity(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(InactivityModal(self.bot))

    @button(label="⚠️ Aviso de Inatividade", style=discord.ButtonStyle.primary)
    async def warning(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(WarningModal(self.bot))

    @button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary)
    async def voltar(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚙️ Painel de Configurações",
                description="Escolha uma categoria abaixo.",
                color=discord.Color.blurple()
            ),
            view=ConfigMainView(self.bot)
        )


# =========================
# MODALS
# =========================

class InactivityModal(Modal, title="Configurar Inatividade"):
    horas = TextInput(
        label="Horas até marcar ação como inativa",
        placeholder="Ex: 24",
        min_length=1,
        max_length=3
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        horas = int(self.horas.value)

        if horas < 1 or horas > 168:
            await interaction.response.send_message(
                embed=create_error_embed("Escolha um valor entre 1 e 168 horas."),
                ephemeral=True
            )
            return

        self.bot.config_service.set_inactivity_hours(interaction.guild.id, horas)
        await interaction.response.send_message(
            embed=create_success_embed(f"Inatividade configurada para {horas}h."),
            ephemeral=True
        )


class WarningModal(Modal, title="Configurar Aviso de Inatividade"):
    horas = TextInput(
        label="Horas até enviar aviso",
        placeholder="Ex: 20",
        min_length=1,
        max_length=3
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        horas = int(self.horas.value)

        if horas < 1 or horas > 168:
            await interaction.response.send_message(
                embed=create_error_embed("Escolha um valor entre 1 e 168 horas."),
                ephemeral=True
            )
            return

        self.bot.config_service.set_warning_hours(interaction.guild.id, horas)
        await interaction.response.send_message(
            embed=create_success_embed(f"Aviso configurado para {horas}h."),
            ephemeral=True
        )
