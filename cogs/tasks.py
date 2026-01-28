# cogs/tasks.py
import discord # type: ignore
from discord.ext import commands, tasks # type: ignore
from datetime import datetime, time
import pytz # type: ignore
from utils import create_action_embed, create_warning_embed
from cogs.action_views import ActionView


class TasksCog(commands.Cog):
    """Cog com tarefas automáticas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.action_service = bot.action_service
        self.config_service = bot.config_service
        
        # Inicia tasks
        self.check_inactivity.start()
        self.daily_reports.start()
        self.weekly_reports.start()
    
    def cog_unload(self):
        """Para tasks quando o cog é descarregado"""
        self.check_inactivity.cancel()
        self.daily_reports.cancel()
        self.weekly_reports.cancel()
    
    @tasks.loop(minutes=30)  # Verifica a cada 30 minutos
    async def check_inactivity(self):
        """Verifica ações inativas e envia avisos/fecha automaticamente"""
        print("🔍 Verificando inatividade de ações...")
        
        for guild in self.bot.guilds:
            config = self.config_service.get_server_config(guild.id)
            warning_hours = config.get('warning_hours', 20)
            inactivity_hours = config.get('inactivity_hours', 24)
            
            # Verifica ações que precisam de aviso
            actions_to_warn = self.action_service.get_actions_needing_inactivity_check(warning_hours)
            for action in actions_to_warn:
                if action.guild_id != guild.id:
                    continue
                
                # Envia aviso ao escalador se houver
                if action.escalator_id:
                    try:
                        escalator = guild.get_member(action.escalator_id)
                        if escalator:
                            embed = create_warning_embed(
                                f"A ação **{action.action_name}** está aberta há {warning_hours}h sem resultado!\n\n"
                                f"Se não houver atividade em breve, ela será marcada como **INATIVA**.",
                                "⏰ Aviso de Inatividade"
                            )
                            await escalator.send(embed=embed)
                            print(f"⚠️ Aviso enviado ao escalador da ação {action.action_id}")
                    except Exception as e:
                        print(f"Erro ao enviar aviso: {e}")
                
                # Marca que o aviso foi enviado
                await self.action_service.mark_inactivity_warning(action.action_id)
            
            # Verifica ações que devem ser fechadas por inatividade
            actions_to_close = self.action_service.get_actions_needing_inactivity_close(inactivity_hours)
            for action in actions_to_close:
                if action.guild_id != guild.id:
                    continue
                
                # Marca como inativa
                await self.action_service.set_inactivity(action.action_id)
                
                # Atualiza mensagem
                channel = guild.get_channel(action.channel_id)
                if channel:
                    try:
                        message = await channel.fetch_message(action.message_id)
                        embed = create_action_embed(action, guild)
                        await message.edit(embed=embed, view=None)  # Remove botões
                        print(f"⏰ Ação {action.action_id} marcada como INATIVA")
                    except Exception as e:
                        print(f"Erro ao atualizar mensagem de inatividade: {e}")
                
                # Notifica o escalador
                if action.escalator_id:
                    try:
                        escalator = guild.get_member(action.escalator_id)
                        if escalator:
                            embed = discord.Embed(
                                title="⏰ Ação Marcada como Inativa",
                                description=f"A ação **{action.action_name}** foi automaticamente marcada como **INATIVA** "
                                           f"após {inactivity_hours}h sem resultado.",
                                color=discord.Color.dark_purple()
                            )
                            await escalator.send(embed=embed)
                    except Exception as e:
                        print(f"Erro ao notificar inatividade: {e}")
    
    @check_inactivity.before_loop
    async def before_inactivity_check(self):
        """Aguarda o bot estar pronto antes de iniciar a task"""
        await self.bot.wait_until_ready()
    
    @tasks.loop(time=time(hour=23, minute=59, tzinfo=pytz.timezone('America/Sao_Paulo')))
    async def daily_reports(self):
        """Envia relatórios diários automaticamente"""
        print("📊 Gerando relatórios diários...")
        
        from cogs.reports import ReportsCog
        reports_cog = self.bot.get_cog('ReportsCog')
        if not reports_cog:
            print("❌ ReportsCog não encontrado!")
            return
        
        for guild in self.bot.guilds:
            config = self.config_service.get_server_config(guild.id)
            report_channel_id = config.get('report_channel')
            
            if not report_channel_id:
                continue
            
            channel = guild.get_channel(report_channel_id)
            if not channel:
                continue
            
            try:
                embed = await reports_cog.generate_daily_report(guild.id)
                await channel.send(embed=embed)
                print(f"✅ Relatório diário enviado para {guild.name}")
            except Exception as e:
                print(f"❌ Erro ao enviar relatório diário para {guild.name}: {e}")
    
    @daily_reports.before_loop
    async def before_daily_reports(self):
        """Aguarda o bot estar pronto antes de iniciar a task"""
        await self.bot.wait_until_ready()
    
    @tasks.loop(time=time(hour=23, minute=59, tzinfo=pytz.timezone('America/Sao_Paulo')))
    async def weekly_reports(self):
        """Envia relatórios semanais automaticamente todo domingo"""
        if datetime.now().weekday() != 6:  # Não é domingo
            return
        
        print("📊 Gerando relatórios semanais...")
        
        from cogs.reports import ReportsCog
        reports_cog = self.bot.get_cog('ReportsCog')
        if not reports_cog:
            print("❌ ReportsCog não encontrado!")
            return
        
        for guild in self.bot.guilds:
            config = self.config_service.get_server_config(guild.id)
            report_channel_id = config.get('report_channel')
            
            if not report_channel_id:
                continue
            
            channel = guild.get_channel(report_channel_id)
            if not channel:
                continue
            
            try:
                embed = await reports_cog.generate_weekly_report(guild.id)
                await channel.send(embed=embed)
                print(f"✅ Relatório semanal enviado para {guild.name}")
            except Exception as e:
                print(f"❌ Erro ao enviar relatório semanal para {guild.name}: {e}")
    
    @weekly_reports.before_loop
    async def before_weekly_reports(self):
        """Aguarda o bot estar pronto antes de iniciar a task"""
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(TasksCog(bot))