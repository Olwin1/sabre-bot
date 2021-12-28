import discord
import discord.utils
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from discord.ext import commands
from discord_slash import cog_ext

guild_ids = [704255331680911402]

class bcolours:
    HEADER = '\033[95m'
    OKBLUE = '\033[34m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[0;31m'
    ENDC = '\033[0m'
print(f"{bcolours.OKBLUE}URL Generation Is Now Active.")

class urlgen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @cog_ext.cog_slash(name="genurl", guild_ids=guild_ids)
    async def _genurl(self, ctx, *, message):
        player = ctx.author
        if player.bot:
            return

        substr = "http://"
        substr2 = "https://"
        if substr in message or substr2 in message:

            with open("./keys/public_key.pem", "rb") as key_file:

                public_key = serialization.load_pem_public_key(
                    key_file.read(),#.decode("UTF-8"),
                    backend = default_backend()
                )
            encrypted = public_key.encrypt(
                message.encode("ascii"),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                   algorithm=hashes.SHA256(),
                   label=None
                )
            )
            encrypted_str = encrypted.hex()
            await ctx.send(f"https://sabreguild.com/aaa?data={encrypted_str}")





def setup(bot):
    bot.add_cog(urlgen(bot))
