# cogs/events.py
import discord
from discord.ext import commands
from utils import create_action_embed
from cogs.action_views import ActionView


class EventsCog(commands.Cog):
    """Cog para eventos do bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.action_service = bot.action_service
        self.config_service = bot.config_service
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detecta mensagens no canal de ações e cria escalações automaticamente"""
        
        # Ignora mensagens do próprio bot
        if message.author == self.bot.user:
            return
        
        # Verifica se é no canal de ações configurado
        config = self.config_service.get_server_config(message.guild.id)
        if message.channel.id != config.get('action_channel'):
            return
        
        # Verifica se tem embeds
        if not message.embeds:
            return
        
        # Processa cada embed
        for embed in message.embeds:
            # Extrai título da descrição
            if not embed.description:
                continue
            
            # Pega primeira linha da descrição
            lines = str(embed.description).split('\n')
            if not lines:
                continue
            
            title = lines[0].strip().replace("*", "")
            
            if not title:
                continue
            
            # Ignora se for "REGISTRADORA"
            if title.upper() == "REGISTRADORA":
                continue
            
            # Cria a ação
            try:
                await self.create_action_from_message(message, title)
            except Exception as e:
                print(f"❌ Erro ao criar ação: {e}")
    
    async def create_action_from_message(self, message: discord.Message, action_name: str):
        """Cria uma ação a partir de uma mensagem"""
        config = self.config_service.get_server_config(message.guild.id)
        
        # Verifica se canal de escalação está configurado
        if not config.get('escalation_channel'):
            print(f"❌ Canal de escalação não configurado para {message.guild.name}")
            return
        
        escalation_channel = message.guild.get_channel(config['escalation_channel'])
        if not escalation_channel:
            print(f"❌ Canal de escalação não encontrado para {message.guild.name}")
            return
        
        # Obtém tipo e config da ação
        action_type = self.config_service.get_action_type_key(action_name)
        action_config = self.config_service.get_action_config(action_name)
        
        # Cria embed temporário
        embed = discord.Embed(
            title="🚨 Nova Ação Detectada",
            description=f"**{action_name}**",
            color=discord.Color.red()
        )
        embed.add_field(name="Status", value="🟢 ABERTA", inline=False)
        embed.add_field(name="Detectada de", value=message.jump_url, inline=False)
        
        # Envia mensagem com view temporária
        view = ActionView(self.bot, "temp")
        escalation_message = await escalation_channel.send(embed=embed, view=view)
        
        # Cria ação no service
        action = await self.action_service.create_action(
            guild_id=message.guild.id,
            action_name=action_name,
            action_type=action_type,
            config=action_config,
            channel_id=escalation_channel.id,
            message_id=escalation_message.id
        )
        
        # Cria view final com ID correto
        final_view = ActionView(self.bot, action.action_id)
        self.bot.add_view(final_view)
        
        # Atualiza mensagem com embed e view corretos
        final_embed = create_action_embed(action, message.guild)
        await escalation_message.edit(embed=final_embed, view=final_view)
        
        print(f"✅ Ação '{action_name}' criada automaticamente no servidor {message.guild.name}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Evento quando o bot fica pronto"""
        print(f"🤖 Bot conectado como {self.bot.user}")
        print(f"📊 Guilds: {len(self.bot.guilds)}")
        print(f"🔧 Ações ativas: {len(self.action_service.active_actions)}")


async def setup(bot):
    await bot.add_cog(EventsCog(bot))