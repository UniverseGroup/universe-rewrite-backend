import os
import asyncio
from quart import Quart, render_template, jsonify, request
from quart_cors import cors, route_cors
from threading import Thread
import discord
from discord.ext import tasks
from dotenv import load_dotenv
import json
import motor.motor_asyncio
load_dotenv(verbose=True)
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = discord.Bot(intents=intents)
app = Quart(__name__)
Cors = cors(app)
app.config['CORS_HEADERS'] = 'Content-Type'
dbclient = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("mongoDB"))
db = dbclient['universe']


def generate_invite_link(bot_id):
    return discord.utils.oauth_url(
        client_id=bot_id,
        permissions=discord.Permissions(0),
        guild=bot.get_guild(1051361439098617927),
        disable_guild_select=True,
    )


@app.route('/')
@route_cors()
async def index():
    return jsonify({"message": "Hello World!"})

@app.route('/members')
@route_cors()
async def members():
    member_id:int = request.args.get("id")
    if member_id is None:
        users_list = request.args.get("users")
        print(users_list)
        user_data = []
        for user in users_list.split(","):
            fetch_user = await bot.fetch_user(int(user))
            user_data.append({"name": fetch_user.name,'discriminator':fetch_user.discriminator, "id": fetch_user.id, "avatar": fetch_user.display_avatar.url,})
        return json.dumps(user_data,ensure_ascii=False)

    try:
        guild = bot.get_guild(953953436133650462)
        member = await guild.fetch_member(member_id)
        return json.dumps({"name": member.name, "id": member.id, "avatar": member.display_avatar.url, 
        "bot": member.bot, "discriminator": member.discriminator, "roles": [role.name for role in member.roles], 
        "joined_at": member.joined_at.strftime("%Y-%m-%d %H:%M:%S"),"member":True,
        "verified":member.public_flags.verified_bot if member.bot else False,
        "status":member.status},ensure_ascii=False)
    except:
        user = await bot.fetch_user(member_id)
        return json.dumps({"name": user.name, "id": member_id, "avatar": user.display_avatar.url,
        "bot": user.bot, "discriminator": user.discriminator,"created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),"member":False,
        "verified":user.public_flags.verified_bot if user.bot else False,"status":"online"},
        ensure_ascii=False)

@app.route('/submit', methods=['POST'])
@route_cors()
async def submit():
    data = await request.get_json()
    print(data)
    user = await bot.fetch_user(int(data['id']))
    if not user.bot:
        return jsonify({"message": "User is not a bot!"})
    guild = bot.get_guild(1051361439098617927)
    channel = await guild.fetch_channel(1051361877214638191)
    review_role = guild.get_role(1051362690339196938)
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={data['id']}&permissions=0&scope=bot&guild_id=1051361439098617927&disable_guild_select=true"
    embed = discord.Embed(title="????????? ??? ?????????",colour=discord.Colour.green())
    embed.add_field(name="??? ???????????????",value=data['library'],inline=False)
    embed.add_field(name="??? ????????????",value=", ".join(data['category']),inline=False)
    embed.add_field(name="??? ?????????",value=data['prefix'],inline=False)
    embed.set_author(name=user.name,icon_url=user.display_avatar, url=invite_url)
    embed.set_thumbnail(url=user.display_avatar)
    await channel.send(content=review_role.mention,embed=embed)
    return jsonify({"code":200,"msg": "success"})

@app.route('/report', methods=['POST'])
@route_cors()
async def report():
    data = await request.get_json()
    print(data)
    botuser = await bot.fetch_user(int(data['botid']))
    reportuser = await bot.fetch_user(int(data['userid']))
    if not botuser.bot:
        return jsonify({"message": "User is not a bot!"})
    guild = bot.get_guild(1051361439098617927)
    channel = await guild.fetch_channel(1052248091778109441)
    review_role = guild.get_role(1051362690339196938)
    embed = discord.Embed(title="????????? ???",colour=discord.Colour.red())
    embed.add_field(name="???",value=f"{botuser.display_name}({botuser.id})",inline=False)
    embed.add_field(name="?????????",value=f"{reportuser.display_name}({reportuser.id})",inline=False)
    embed.add_field(name="?????? ????????????",value=data['category'],inline=False)
    embed.add_field(name="?????? ??????",value=data['description'],inline=False)
    embed.set_thumbnail(url=botuser.display_avatar)
    await channel.send(content=review_role.mention,embed=embed)
    return jsonify({"code":200,"msg": "success"})





