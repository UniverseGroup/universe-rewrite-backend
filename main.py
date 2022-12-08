import os
import asyncio
from quart import Quart, render_template, jsonify, request
from quart_cors import cors, route_cors
from threading import Thread
import discord
from dotenv import load_dotenv
load_dotenv(verbose=True)
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = discord.Bot(intents=intents)
app = Quart(__name__)
Cors = cors(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
@route_cors()
async def index():
    return jsonify({"message": "Hello World!"})

@app.route('/members')
@route_cors()
async def members():
    member_id:int = request.args.get("id")
    print(member_id)
    guild = bot.get_guild(953953436133650462)
    print(guild)
    member = await guild.fetch_member(member_id)
    print(member)
    return jsonify({"member": member.name})

@app.route('/submit', methods=['POST'])
@route_cors()
async def submit():
    data = await request.get_json()
    print(data)
    user = await bot.fetch_user(int(data['id']))
    if not user.bot:
        return jsonify({"message": "User is not a bot!"})
    guild = bot.get_guild(953953436133650462)
    channel = await guild.fetch_channel(1011145869971693640)
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={data['id']}&permissions=0&scope=bot&guild_id=953953436133650462&disable_guild_select=true&prompt=none" if not data.get("url") else data['url']
    embed = discord.Embed(title="새로운 봇 등록됨",colour=discord.Colour.green())
    embed.add_field(name="봇 라이브러리",value=data['library'],inline=False)
    embed.add_field(name="봇 카테고리",value=",".join(data['category']),inline=False)
    embed.add_field(name="봇 접두사",value=data['prefix'],inline=False)
    embed.set_author(name=user.name,icon_url=user.display_avatar, url=invite_url)
    embed.set_thumbnail(url=user.display_avatar)
    await channel.send(embed=embed)
    return jsonify({"code":200,"msg": "success"})

@bot.event
async def on_ready():
    print("bot ready")

@bot.slash_command(guild_ids=[953953436133650462])
async def approve(ctx: discord.ApplicationContext, user_id):
    # Setting a default value for the member parameter makes it optional ^
    guild = bot.get_guild(953953436133650462)
    review_role = guild.get_role(955829397741502514)
    if review_role not in ctx.author.roles:
        return await ctx.respond("You do not have permission to use this command.", ephemeral=True)
    #member = await guild.fetch_member((user_id))
    bot_user = await bot.fetch_user(int(user_id))
    await ctx.respond(f"{bot_user.mention}(`{bot_user.name}#{bot_user.discriminator}` | `{bot_user.id}`) has been approved!")

@bot.slash_command(guild_ids=[953953436133650462])
async def deny(ctx: discord.ApplicationContext, user_id,reason):
    # Setting a default value for the member parameter makes it optional ^
    guild = bot.get_guild(953953436133650462)
    review_role = guild.get_role(955829397741502514)
    if review_role not in ctx.author.roles:
        return await ctx.respond("You do not have permission to use this command.", ephemeral=True)
    #member = await guild.fetch_member((user_id))
    bot_user = await bot.fetch_user(int(user_id))
    await ctx.respond(f"{bot_user.mention}(`{bot_user.name}#{bot_user.discriminator}` | `{bot_user.id}`) has been denied for `{reason}`!")
def run_api():
    app.run(port=5000,use_reloader=False)

if __name__ == '__main__':
    bot.loop.create_task(app.run_task())
    bot.run(os.getenv("botTOKEN"))