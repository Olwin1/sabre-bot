import psycopg
import redis

import json
conn = psycopg.connect(dbname="sabre", user="postgres", password="***REMOVED***", host="localhost")
r = redis.Redis(host='161.97.86.11', port=6379, db=0, password="***REMOVED***")
def get_guild(guild_id):
    value = r.get(guild_id)
    if value is None:
        cur = conn.cursor()
        cur.execute("""SELECT role_rewards, toggle_moderation,  toggle_automod, toggle_welcomer, toggle_autoresponder, toggle_leveling, toggle_autorole, toggle_reactionroles, toggle_music, toggle_modlog, 
            automod_links, automod_invites, automod_mention, automod_swears, 
            welcome_join_channel, welcome_join_message, welcome_join_role, welcome_join_message_p, welcome_leave_message, welcome_leave_channel, 
            modlog_channel, modlog_bans, modlog_warns, modlog_mutes, modlog_purge, modlog_lock, modlog_kick FROM guilds WHERE id=%s""", (guild_id,))
        selected = cur.fetchone()
        if selected is None:# If Guild Is Not Found... Create It
            cur.execute("INSERT INTO guilds (id) VALUES (%s)", (guild_id,))
            conn.commit()
            cur.execute("""SELECT role_rewards, toggle_moderation,  toggle_automod, toggle_welcomer, toggle_autoresponder, toggle_leveling, toggle_autorole, toggle_reactionroles, toggle_music, toggle_modlog, 
            automod_links, automod_invites, automod_mention, automod_swears, 
            welcome_join_channel, welcome_join_message, welcome_join_role, welcome_join_message_p, welcome_leave_message, welcome_leave_channel, 
            modlog_channel, modlog_bans, modlog_warns, modlog_mutes, modlog_purge, modlog_lock, modlog_kick FROM guilds WHERE id=%s""", (guild_id,))
            selected = cur.fetchone()
    
            
            
            
        guild = {
            "id": guild_id, 
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
            guild["members"].append({"u_id": member[0], "g_id": guild_id, "exp": member[1], "infraction_description": member[2], "infraction_date": member[3]})
            
        r.set(guild["id"], json.dumps(guild))
            
        return guild
    return json.loads(value)


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
    
        r.set(user["id"], json.dumps(user))
    else:
        user = json.loads(value)
            
    return user

def create_member(guild, user_id):
    cur = conn.cursor()
    cur.execute("SELECT EXISTS(SELECT id FROM users WHERE id = %s)", (user_id,))
    if not cur.fetchone()[0]:
        cur.execute("INSERT INTO users (id) VALUES (%s)", (user_id,))
    cur.execute("INSERT INTO members (user_id, guild_id, exp) VALUES (%s, %s, %s)", (user_id, guild["id"], 1))# Create Member.
    conn.commit()
    cur.execute("SELECT user_id, exp, infraction_description, infraction_date FROM members WHERE user_id = %s AND guild_id=%s", (user_id, guild["id"]))
    member = cur.fetchone()
    guild["members"].append({"user_id": member[0], "g_id": guild["id"], "exp": member[1], "infraction_description": member[2], "infraction_date": member[3]})
    r.set(guild["id"], json.dumps(guild))
    return guild
    
    
    
def find_member(guild, member_id):
    for i, member in enumerate(guild["members"]):
        if member["u_id"] == member_id:
            return guild, i
    create_member(guild["id"], member_id)
    find_member(guild, i)
    
    

def update_guild(guild):
    r.set(guild["id"], json.dumps(guild))
    

def update_user(user):
    r.set(user["id"], json.dumps(user))

def make_space():
    keys = []
    for key in r.scan_iter("*"):
        #size = r.execute_command("MEMORY USAGE", key)
        idle = r.object("idletime", key)
        keys.append({"k": key, "i": idle})
        # idle time is in seconds. This is 90days
        #if idle > 7776000:
        #    r.delete(key)
    sorted_list = sorted(keys, key=lambda y: y["i"], reverse=True)
    x = True
    iter = 0
    while x:
        if r.info()['used_memory'] < 2097152000:
        #if length < r.execute_command("MEMORY USAGE", keys[iter]["k"]):
            x = False
        # SAVE CACHE TO SLOWSTORE
        g = get_guild(keys[iter]["k"])
        cur = conn.cursor()
        if "members" in g:

            cur.execute("""UPDATE guilds
                SET role_rewards=%s, toggle_moderation=%s,  toggle_automod=%s, toggle_welcomer=%s, toggle_autoresponder=%s, toggle_leveling=%s, toggle_autorole=%s, toggle_reactionroles=%s, toggle_music=%s, toggle_modlog=%s, 
                automod_links=%s, automod_invites=%s, automod_mention=%s, automod_swears=%s, 
                welcome_join_channel=%s, welcome_join_message=%s, welcome_join_role=%s, welcome_join_message_p=%s, welcome_leave_message=%s, welcome_leave_channel=%s, 
                modlog_channel=%s, modlog_bans=%s, modlog_warns=%s, modlog_mutes=%s, modlog_purge=%s, modlog_lock=%s, modlog_kick=%s
                WHERE id=%s""", (g["role_rewards"], g["toggle"]["moderation"], g["toggle"]["automod"], g["toggle"]["welcomer"], g["toggle"]["autoresponder"], g["toggle"]["leveling"],
                                g["toggle"]["autorole"], g["toggle"]["reactionroles"], g["toggle"]["music"], g["toggle"]["modlog"],
                                g["automod"]["links"], g["automod"]["invites"], g["automod"]["mention"], g["automod"]["swears"],
                                g["welcome"]["join"]["channel"], g["welcome"]["join"]["message"], g["welcome"]["join"]["role"], g["welcome"]["join"]["private"], g["welcome"]["leave"]["message"], g["welcome"]["leave"]["channel"],
                                g["modlog"]["channel"], g["modlog"]["bans"], g["modlog"]["warns"], g["modlog"]["mutes"], g["modlog"]["purge"], g["modlog"]["lock"], g["modlog"]["kick"],
                                g["id"]
                                ))
            
            for member in g["members"]:
                cur.execute("UPDATE members SET exp=%s, infraction_description=%s, infraction_date=%s WHERE user_id = %s AND guild_id=%s", (member["exp"], member["infraction_description"], member["infraction_date"], member["user_id"], member["g_id"]))
            
        else:
            cur.execute("UPDATE users SET birthday=%s WHERE id = %s", (g["bday"],g["id"]))
            
        conn.commit()
        
        #REMOVE CACHE
        r.delete
        
        
        #Increment Iter By 1
        iter += 1


def __len__(self):
    return r.dbsize()

#role_rewards, toggle_moderation,  toggle_automod, toggle_welcomer, toggle_autoresponder, 
# toggle_leveling, toggle_autorole, toggle_reactionroles, toggle_music, 
# toggle_modlog, automod_links, automod_invites, automod_mention, automod_swears, 
# welcome_join_channel, welcome_join_message, 
# welcome_join_role, welcome_join_message_p, welcome_leave_message, welcome_leave_channel