@bot.event
async def on_ready():
    print("bot ready")


@tasks.loop(seconds=60)
async def update_status():
    print("updating status...")
    db_bots = await db['bots'].find({'approved':True}).to_list(length=None)
    for bots in db_bots:
        guild = bot.get_guild(953953436133650462)
        member = await guild.fetch_member(int(bots['botid']))
        botuser = await bot.fetch_user(int(bots['botid']))
        if member.status == discord.Status.online:
            await db['bots'].update_one({'botid':bots['botid']},{'$set':{'status':'online','name':botuser.name,'discordVerified':botuser.public_flags.verified_bot}})
        elif member.status == discord.Status.idle:
            await db['bots'].update_one({'botid':bots['botid']},{'$set':{'status':'idle','name':botuser.name,'discordVerified':botuser.public_flags.verified_bot}})
        elif member.status == discord.Status.dnd:
            await db['bots'].update_one({'botid':bots['botid']},{'$set':{'status':'dnd','name':botuser.name,'discordVerified':botuser.public_flags.verified_bot}})
        elif member.status == discord.Status.offline:
            await db['bots'].update_one({'botid':bots['botid']},{'$set':{'status':'offline','name':botuser.name,'discordVerified':botuser.public_flags.verified_bot}})
        else:
            await db['bots'].update_one({'botid':bots['botid']},{'$set':{'status':'offline','name':botuser.name,'discordVerified':botuser.public_flags.verified_bot}})
    print("updated status")
update_status.start()
@update_status.before_loop
async def before_update_status():
    await bot.wait_until_ready()

@bot.slash_command(guild_ids=[1051361439098617927])
async def todos(ctx: discord.ApplicationContext):
    counts = await db['pendbots'].count_documents({'pending': True})
    await ctx.respond(f"?????? {counts}?????? ?????? ?????? ??????????????????.")

@bot.slash_command(guild_ids=[1051361439098617927])
async def pendings(ctx: discord.ApplicationContext):
    pendbots = await db['pendbots'].find({'pending': True}).to_list(length=10)
    embed = discord.Embed(title="?????? ???????????? ??????",colour=discord.Colour.green())
    for pendbot in pendbots:
        user = await bot.fetch_user(int(pendbot['botid']))
        embed.add_field(name=f"{user.name}#{user.discriminator}",value=f"ID: {user.id}\nINVITE: {generate_invite_link(user.id)}",inline=False)
    await ctx.respond(embed=embed)

