import psycopg
import redis

import json
conn = psycopg.connect(dbname="sabre", user="postgres", password="***REMOVED***", host="localhost")
r = redis.Redis(host='161.97.86.11', port=6379, db=0, password="Q29ubmll")
def get_guild(guild_id):
    value = r.get(guild_id)
    if value is None:
        cur = conn.cursor()
        cur.execute("""SELECT role_rewards, toggle_moderation,  toggle_automod, toggle_welcomer, toggle_autoresponder, toggle_leveling, toggle_autorole, toggle_reactionroles, toggle_music, toggle_modlog, 
            automod_links, automod_invites, automod_mention, automod_swears, 
            welcome_join_channel, welcome_join_message, welcome_join_role, welcome_join_message_p, welcome_leave_message, welcome_leave_channel, 
            modlog_channel, modlog_bans, modlog_warns, modlog_mutes, modlog_purge, modlog_lock, modlog_kick, FROM guilds WHERE id=%s""", (guild_id,))
        selected = cur.fetchone()
        if selected is None:# If Guild Is Not Found... Create It
            cur.execute("INSERT INTO guilds (id) VALUES (%s)", (guild_id,))
            conn.commit()
            cur.execute("""SELECT role_rewards, toggle_moderation,  toggle_automod, toggle_welcomer, toggle_autoresponder, toggle_leveling, toggle_autorole, toggle_reactionroles, toggle_music, toggle_modlog, 
            automod_links, automod_invites, automod_mention, automod_swears, 
            welcome_join_channel, welcome_join_message, welcome_join_role, welcome_join_message_p, welcome_leave_message, welcome_leave_channel, 
            modlog_channel, modlog_bans, modlog_warns, modlog_mutes, modlog_purge, modlog_lock, modlog_kick, FROM guilds WHERE id=%s""", (guild_id,))
            selected = cur.fetchone()
            
            
            
        guild = {
            "guild_id": guild_id, 
            "role_rewards": selected[0],
            "toggle": {
                "moderation": selected[1], 
                "automod": selected[2], 
                "welcomer": selected[3], 
                "autoresponder": selected[4], 
                "leveling": selected[5], 
                "autorole": selected[6], 
                "reactionroles": selected[7], 
                "music": selected[8], 
                "modlog": selected[9]
                },
            "automod": {
                "links": selected[10],
                "invites": selected[11],
                "mention": selected[12],
                "swears": selected[13]
                },
            "welcome": {
                "join": {
                    "channel": selected[14],
                    "message": selected[15],
                    "role": selected[16],
                    "private": selected[17]
                },
                "leave": {
                    "message": selected[18],
                    "channel": selected[19]
                }
                },
            "modlog": {
                "channel": selected[20],
                "bans": selected[21],
                "warns": selected[22],
                "mutes": selected[23],
                "purge": selected[24],
                "lock": selected[25],
                "kick": selected[26],
            },
            "members": []
            }
    
        
        cur.execute("SELECT user_id, exp, infraction_description, infraction_date FROM members WHERE guild_id=%s", (guild_id,))
        selected_members = cur.fetchall()
        for member in selected_members:
            guild["members"].append({"user_id": member[0], "guild_id": guild_id, "exp": member[1], "infraction_description": member[2], "infraction_date": member[3]})
            
        r.set(guild["guild_id"], guild)
            
        return guild


def get_user(arg):
    value = r.get(arg)
    if value is None:
        cur = conn.cursor()
        cur.execute("SELECT id, birthday FROM users WHERE id = %s", (arg,))
        selected = cur.fetchone()
        if selected is None:
            cur.execute("INSERT INTO users (id) VALUES (%s)", (arg,))
            conn.commit()
            cur.execute("SELECT id, birthday FROM users WHERE id = %s", (arg,))
            selected = cur.fetchone()
            
    user = {"id": selected[0], "bday": selected[1]}
    
    r.set(user["id"], user)
            
    return user

def create_member(guild, user_id):
    cur = conn.cursor()
    cur.execute("INSERT INTO members (user_id, guild_id, exp) VALUES (%s, %s, %s)", (user_id, guild["id"], 1))# Create Member.
    conn.commit()
    cur.execute("SELECT user_id, exp, infraction_description, infraction_date FROM members WHERE user_id = %s AND guild_id=%s", (user_id, guild["id"]))
    member = cur.fetchone()
    guild["members"].append({"user_id": member[0], "guild_id": guild["id"], "exp": member[1], "infraction_description": member[2], "infraction_date": member[3]})
    r.set(guild["id"], json.dumps(guild))
    return guild
    
    
    
def find_member(guild, member_id):
    for i, member in enumerate(guild["members"]):
        if member["id"] == member_id:
            return guild, i
    create_member(guild["id"], member_id)
    find_member(guild, i)
    
    

def update_guild(guild):
    r.set(guild["id"], json.dumps(guild))
    

def update_user(user):
    r.set(user["id"], json.dumps(user))




#role_rewards, toggle_moderation,  toggle_automod, toggle_welcomer, toggle_autoresponder, 
# toggle_leveling, toggle_autorole, toggle_reactionroles, toggle_music, 
# toggle_modlog, automod_links, automod_invites, automod_mention, automod_swears, 
# welcome_join_channel, welcome_join_message, 
# welcome_join_role, welcome_join_message_p, welcome_leave_message, welcome_leave_channel