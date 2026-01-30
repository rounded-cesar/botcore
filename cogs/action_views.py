# cogs/action_views.py
import discord
from discord import ui
from typing import Optional
from utils import (
    create_action_embed, create_error_embed, create_success_embed,
    can_escalate, is_escalator, can_manage_action, get_missing_roles_text
)
import asyncio


class ActionView(ui.View):
    """View persistente para ações - sobrevive a reinicializações"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        self.config_service = bot.config_service
        
        # Cooldown para prevenir spam
        self._cooldowns = {}
        
        # Adiciona botões dinamicamente
        self._setup_buttons()
    
    def _setup_buttons(self):
        """Configura botões baseado na configuração da ação"""
        action = self.action_service.get_action(self.action_id)
        if not action:
            return
        
        # Remove todos os botões existentes
        self.clear_items()
        
        # Botão de escalador (sempre presente)
        self.add_item(self.create_escalator_button())
        
        # Botões de Call baseado na configuração
        if action.has_call_p1 and action.has_call_p2:
            # Tem P1 e P2 - mostra ambos
            self.add_item(self.create_call_p1_button())
            self.add_item(self.create_call_p2_button())
        elif action.has_call_p1 and not action.has_call_p2:
            # Tem apenas P1 - mostra Call genérico
            self.add_item(self.create_call_single_button())
        
        # Botões de participar/sair
        self.add_item(self.create_join_button())
        self.add_item(self.create_leave_button())
        
        # Painel de escalação (se tiver escalador)
        if action.escalator_id:
            self.add_item(self.create_panel_button())
    
    def create_escalator_button(self):
        """Cria botão de escalador"""
        button = ui.Button(
            label="📋 Assumir Escalação",
            style=discord.ButtonStyle.primary,
            custom_id="action:escalator",
            row=0
        )
        button.callback = self.escalator_button_callback
        return button
    
    def create_call_p1_button(self):
        """Cria botão de Call P1"""
        button = ui.Button(
            label="📞 Call P1",
            style=discord.ButtonStyle.primary,
            custom_id="action:call_p1",
            row=0
        )
        button.callback = self.call_p1_callback
        return button
    
    def create_call_p2_button(self):
        """Cria botão de Call P2"""
        button = ui.Button(
            label="📞 Call P2",
            style=discord.ButtonStyle.primary,
            custom_id="action:call_p2",
            row=0
        )
        button.callback = self.call_p2_callback
        return button
    
    def create_call_single_button(self):
        """Cria botão de Call único"""
        button = ui.Button(
            label="📞 Call",
            style=discord.ButtonStyle.primary,
            custom_id="action:call_single",
            row=0
        )
        button.callback = self.call_single_callback
        return button
    
    def create_join_button(self):
        """Cria botão de entrar"""
        button = ui.Button(
            label="✅ Entrar na Ação",
            style=discord.ButtonStyle.success,
            custom_id="action:join",
            row=1
        )
        button.callback = self.join_callback
        return button
    
    def create_leave_button(self):
        """Cria botão de sair"""
        button = ui.Button(
            label="❌ Sair da Ação",
            style=discord.ButtonStyle.danger,
            custom_id="action:leave",
            row=1
        )
        button.callback = self.leave_callback
        return button
    
    def create_panel_button(self):
        """Cria botão do painel"""
        button = ui.Button(
            label="⚙️ Painel de Escalação",
            style=discord.ButtonStyle.secondary,
            custom_id="action:panel",
            row=2
        )
        button.callback = self.panel_callback
        return button
    
    async def check_cooldown(self, user_id: int) -> bool:
        """Verifica cooldown do usuário (anti-spam)"""
        import time
        current_time = time.time()
        
        if user_id in self._cooldowns:
            if current_time - self._cooldowns[user_id] < 2:  # 2 segundos
                return False
        
        self._cooldowns[user_id] = current_time
        return True
    
    async def update_message(self, interaction: discord.Interaction):
        """Atualiza a mensagem da ação"""
        action = self.action_service.get_action(self.action_id)
        if not action:
            return
        
        embed = create_action_embed(action, interaction.guild)
        
        # Recria a view com botões atualizados
        new_view = ActionView(self.bot, self.action_id)
        
        try:
            await interaction.message.edit(embed=embed, view=new_view)
        except:
            pass
    
    async def escalator_button_callback(self, interaction: discord.Interaction):
        """Botão para assumir escalação"""
        # Verifica cooldown
        if not await self.check_cooldown(interaction.user.id):
            await interaction.response.send_message(
                "⏱️ Aguarde alguns segundos antes de clicar novamente!",
                ephemeral=True
            )
            return
        
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Verifica se já tem escalador
        if action.escalator_id:
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação já possui um escalador!"),
                ephemeral=True
            )
            return
        
        # Verifica se está fechada
        if not action.is_open():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação está fechada!"),
                ephemeral=True
            )
            return
        
        # Verifica permissões
        if not can_escalate(interaction.user, interaction.guild.id, action, self.config_service):
            missing_roles = get_missing_roles_text(interaction.user, interaction.guild.id, self.config_service)
            await interaction.response.send_message(
                embed=create_error_embed(
                    f"Você não tem permissão para assumir esta escalação!\n{missing_roles}",
                    "Permissão Negada"
                ),
                ephemeral=True
            )
            return
        
        # Define escalador
        success = await self.action_service.set_escalator(self.action_id, interaction.user.id)
        
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    f"Você assumiu a escalação de **{action.action_name}**!"
                ),
                ephemeral=True
            )
            await self.update_message(interaction)
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível assumir a escalação!"),
                ephemeral=True
            )
    
    async def call_p1_callback(self, interaction: discord.Interaction):
        """Botão para assumir Call P1"""
        if not await self.check_cooldown(interaction.user.id):
            await interaction.response.send_message(
                "⏱️ Aguarde alguns segundos antes de clicar novamente!",
                ephemeral=True
            )
            return
        
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Verifica se já está ocupada
        if action.call_p1_id:
            await interaction.response.send_message(
                embed=create_error_embed("Call P1 já está ocupada!"),
                ephemeral=True
            )
            return
        
        # Verifica se está fechada
        if not action.is_open():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação está fechada!"),
                ephemeral=True
            )
            return
        
        # Define Call P1
        success = await self.action_service.set_call_p1(self.action_id, interaction.user.id)
        
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    f"Você assumiu a Call P1 de **{action.action_name}**!"
                ),
                ephemeral=True
            )
            await self.update_message(interaction)
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível assumir a Call P1!"),
                ephemeral=True
            )
    
    async def call_p2_callback(self, interaction: discord.Interaction):
        """Botão para assumir Call P2"""
        if not await self.check_cooldown(interaction.user.id):
            await interaction.response.send_message(
                "⏱️ Aguarde alguns segundos antes de clicar novamente!",
                ephemeral=True
            )
            return
        
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Verifica se já está ocupada
        if action.call_p2_id:
            await interaction.response.send_message(
                embed=create_error_embed("Call P2 já está ocupada!"),
                ephemeral=True
            )
            return
        
        # Verifica se está fechada
        if not action.is_open():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação está fechada!"),
                ephemeral=True
            )
            return
        
        # Define Call P2
        success = await self.action_service.set_call_p2(self.action_id, interaction.user.id)
        
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    f"Você assumiu a Call P2 de **{action.action_name}**!"
                ),
                ephemeral=True
            )
            await self.update_message(interaction)
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível assumir a Call P2!"),
                ephemeral=True
            )
    
    async def call_single_callback(self, interaction: discord.Interaction):
        """Botão para assumir Call única (quando não há P1/P2)"""
        if not await self.check_cooldown(interaction.user.id):
            await interaction.response.send_message(
                "⏱️ Aguarde alguns segundos antes de clicar novamente!",
                ephemeral=True
            )
            return
        
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Verifica se já está ocupada
        if action.call_p1_id:
            await interaction.response.send_message(
                embed=create_error_embed("Call já está ocupada!"),
                ephemeral=True
            )
            return
        
        # Verifica se está fechada
        if not action.is_open():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação está fechada!"),
                ephemeral=True
            )
            return
        
        # Define Call (usa P1 internamente)
        success = await self.action_service.set_call_p1(self.action_id, interaction.user.id)
        
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    f"Você assumiu a Call de **{action.action_name}**!"
                ),
                ephemeral=True
            )
            await self.update_message(interaction)
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível assumir a Call!"),
                ephemeral=True
            )
    
    async def join_callback(self, interaction: discord.Interaction):
        """Botão para entrar na ação"""
        if not await self.check_cooldown(interaction.user.id):
            await interaction.response.send_message(
                "⏱️ Aguarde alguns segundos antes de clicar novamente!",
                ephemeral=True
            )
            return
        
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Verifica se está fechada
        if not action.is_open():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação está fechada!"),
                ephemeral=True
            )
            return
        
        # Verifica se já está na ação
        if interaction.user.id in action.participant_ids:
            await interaction.response.send_message(
                embed=create_error_embed("Você já está nesta ação!"),
                ephemeral=True
            )
            return
        
        # Verifica se está cheia
        if action.is_full():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação está cheia!"),
                ephemeral=True
            )
            return
        
        # Adiciona participante
        success = await self.action_service.add_participant(self.action_id, interaction.user.id)
        
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    f"Você entrou na ação **{action.action_name}**!"
                ),
                ephemeral=True
            )
            await self.update_message(interaction)
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível entrar na ação!"),
                ephemeral=True
            )
    
    async def leave_callback(self, interaction: discord.Interaction):
        """Botão para sair da ação"""
        if not await self.check_cooldown(interaction.user.id):
            await interaction.response.send_message(
                "⏱️ Aguarde alguns segundos antes de clicar novamente!",
                ephemeral=True
            )
            return
        
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Verifica se está na ação
        if interaction.user.id not in action.participant_ids:
            await interaction.response.send_message(
                embed=create_error_embed("Você não está nesta ação!"),
                ephemeral=True
            )
            return
        
        # Remove participante
        success = await self.action_service.remove_participant(self.action_id, interaction.user.id)
        
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    f"Você saiu da ação **{action.action_name}**!"
                ),
                ephemeral=True
            )
            await self.update_message(interaction)
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível sair da ação!"),
                ephemeral=True
            )
    
    async def panel_callback(self, interaction: discord.Interaction):
        """Botão para abrir painel de gerenciamento"""
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Verifica permissões
        if not can_manage_action(interaction.user, interaction.guild.id, action, self.config_service):
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Apenas o escalador ou administradores podem acessar este painel!",
                    "Permissão Negada"
                ),
                ephemeral=True
            )
            return
        
        # Abre o painel
        view = ManagementPanelView(self.bot, self.action_id)
        embed = discord.Embed(
            title="⚙️ Painel de Gerenciamento",
            description=f"**Ação:** {action.action_name}\n**Status:** {action.status.upper()}",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ManagementPanelView(ui.View):
    """Painel de gerenciamento unificado"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=300)  # 5 minutos
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        self.config_service = bot.config_service
    
    @ui.button(label="👤 Gerenciar Escalador", style=discord.ButtonStyle.primary, row=0)
    async def manage_escalator(self, interaction: discord.Interaction, button: ui.Button):
        """Gerencia o escalador"""
        await interaction.response.send_message(
            "Selecione uma ação:",
            view=ManageEscalatorView(self.bot, self.action_id),
            ephemeral=True
        )
    
    @ui.button(label="📞 Gerenciar Calls", style=discord.ButtonStyle.primary, row=0)
    async def manage_calls(self, interaction: discord.Interaction, button: ui.Button):
        """Gerencia calls"""
        await interaction.response.send_message(
            "Selecione uma ação:",
            view=ManageCallsView(self.bot, self.action_id),
            ephemeral=True
        )
    
    @ui.button(label="➕ Adicionar Participante", style=discord.ButtonStyle.primary, row=1)
    async def add_participant(self, interaction: discord.Interaction, button: ui.Button):
        """Adiciona participante manualmente"""
        await interaction.response.send_message(
            "Selecione o usuário para adicionar:",
            view=AddParticipantView(self.bot, self.action_id),
            ephemeral=True
        )
    
    @ui.button(label="➖ Remover Participante", style=discord.ButtonStyle.primary, row=1)
    async def remove_participant(self, interaction: discord.Interaction, button: ui.Button):
        """Remove participante manualmente"""
        action = self.action_service.get_action(self.action_id)
        if not action or not action.participant_ids:
            await interaction.response.send_message(
                embed=create_error_embed("Não há participantes para remover!"),
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            "Selecione o participante para remover:",
            view=RemoveParticipantView(self.bot, self.action_id),
            ephemeral=True
        )
    
    @ui.button(label="🔒 Fechar Escalação", style=discord.ButtonStyle.secondary, row=2)
    async def close_action(self, interaction: discord.Interaction, button: ui.Button):
        """Fecha a escalação"""
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        if not action.is_open():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação já está fechada!"),
                ephemeral=True
            )
            return
        
        # Confirmação
        await interaction.response.send_message(
            "⚠️ Tem certeza que deseja fechar a escalação?",
            view=ConfirmCloseView(self.bot, self.action_id),
            ephemeral=True
        )
    
    @ui.button(label="🔓 Reabrir Ação", style=discord.ButtonStyle.secondary, row=2)
    async def reopen_action(self, interaction: discord.Interaction, button: ui.Button):
        """Reabre a ação"""
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        if action.has_result():
            await interaction.response.send_message(
                embed=create_error_embed("Não é possível reabrir uma ação com resultado definido!"),
                ephemeral=True
            )
            return
        
        if action.is_open():
            await interaction.response.send_message(
                embed=create_error_embed("Esta ação já está aberta!"),
                ephemeral=True
            )
            return
        
        success = await self.action_service.reopen_action(self.action_id)
        if success:
            # Atualiza mensagem original
            channel = interaction.guild.get_channel(action.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(action.message_id)
                    embed = create_action_embed(action, interaction.guild)
                    view = ActionView(self.bot, self.action_id)
                    await message.edit(embed=embed, view=view)
                except:
                    pass
            
            await interaction.response.send_message(
                embed=create_success_embed("Ação reaberta com sucesso!"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível reabrir a ação!"),
                ephemeral=True
            )
    
    @ui.button(label="🏆 Definir Vitória", style=discord.ButtonStyle.success, row=3)
    async def set_victory(self, interaction: discord.Interaction, button: ui.Button):
        """Define resultado como vitória"""
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        if not action.can_set_result():
            await interaction.response.send_message(
                embed=create_error_embed("A ação precisa estar fechada antes de definir resultado!"),
                ephemeral=True
            )
            return
        
        success = await self.action_service.set_result(self.action_id, "victory", interaction.user.id)
        if success:
            # Atualiza mensagem original
            channel = interaction.guild.get_channel(action.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(action.message_id)
                    embed = create_action_embed(action, interaction.guild)
                    await message.edit(embed=embed, view=None)  # Remove botões
                except:
                    pass
            
            await interaction.response.send_message(
                embed=create_success_embed("🏆 Vitória registrada!"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível registrar a vitória!"),
                ephemeral=True
            )
    
    @ui.button(label="💀 Definir Derrota", style=discord.ButtonStyle.danger, row=3)
    async def set_defeat(self, interaction: discord.Interaction, button: ui.Button):
        """Define resultado como derrota"""
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        if not action.can_set_result():
            await interaction.response.send_message(
                embed=create_error_embed("A ação precisa estar fechada antes de definir resultado!"),
                ephemeral=True
            )
            return
        
        success = await self.action_service.set_result(self.action_id, "defeat", interaction.user.id)
        if success:
            # Atualiza mensagem original
            channel = interaction.guild.get_channel(action.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(action.message_id)
                    embed = create_action_embed(action, interaction.guild)
                    await message.edit(embed=embed, view=None)  # Remove botões
                except:
                    pass
            
            await interaction.response.send_message(
                embed=create_success_embed("💀 Derrota registrada!"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível registrar a derrota!"),
                ephemeral=True
            )
    
    @ui.button(label="🗑️ Apagar Ação", style=discord.ButtonStyle.danger, row=4)
    async def delete_action(self, interaction: discord.Interaction, button: ui.Button):
        """Apaga a ação completamente"""
        await interaction.response.send_message(
            "⚠️ **ATENÇÃO!** Tem certeza que deseja APAGAR esta ação? Esta operação não pode ser desfeita!",
            view=ConfirmDeleteView(self.bot, self.action_id),
            ephemeral=True
        )


class ManageEscalatorView(ui.View):
    """View para gerenciar o escalador"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        
        action = self.action_service.get_action(action_id)
        if action and action.escalator_id:
            # Se tem escalador, oferece remover
            remove_btn = ui.Button(label="❌ Remover Escalador", style=discord.ButtonStyle.danger)
            remove_btn.callback = self.remove_escalator_callback
            self.add_item(remove_btn)
        
        # Sempre oferece definir novo escalador
        define_btn = ui.Button(label="✅ Definir Escalador", style=discord.ButtonStyle.success)
        define_btn.callback = self.define_escalator_callback
        self.add_item(define_btn)
    
    async def remove_escalator_callback(self, interaction: discord.Interaction):
        """Remove o escalador atual"""
        action = self.action_service.get_action(self.action_id)
        if not action or not action.escalator_id:
            await interaction.response.send_message(
                embed=create_error_embed("Não há escalador para remover!"),
                ephemeral=True
            )
            return
        
        # Remove escalador
        action.escalator_id = None
        self.action_service.save_active_actions()
        self.action_service.save_to_history(action)
        
        # Atualiza mensagem
        channel = interaction.guild.get_channel(action.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(action.message_id)
                embed = create_action_embed(action, interaction.guild)
                view = ActionView(self.bot, self.action_id)
                await message.edit(embed=embed, view=view)
            except:
                pass
        
        await interaction.response.send_message(
            embed=create_success_embed("Escalador removido!"),
            ephemeral=True
        )
    
    async def define_escalator_callback(self, interaction: discord.Interaction):
        """Define novo escalador"""
        await interaction.response.send_message(
            "Selecione o novo escalador:",
            view=DefineEscalatorView(self.bot, self.action_id),
            ephemeral=True
        )


class DefineEscalatorView(ui.View):
    """View para definir escalador"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        
        # Adiciona UserSelect
        user_select = ui.UserSelect(
            placeholder="Selecione o escalador",
            min_values=1,
            max_values=1
        )
        user_select.callback = self.select_user_callback
        self.add_item(user_select)
    
    async def select_user_callback(self, interaction: discord.Interaction):
        select = [item for item in self.children if isinstance(item, ui.UserSelect)][0]
        user = select.values[0]
        
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Define novo escalador
        action.escalator_id = user.id
        self.action_service.save_active_actions()
        self.action_service.save_to_history(action)
        
        # Atualiza mensagem
        channel = interaction.guild.get_channel(action.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(action.message_id)
                embed = create_action_embed(action, interaction.guild)
                view = ActionView(self.bot, self.action_id)
                await message.edit(embed=embed, view=view)
            except:
                pass
        
        await interaction.response.send_message(
            embed=create_success_embed(f"{user.mention} definido como escalador!"),
            ephemeral=True
        )


class ManageCallsView(ui.View):
    """View para gerenciar calls"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        
        action = self.action_service.get_action(action_id)
        if not action:
            return
        
        # Botões para Call P1
        if action.has_call_p1:
            if action.call_p1_id:
                remove_p1 = ui.Button(label="❌ Remover Call P1", style=discord.ButtonStyle.danger, row=0)
                remove_p1.callback = self.remove_call_p1_callback
                self.add_item(remove_p1)
            
            define_p1 = ui.Button(label="✅ Definir Call P1", style=discord.ButtonStyle.success, row=0)
            define_p1.callback = self.define_call_p1_callback
            self.add_item(define_p1)
        
        # Botões para Call P2
        if action.has_call_p2:
            if action.call_p2_id:
                remove_p2 = ui.Button(label="❌ Remover Call P2", style=discord.ButtonStyle.danger, row=1)
                remove_p2.callback = self.remove_call_p2_callback
                self.add_item(remove_p2)
            
            define_p2 = ui.Button(label="✅ Definir Call P2", style=discord.ButtonStyle.success, row=1)
            define_p2.callback = self.define_call_p2_callback
            self.add_item(define_p2)
    
    async def remove_call_p1_callback(self, interaction: discord.Interaction):
        action = self.action_service.get_action(self.action_id)
        if not action or not action.call_p1_id:
            await interaction.response.send_message(
                embed=create_error_embed("Não há Call P1 para remover!"),
                ephemeral=True
            )
            return
        
        action.call_p1_id = None
        self.action_service.save_active_actions()
        self.action_service.save_to_history(action)
        
        channel = interaction.guild.get_channel(action.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(action.message_id)
                embed = create_action_embed(action, interaction.guild)
                view = ActionView(self.bot, self.action_id)
                await message.edit(embed=embed, view=view)
            except:
                pass
        
        await interaction.response.send_message(
            embed=create_success_embed("Call P1 removido!"),
            ephemeral=True
        )
    
    async def remove_call_p2_callback(self, interaction: discord.Interaction):
        action = self.action_service.get_action(self.action_id)
        if not action or not action.call_p2_id:
            await interaction.response.send_message(
                embed=create_error_embed("Não há Call P2 para remover!"),
                ephemeral=True
            )
            return
        
        action.call_p2_id = None
        self.action_service.save_active_actions()
        self.action_service.save_to_history(action)
        
        channel = interaction.guild.get_channel(action.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(action.message_id)
                embed = create_action_embed(action, interaction.guild)
                view = ActionView(self.bot, self.action_id)
                await message.edit(embed=embed, view=view)
            except:
                pass
        
        await interaction.response.send_message(
            embed=create_success_embed("Call P2 removido!"),
            ephemeral=True
        )
    
    async def define_call_p1_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Selecione o Call P1:",
            view=DefineCallP1View(self.bot, self.action_id),
            ephemeral=True
        )
    
    async def define_call_p2_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Selecione o Call P2:",
            view=DefineCallP2View(self.bot, self.action_id),
            ephemeral=True
        )


class DefineCallP1View(ui.View):
    """View para definir Call P1"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        
        user_select = ui.UserSelect(placeholder="Selecione o Call P1", min_values=1, max_values=1)
        user_select.callback = self.select_callback
        self.add_item(user_select)
    
    async def select_callback(self, interaction: discord.Interaction):
        select = [item for item in self.children if isinstance(item, ui.UserSelect)][0]
        user = select.values[0]
        
        action = self.action_service.get_action(self.action_id)
        action.call_p1_id = user.id
        self.action_service.save_active_actions()
        self.action_service.save_to_history(action)
        
        channel = interaction.guild.get_channel(action.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(action.message_id)
                embed = create_action_embed(action, interaction.guild)
                view = ActionView(self.bot, self.action_id)
                await message.edit(embed=embed, view=view)
            except:
                pass
        
        await interaction.response.send_message(
            embed=create_success_embed(f"{user.mention} definido como Call P1!"),
            ephemeral=True
        )


class DefineCallP2View(ui.View):
    """View para definir Call P2"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        
        user_select = ui.UserSelect(placeholder="Selecione o Call P2", min_values=1, max_values=1)
        user_select.callback = self.select_callback
        self.add_item(user_select)
    
    async def select_callback(self, interaction: discord.Interaction):
        select = [item for item in self.children if isinstance(item, ui.UserSelect)][0]
        user = select.values[0]
        
        action = self.action_service.get_action(self.action_id)
        action.call_p2_id = user.id
        self.action_service.save_active_actions()
        self.action_service.save_to_history(action)
        
        channel = interaction.guild.get_channel(action.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(action.message_id)
                embed = create_action_embed(action, interaction.guild)
                view = ActionView(self.bot, self.action_id)
                await message.edit(embed=embed, view=view)
            except:
                pass
        
        await interaction.response.send_message(
            embed=create_success_embed(f"{user.mention} definido como Call P2!"),
            ephemeral=True
        )


class AddParticipantView(ui.View):
    """View para adicionar participante"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        
        # Adiciona UserSelect manualmente
        user_select = ui.UserSelect(
            placeholder="Selecione o usuário",
            min_values=1,
            max_values=1
        )
        user_select.callback = self.select_user_callback
        self.add_item(user_select)
    
    async def select_user_callback(self, interaction: discord.Interaction):
        # Pega o select do componente
        select = [item for item in self.children if isinstance(item, ui.UserSelect)][0]
        user = select.values[0]
        
        success = await self.action_service.add_participant(self.action_id, user.id)
        if success:
            action = self.action_service.get_action(self.action_id)
            # Atualiza mensagem original
            channel = interaction.guild.get_channel(action.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(action.message_id)
                    embed = create_action_embed(action, interaction.guild)
                    view = ActionView(self.bot, self.action_id)
                    await message.edit(embed=embed, view=view)
                except:
                    pass
            
            await interaction.response.send_message(
                embed=create_success_embed(f"{user.mention} foi adicionado à ação!"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível adicionar o usuário!"),
                ephemeral=True
            )


class RemoveParticipantView(ui.View):
    """View para remover participante"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
        
        action = self.action_service.get_action(action_id)
        if action and action.participant_ids:
            # Cria opções baseadas nos participantes
            options = []
            for user_id in action.participant_ids[:25]:  # Discord limita a 25
                options.append(discord.SelectOption(
                    label=f"Usuário {user_id}",
                    value=str(user_id)
                ))
            
            # Adiciona Select manualmente
            select = ui.Select(
                placeholder="Selecione o participante para remover",
                min_values=1,
                max_values=1,
                options=options
            )
            select.callback = self.select_callback
            self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        # Pega o select do componente
        select = [item for item in self.children if isinstance(item, ui.Select)][0]
        user_id = int(select.values[0])
        
        action = self.action_service.get_action(self.action_id)
        if action and action.escalator_id == user_id:
            await interaction.response.send_message(
                embed=create_error_embed("Não é possível remover o escalador!"),
                ephemeral=True
            )
            return
        
        success = await self.action_service.remove_participant(self.action_id, user_id)
        if success:
            # Atualiza mensagem original
            channel = interaction.guild.get_channel(action.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(action.message_id)
                    embed = create_action_embed(action, interaction.guild)
                    view = ActionView(self.bot, self.action_id)
                    await message.edit(embed=embed, view=view)
                except:
                    pass
            
            await interaction.response.send_message(
                embed=create_success_embed(f"<@{user_id}> foi removido da ação!"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível remover o participante!"),
                ephemeral=True
            )


class ConfirmCloseView(ui.View):
    """Confirmação para fechar ação"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=30)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
    
    @ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        success = await self.action_service.close_action(self.action_id, interaction.user.id)
        if success:
            action = self.action_service.get_action(self.action_id)
            # Atualiza mensagem original
            channel = interaction.guild.get_channel(action.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(action.message_id)
                    embed = create_action_embed(action, interaction.guild)
                    view = ActionView(self.bot, self.action_id)
                    await message.edit(embed=embed, view=view)
                except:
                    pass
            
            await interaction.response.send_message(
                embed=create_success_embed("Escalação fechada! Agora você pode definir o resultado."),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Não foi possível fechar a escalação!"),
                ephemeral=True
            )
        
        self.stop()
    
    @ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Operação cancelada.", ephemeral=True)
        self.stop()


class ConfirmDeleteView(ui.View):
    """Confirmação para apagar ação"""
    
    def __init__(self, bot, action_id: str):
        super().__init__(timeout=30)
        self.bot = bot
        self.action_id = action_id
        self.action_service = bot.action_service
    
    @ui.button(label="✅ Sim, Apagar", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        action = self.action_service.get_action(self.action_id)
        if not action:
            await interaction.response.send_message(
                embed=create_error_embed("Ação não encontrada!"),
                ephemeral=True
            )
            return
        
        # Tenta deletar mensagem
        channel = interaction.guild.get_channel(action.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(action.message_id)
                await message.delete()
            except:
                pass
        
        # Remove do serviço
        await self.action_service.delete_action(self.action_id)
        
        await interaction.response.send_message(
            embed=create_success_embed("🗑️ Ação apagada com sucesso!"),
            ephemeral=True
        )
        self.stop()
    
    @ui.button(label="❌ Não, Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Operação cancelada.", ephemeral=True)
        self.stop()


def setup_persistent_views(bot):
    """Registra todas as views persistentes no bot"""
    # Percorre todas as ações ativas e registra as views
    for action_id in bot.action_service.active_actions.keys():
        view = ActionView(bot, action_id)
        bot.add_view(view)
    
    print(f"✅ {len(bot.action_service.active_actions)} views persistentes registradas")