@bot.slash_command(guild_ids=[1051361439098617927])
async def approve(ctx: discord.ApplicationContext, pendbot:discord.Member):
    #member = await guild.fetch_member((user_id))
    if not pendbot.bot:
        return await ctx.respond("User is not a bot!", ephemeral=True)
    pendDB = await db['pendbots'].find_one({'botid': str(pendbot.id)})
    guild = bot.get_guild(953953436133650462)
    try:
        guild.get_member(int(pendDB['userid']))
    except discord.errors.NotFound:
        denyEmbed = discord.Embed(title="?????? ??????",description=f"?????? ??????! (`{pendbot.name}#{pendbot.discriminator}` | `{pendbot.id}`)\n??????: `?????? ???????????? ????????? ???????????????????????????.`",colour=discord.Colour.red())
        await bot.get_channel(1051365552813264967).send(embed=denyEmbed)
        await pendbot.kick(reason="???????????? ????????? ??????????????????")
        await db['pendbots'].update_one({'botid': str(pendbot.id)}, {'$set': {'pending': False, 'deny': True,'denyReason': "???????????? ????????? ??????????????????"}})
        return await ctx.respond(f"{pendbot.mention}(`{pendbot.name}#{pendbot.discriminator}` | `{pendbot.id}`)??? ????????? ?????????????????????.\n????????????: `???????????? ????????? ??????????????????`", ephemeral=True)
    await db['pendbots'].update_one({'botid': str(pendbot.id),'pending':True,'deny':False,'approved':False}, {'$set': {'pending': False, 'approved': True}})
    await db['bots'].update_one({'botid': str(pendbot.id)}, {'$set': {'approved': True}})
    bot_user = await bot.fetch_user(int(pendbot.id))
    approveEmbed = discord.Embed(title="??????",description=f"??????! (`{pendbot.name}#{pendbot.discriminator}` | `{pendbot.id}`)",colour=discord.Colour.green())
    await guild.get_member(int(pendDB['userid'])).add_roles(guild.get_role(954184048358596648))
    await bot.get_channel(1051365552813264967).send(embed=approveEmbed)
    await guild.get_member(int(pendDB['userid'])).send(f"???????????? ??? `{pendbot.name}`??? ?????????????????????!")
    await ctx.respond(f"{bot_user.mention}(`{bot_user.name}#{bot_user.discriminator}` | `{bot_user.id}`) has been approved!")
    await pendbot.kick()

@bot.slash_command(guild_ids=[1051361439098617927])
async def deny(ctx: discord.ApplicationContext, pendbot:discord.Member,reason):
    #member = await guild.fetch_member((user_id))
    bot_user = await bot.fetch_user(pendbot.id)
    if not pendbot.bot:
        return await ctx.respond("User is not a bot!", ephemeral=True)
    pendDB = await db['pendbots'].find_one({'botid': str(pendbot.id)})
    guild = bot.get_guild(953953436133650462)
    try:
        guild.get_member(int(pendDB['userid']))
    except discord.errors.NotFound:
        denyEmbed = discord.Embed(title="?????? ??????",description=f"?????? ??????! (`{pendbot.name}#{pendbot.discriminator}` | `{pendbot.id}`)\n??????: `?????? ???????????? ????????? ???????????????????????????.`",colour=discord.Colour.red())
        await bot.get_channel(1051365552813264967).send(embed=denyEmbed)
        await pendbot.kick(reason="???????????? ????????? ??????????????????")
        await db['pendbots'].update_one({'botid': str(pendbot.id)}, {'$set': {'pending': False, 'deny': True,'denyReason': "???????????? ????????? ??????????????????"}})
        return await ctx.respond(f"{pendbot.mention}(`{pendbot.name}#{pendbot.discriminator}` | `{pendbot.id}`)??? ????????? ?????????????????????.\n????????????: `???????????? ????????? ??????????????????`", ephemeral=True)
    await db['pendbots'].update_one({'botid': str(pendbot.id),'pending':True,'deny':False,'approved':False}, {'$set': {'pending': False, 'deny': True,'denyReason': reason}})
    await db['bots'].delete_one({'botid': str(pendbot.id)})
    bot_user = await bot.fetch_user(int(pendbot.id))
    denyEmbed = discord.Embed(title="?????? ??????",description=f"?????? ??????! (`{pendbot.name}#{pendbot.discriminator}` | `{pendbot.id}`)\n??????: `{reason}`",colour=discord.Colour.red())
    await bot.get_channel(1051365552813264967).send(embed=denyEmbed)
    await guild.get_member(int(pendDB['userid'])).send(f"???????????? ??? `{pendbot.name}`??? ????????? ?????? ????????? ?????????????????????.\n??????: `{reason}`")
    await ctx.respond(f"{bot_user.mention}(`{bot_user.name}#{bot_user.discriminator}` | `{bot_user.id}`) has been denied for `{reason}`!")
    await pendbot.kick(reason=reason)

def run_api():
    app.run(port=5000,use_reloader=False)

if __name__ == '__main__':
    bot.loop.create_task(app.run_task())
    bot.run(os.getenv("botTOKEN"))