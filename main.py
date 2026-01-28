# main.py
import discord # type: ignore
from discord.ext import commands # type: ignore
import os
import asyncio
from dotenv import load_dotenv # type: ignore

from services import ActionService, ConfigService
from cogs.action_views import setup_persistent_views

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


class PoliceBot(commands.Bot):
    """Bot customizado com serviços integrados"""
    
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        # Inicializa serviços
        self.action_service = ActionService(data_dir="data")
        self.config_service = ConfigService(data_dir="data")
    
    async def setup_hook(self):
        """Setup inicial do bot"""
        # Carrega todos os cogs
        cogs_to_load = [
            'cogs.commands',
            'cogs.reports',
            'cogs.tasks',
            'cogs.events'
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                print(f"✅ Cog carregado: {cog}")
            except Exception as e:
                print(f"❌ Erro ao carregar {cog}: {e}")
        
        # Registra views persistentes
        setup_persistent_views(self)
        
        # Sincroniza comandos slash
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos sincronizados")
        except Exception as e:
            print(f"❌ Erro ao sincronizar comandos: {e}")
    
    async def on_ready(self):
        """Chamado quando o bot está pronto"""
        print("=" * 50)
        print(f"🤖 Bot conectado como {self.user}")
        print(f"📊 ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print(f"🔧 Ações ativas: {len(self.action_service.active_actions)}")
        print("=" * 50)


def main():
    """Função principal"""
    # Obtém token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN não encontrado no arquivo .env")
        return
    
    # Cria e inicia o bot
    bot = PoliceBot()
    
    try:
        bot.run(token)
    except KeyboardInterrupt:
        print("\n🛑 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar bot: {e}")


if __name__ == "__main__":
    main()