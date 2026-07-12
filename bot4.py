"""
==============================================
bot4.py - Mini Games System v1.0
==============================================
Games: Rock Paper Scissors | Tic Tac Toe | Animal Hunt
Modes: vs AI | vs Real Players (with Fake Rooms)
==============================================
"""

import random
import time
import threading
from datetime import datetime, timedelta
from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, CHANNEL_ID
from database import (bot_config, save_json, DB_CONFIG, get_user,
                      update_user_data, update_user_rank_and_quests)

# =====================================================
# INITIALIZATION
# =====================================================

def init_games_config():
    defaults = {
        "games_last_played": {},
        "games_stats": {},
        "active_rooms": {},
        "player_queues": {"rps": [], "ttt": [], "hunt": []},
        "games_banned_users": {},
        "games_history": []
    }
    changed = False
    for k, v in defaults.items():
        if k not in bot_config:
            bot_config[k] = v
            changed = True
    if changed:
        save_json(DB_CONFIG, bot_config)

init_games_config()

# Temp storage
active_games = {}  # {game_id: game_data}
user_current_game = {}  # {uid: game_id}
temp_bet_setup = {}  # {uid: {game: "rps", bet: 0}}

# =====================================================
# GAMES TRANSLATIONS
# =====================================================

GAMES_LANG = {
    "ar": {
        "games_title": "🎮 <b>━━ مركز الألعاب ━━</b>\n\n🎯 <i>العب واربح النقاط!</i>",
        "games_desc": "✨ 3 ألعاب مثيرة بانتظارك",
        "btn_rps": "✂️ حجرة ورقة مقص",
        "btn_ttt": "⭕ X و O",
        "btn_hunt": "🐾 صيد الحيوانات",
        "btn_stats": "📊 إحصائياتي",
        "btn_leaderboard": "🏆 المتصدرون",
        "btn_back": "🔙 رجوع",
        "choose_mode": "🎯 <b>اختر طريقة اللعب:</b>",
        "mode_ai": "🤖 اللعب ضد الذكاء الاصطناعي",
        "mode_pvp": "👥 اللعب ضد لاعب حقيقي",
        "choose_bet": "💎 <b>اختر قيمة اللعب:</b>",
        "bet_placeholder": "💫 قيمة أعلى = ربح أكبر!",
        "already_played": "⏰ <b>لقد لعبت اليوم!</b>\n\n🔄 عد بعد: <b>{hours}س {mins}د</b>\n\n💡 <i>محاولة واحدة يومياً لكل لعبة</i>",
        "insufficient": "❌ رصيدك غير كافٍ!",
        "searching_player": "🔍 <b>جاري البحث عن لاعب...</b>\n\n⏳ الوقت المتبقي: {time}s\n\n💡 <i>سيتم توصيلك بأول لاعب متاح</i>",
        "no_players": "😔 <b>لا يوجد لاعبين متاحين</b>\n\n🤖 <i>هل تريد اللعب ضد الذكاء الاصطناعي؟</i>",
        "game_starting": "🎊 <b>وجدنا خصم!</b>\n\n⚡ اللعبة تبدأ الآن...",
        "your_turn": "🎯 <b>دورك!</b>\n\n⏰ لديك 20 ثانية",
        "opponent_turn": "⏳ <b>دور الخصم...</b>",
        "you_won": "🎊 <b>مبروك! فزت!</b>\n\n💎 ربحت: <b>+{amount}</b>",
        "you_lost": "😔 <b>خسرت هذه الجولة</b>\n\n💔 حظاً أوفر المرة القادمة!",
        "draw": "🤝 <b>تعادل!</b>\n\n💰 استرجعت رهانك",
        "rps_choose": "✂️ <b>اختر:</b>",
        "rock": "🪨 حجرة",
        "paper": "📄 ورقة",
        "scissors": "✂️ مقص",
        "ttt_desc": "⭕ <b>X و O</b>\n\nاجمع 3 على التوالي لتفوز!",
        "hunt_desc": "🐾 <b>صيد الحيوانات</b>\n\nستظهر إيموجيات لثانيتين، اضغط بسرعة!",
        "hunt_ready": "⚡ <b>استعد!</b>\n\n🎯 <i>الحيوانات ستظهر خلال 3 ثواني...</i>",
        "hunt_go": "🎯 <b>اضغط بسرعة!</b>",
        "cheat_detected": "🚫 <b>تم رصد محاولة تلاعب!</b>\n\n⛔ تم حظرك مؤقتاً لمدة ساعة\n\n💡 <i>ممنوع اللعب من حسابين للربح</i>",
        "same_ip_warn": "⚠️ <b>تنبيه أمني</b>\n\n🔒 لا يمكنك اللعب ضد نفسك!",
        "stats_title": "📊 <b>━━ إحصائياتي ━━</b>\n\n🎮 المباريات: <b>{total}</b>\n🏆 الانتصارات: <b>{wins}</b>\n💔 الخسائر: <b>{losses}</b>\n🤝 التعادلات: <b>{draws}</b>\n💎 أرباحك: <b>{earnings}</b>\n📈 نسبة الفوز: <b>{winrate}%</b>",
        "leaderboard_title": "🏆 <b>━━ أفضل اللاعبين ━━</b>",
    },
    "en": {
        "games_title": "🎮 <b>━━ GAMES CENTER ━━</b>\n\n🎯 <i>Play & Win Points!</i>",
        "games_desc": "✨ 3 Exciting games await",
        "btn_rps": "✂️ Rock Paper Scissors",
        "btn_ttt": "⭕ Tic Tac Toe",
        "btn_hunt": "🐾 Animal Hunt",
        "btn_stats": "📊 My Stats",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_back": "🔙 Back",
        "choose_mode": "🎯 <b>Choose game mode:</b>",
        "mode_ai": "🤖 Play vs AI",
        "mode_pvp": "👥 Play vs Real Player",
        "choose_bet": "💎 <b>Choose stakes:</b>",
        "bet_placeholder": "💫 Higher stakes = Bigger wins!",
        "already_played": "⏰ <b>Already played today!</b>\n\n🔄 Come back in: <b>{hours}h {mins}m</b>\n\n💡 <i>One try per day per game</i>",
        "insufficient": "❌ Not enough balance!",
        "searching_player": "🔍 <b>Searching for player...</b>\n\n⏳ Time left: {time}s\n\n💡 <i>You'll be matched with next available</i>",
        "no_players": "😔 <b>No players available</b>\n\n🤖 <i>Play vs AI instead?</i>",
        "game_starting": "🎊 <b>Match found!</b>\n\n⚡ Game starting...",
        "your_turn": "🎯 <b>Your turn!</b>\n\n⏰ 20 seconds",
        "opponent_turn": "⏳ <b>Opponent's turn...</b>",
        "you_won": "🎊 <b>You WON!</b>\n\n💎 Prize: <b>+{amount}</b>",
        "you_lost": "😔 <b>You lost this round</b>\n\n💔 Better luck next time!",
        "draw": "🤝 <b>Draw!</b>\n\n💰 Bet refunded",
        "rps_choose": "✂️ <b>Choose:</b>",
        "rock": "🪨 Rock",
        "paper": "📄 Paper",
        "scissors": "✂️ Scissors",
        "ttt_desc": "⭕ <b>Tic Tac Toe</b>\n\nGet 3 in a row to win!",
        "hunt_desc": "🐾 <b>Animal Hunt</b>\n\nEmojis appear for 2 seconds, click fast!",
        "hunt_ready": "⚡ <b>Get Ready!</b>\n\n🎯 <i>Animals appearing in 3 seconds...</i>",
        "hunt_go": "🎯 <b>Click Fast!</b>",
        "cheat_detected": "🚫 <b>Cheating detected!</b>\n\n⛔ Banned for 1 hour\n\n💡 <i>Don't play against yourself!</i>",
        "same_ip_warn": "⚠️ <b>Security Warning</b>\n\n🔒 Can't play against yourself!",
        "stats_title": "📊 <b>━━ My Stats ━━</b>\n\n🎮 Games: <b>{total}</b>\n🏆 Wins: <b>{wins}</b>\n💔 Losses: <b>{losses}</b>\n🤝 Draws: <b>{draws}</b>\n💎 Earnings: <b>{earnings}</b>\n📈 Win rate: <b>{winrate}%</b>",
        "leaderboard_title": "🏆 <b>━━ TOP PLAYERS ━━</b>",
    },
    "fr": {
        "games_title": "🎮 <b>━━ JEUX ━━</b>",
        "games_desc": "✨ 3 jeux passionnants",
        "btn_rps": "✂️ Pierre Papier Ciseaux",
        "btn_ttt": "⭕ Morpion",
        "btn_hunt": "🐾 Chasse aux Animaux",
        "btn_stats": "📊 Mes Stats",
        "btn_leaderboard": "🏆 Classement",
        "btn_back": "🔙 Retour",
        "choose_mode": "🎯 <b>Mode:</b>",
        "mode_ai": "🤖 vs IA",
        "mode_pvp": "👥 vs Joueur",
        "choose_bet": "💎 <b>Mise:</b>",
        "bet_placeholder": "💫 Plus haut = Plus gros gains!",
        "already_played": "⏰ <b>Déjà joué!</b>\n\n🔄 Revenez dans: {hours}h {mins}m",
        "insufficient": "❌ Solde insuffisant!",
        "searching_player": "🔍 Recherche... {time}s",
        "no_players": "😔 Personne disponible\n\n🤖 Jouer vs IA?",
        "game_starting": "🎊 Match trouvé!",
        "your_turn": "🎯 À votre tour!",
        "opponent_turn": "⏳ Tour de l'adversaire...",
        "you_won": "🎊 <b>Vous avez GAGNÉ!</b>\n\n💎 +{amount}",
        "you_lost": "😔 Perdu",
        "draw": "🤝 Égalité!",
        "rps_choose": "✂️ Choisissez:",
        "rock": "🪨 Pierre",
        "paper": "📄 Papier",
        "scissors": "✂️ Ciseaux",
        "ttt_desc": "⭕ <b>Morpion</b>\n\n3 alignés pour gagner!",
        "hunt_desc": "🐾 <b>Chasse</b>\n\nCliquez vite!",
        "hunt_ready": "⚡ Prêt!\n\n3 secondes...",
        "hunt_go": "🎯 <b>CLIQUEZ!</b>",
        "cheat_detected": "🚫 Triche détectée! Banni 1h",
        "same_ip_warn": "⚠️ Ne jouez pas contre vous-même!",
        "stats_title": "📊 Stats\n\n🎮 {total}\n🏆 {wins}\n💔 {losses}\n🤝 {draws}\n💎 {earnings}\n📈 {winrate}%",
        "leaderboard_title": "🏆 <b>TOP JOUEURS</b>",
    },
    "es": {
        "games_title": "🎮 <b>━━ JUEGOS ━━</b>",
        "games_desc": "✨ 3 juegos emocionantes",
        "btn_rps": "✂️ Piedra Papel Tijeras",
        "btn_ttt": "⭕ Tres en Raya",
        "btn_hunt": "🐾 Caza de Animales",
        "btn_stats": "📊 Mis Stats",
        "btn_leaderboard": "🏆 Ranking",
        "btn_back": "🔙 Atrás",
        "choose_mode": "🎯 <b>Modo:</b>",
        "mode_ai": "🤖 vs IA",
        "mode_pvp": "👥 vs Jugador",
        "choose_bet": "💎 <b>Apuesta:</b>",
        "bet_placeholder": "💫 ¡Más alto = Más premio!",
        "already_played": "⏰ ¡Ya jugaste!\n\n🔄 Vuelve en: {hours}h {mins}m",
        "insufficient": "❌ ¡Saldo insuficiente!",
        "searching_player": "🔍 Buscando... {time}s",
        "no_players": "😔 Nadie disponible\n\n🤖 ¿Jugar vs IA?",
        "game_starting": "🎊 ¡Partida encontrada!",
        "your_turn": "🎯 ¡Tu turno!",
        "opponent_turn": "⏳ Turno del rival...",
        "you_won": "🎊 <b>¡GANASTE!</b>\n\n💎 +{amount}",
        "you_lost": "😔 Perdiste",
        "draw": "🤝 ¡Empate!",
        "rps_choose": "✂️ Elige:",
        "rock": "🪨 Piedra",
        "paper": "📄 Papel",
        "scissors": "✂️ Tijeras",
        "ttt_desc": "⭕ <b>Tres en Raya</b>\n\n¡3 en línea gana!",
        "hunt_desc": "🐾 <b>Caza</b>\n\n¡Rápido!",
        "hunt_ready": "⚡ ¡Listo!\n\n3 segundos...",
        "hunt_go": "🎯 <b>¡CLICK!</b>",
        "cheat_detected": "🚫 ¡Trampa detectada! Baneado 1h",
        "same_ip_warn": "⚠️ ¡No juegues contra ti mismo!",
        "stats_title": "📊 Stats\n\n🎮 {total}\n🏆 {wins}\n💔 {losses}\n🤝 {draws}\n💎 {earnings}\n📈 {winrate}%",
        "leaderboard_title": "🏆 <b>TOP JUGADORES</b>",
    },
    "vi": {
        "games_title": "🎮 <b>━━ TRÒ CHƠI ━━</b>",
        "games_desc": "✨ 3 trò chơi thú vị",
        "btn_rps": "✂️ Kéo Búa Bao",
        "btn_ttt": "⭕ Cờ Caro",
        "btn_hunt": "🐾 Săn Thú",
        "btn_stats": "📊 Thống kê",
        "btn_leaderboard": "🏆 BXH",
        "btn_back": "🔙 Quay lại",
        "choose_mode": "🎯 <b>Chế độ:</b>",
        "mode_ai": "🤖 vs AI",
        "mode_pvp": "👥 vs Người thật",
        "choose_bet": "💎 <b>Đặt cược:</b>",
        "bet_placeholder": "💫 Cao hơn = Thắng nhiều!",
        "already_played": "⏰ Đã chơi hôm nay!\n\n🔄 Quay lại: {hours}h {mins}p",
        "insufficient": "❌ Không đủ!",
        "searching_player": "🔍 Đang tìm... {time}s",
        "no_players": "😔 Không ai\n\n🤖 Chơi vs AI?",
        "game_starting": "🎊 Tìm thấy!",
        "your_turn": "🎯 Lượt bạn!",
        "opponent_turn": "⏳ Đối thủ...",
        "you_won": "🎊 <b>THẮNG!</b>\n\n💎 +{amount}",
        "you_lost": "😔 Thua",
        "draw": "🤝 Hòa!",
        "rps_choose": "✂️ Chọn:",
        "rock": "🪨 Đá",
        "paper": "📄 Giấy",
        "scissors": "✂️ Kéo",
        "ttt_desc": "⭕ <b>Cờ Caro</b>\n\n3 hàng liên tiếp!",
        "hunt_desc": "🐾 <b>Săn</b>\n\nNhanh lên!",
        "hunt_ready": "⚡ Sẵn sàng!\n\n3 giây...",
        "hunt_go": "🎯 <b>NHẤN!</b>",
        "cheat_detected": "🚫 Phát hiện gian lận! Cấm 1h",
        "same_ip_warn": "⚠️ Không được chơi với chính mình!",
        "stats_title": "📊 Stats\n\n🎮 {total}\n🏆 {wins}\n💔 {losses}\n🤝 {draws}\n💎 {earnings}\n📈 {winrate}%",
        "leaderboard_title": "🏆 <b>TOP</b>",
    }
}

def gt(lang, key, **kwargs):
    """Get game translation"""
    if lang not in GAMES_LANG:
        lang = "en"
    txt = GAMES_LANG[lang].get(key, GAMES_LANG["en"].get(key, key))
    if kwargs:
        try:
            txt = txt.format(**kwargs)
        except:
            pass
    return txt

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_user_lang(uid):
    u = get_user(uid) or {}
    return u.get("lang", "ar")

def can_play_today(uid, game_type):
    """Check if user can play (once per day per game)"""
    uid = str(uid)
    last_played = bot_config.get("games_last_played", {})
    key = f"{uid}_{game_type}"
    
    if key not in last_played:
        return True, None
    
    try:
        last_time = datetime.fromisoformat(last_played[key])
        next_time = last_time + timedelta(hours=24)
        if datetime.now() >= next_time:
            return True, None
        remaining = next_time - datetime.now()
        hours = remaining.seconds // 3600
        mins = (remaining.seconds % 3600) // 60
        return False, {"hours": hours, "mins": mins}
    except:
        return True, None

def mark_played(uid, game_type):
    """Mark user as played today"""
    uid = str(uid)
    if "games_last_played" not in bot_config:
        bot_config["games_last_played"] = {}
    bot_config["games_last_played"][f"{uid}_{game_type}"] = datetime.now().isoformat()
    save_json(DB_CONFIG, bot_config)

def update_stats(uid, game_type, result, amount=0):
    """Update player statistics"""
    uid = str(uid)
    if "games_stats" not in bot_config:
        bot_config["games_stats"] = {}
    
    if uid not in bot_config["games_stats"]:
        bot_config["games_stats"][uid] = {
            "total": 0, "wins": 0, "losses": 0, "draws": 0, "earnings": 0
        }
    
    stats = bot_config["games_stats"][uid]
    stats["total"] += 1
    
    if result == "win":
        stats["wins"] += 1
        stats["earnings"] += amount
    elif result == "loss":
        stats["losses"] += 1
        stats["earnings"] -= amount
    elif result == "draw":
        stats["draws"] += 1
    
    save_json(DB_CONFIG, bot_config)

def check_anti_cheat(uid):
    """Check for cheating patterns"""
    uid = str(uid)
    banned = bot_config.get("games_banned_users", {})
    if uid in banned:
        try:
            until = datetime.fromisoformat(banned[uid]["until"])
            if datetime.now() < until:
                return False, "banned"
            else:
                del banned[uid]
                save_json(DB_CONFIG, bot_config)
        except: pass
    return True, "ok"

def ban_cheater(uid, hours=1):
    """Ban user for cheating"""
    uid = str(uid)
    if "games_banned_users" not in bot_config:
        bot_config["games_banned_users"] = {}
    until = (datetime.now() + timedelta(hours=hours)).isoformat()
    bot_config["games_banned_users"][uid] = {
        "until": until,
        "reason": "cheating"
    }
    save_json(DB_CONFIG, bot_config)

# =====================================================
# MAIN GAMES MENU
# =====================================================

@bot.message_handler(func=lambda message: message.text == "🎮 Mini Games")
def show_games_menu(message):
    uid = str(message.from_user.id)
    lang = get_user_lang(uid)
    
    msg = f"{gt(lang, 'games_title')}\n\n<i>{gt(lang, 'games_desc')}</i>"
    
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(gt(lang, "btn_rps"), callback_data="game_rps"))
    m.add(types.InlineKeyboardButton(gt(lang, "btn_ttt"), callback_data="game_ttt"))
    m.add(types.InlineKeyboardButton(gt(lang, "btn_hunt"), callback_data="game_hunt"))
    m.add(
        types.InlineKeyboardButton(gt(lang, "btn_stats"), callback_data="game_stats"),
        types.InlineKeyboardButton(gt(lang, "btn_leaderboard"), callback_data="game_leaderboard")
    )
    
    bot.send_message(message.chat.id, msg, reply_markup=m, parse_mode="HTML")

# =====================================================
# GAME SELECTION CALLBACKS
# =====================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def handle_game_menu(call):
    uid = str(call.from_user.id)
    lang = get_user_lang(uid)
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # Show stats
    if data == "game_stats":
        stats = bot_config.get("games_stats", {}).get(uid, {
            "total": 0, "wins": 0, "losses": 0, "draws": 0, "earnings": 0
        })
        winrate = round((stats["wins"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0
        msg = gt(lang, "stats_title",
                 total=stats["total"], wins=stats["wins"],
                 losses=stats["losses"], draws=stats["draws"],
                 earnings=stats["earnings"], winrate=winrate)
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(gt(lang, "btn_back"), callback_data="game_back"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return
    
    # Show leaderboard
    if data == "game_leaderboard":
        stats_all = bot_config.get("games_stats", {})
        sorted_players = sorted(stats_all.items(), key=lambda x: x[1].get("earnings", 0), reverse=True)[:10]
        
        msg = gt(lang, "leaderboard_title") + "\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, (pid, pstats) in enumerate(sorted_players):
            u = get_user(pid) or {}
            uname = u.get("username", "N/A")
            wins = pstats.get("wins", 0)
            earnings = pstats.get("earnings", 0)
            msg += f"{medals[i]} @{uname} - 🏆{wins} | 💎{earnings}\n"
        
        if not sorted_players:
            msg += "\n<i>No players yet!</i>"
        
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton(gt(lang, "btn_back"), callback_data="game_back"))
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return
    
    # Back to games menu
    if data == "game_back":
        msg = f"{gt(lang, 'games_title')}\n\n<i>{gt(lang, 'games_desc')}</i>"
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton(gt(lang, "btn_rps"), callback_data="game_rps"))
        m.add(types.InlineKeyboardButton(gt(lang, "btn_ttt"), callback_data="game_ttt"))
        m.add(types.InlineKeyboardButton(gt(lang, "btn_hunt"), callback_data="game_hunt"))
        m.add(
            types.InlineKeyboardButton(gt(lang, "btn_stats"), callback_data="game_stats"),
            types.InlineKeyboardButton(gt(lang, "btn_leaderboard"), callback_data="game_leaderboard")
        )
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return
    
    # Select game type
    if data in ["game_rps", "game_ttt", "game_hunt"]:
        game_type = data.split("_")[1]
        
        # Check daily limit
        can_play, wait_info = can_play_today(uid, game_type)
        if not can_play:
            bot.answer_callback_query(call.id,
                gt(lang, "already_played", hours=wait_info["hours"], mins=wait_info["mins"]),
                show_alert=True)
            return
        
        # Check cheat ban
        allowed, reason = check_anti_cheat(uid)
        if not allowed:
            bot.answer_callback_query(call.id, gt(lang, "cheat_detected"), show_alert=True)
            return
        
        # Show mode selection
        game_names = {"rps": gt(lang, "btn_rps"), "ttt": gt(lang, "btn_ttt"), "hunt": gt(lang, "btn_hunt")}
        msg = f"{game_names[game_type]}\n\n{gt(lang, 'choose_mode')}"
        
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton(gt(lang, "mode_ai"), callback_data=f"mode_ai_{game_type}"))
        m.add(types.InlineKeyboardButton(gt(lang, "mode_pvp"), callback_data=f"mode_pvp_{game_type}"))
        m.add(types.InlineKeyboardButton(gt(lang, "btn_back"), callback_data="game_back"))
        
        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
        except: pass
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith("mode_"))
def handle_mode_selection(call):
    uid = str(call.from_user.id)
    lang = get_user_lang(uid)
    parts = call.data.split("_")
    mode = parts[1]  # ai or pvp
    game_type = parts[2]  # rps, ttt, hunt
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # Store setup
    temp_bet_setup[uid] = {"game": game_type, "mode": mode}
    
    # Show bet selection
    msg = f"{gt(lang, 'choose_bet')}\n\n<i>{gt(lang, 'bet_placeholder')}</i>"
    
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton("1 💎", callback_data="bet_1"),
        types.InlineKeyboardButton("2 💎", callback_data="bet_2"),
        types.InlineKeyboardButton("3 💎", callback_data="bet_3")
    )
    m.add(types.InlineKeyboardButton(gt(lang, "btn_back"), callback_data="game_back"))
    
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("bet_"))
def handle_bet_selection(call):
    uid = str(call.from_user.id)
    lang = get_user_lang(uid)
    u = get_user(uid) or {}
    bet = int(call.data.split("_")[1])
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # Check user has enough
    if u.get("points", 0) < bet:
        bot.answer_callback_query(call.id, gt(lang, "insufficient"), show_alert=True)
        return
    
    # Get game setup
    setup = temp_bet_setup.get(uid, {})
    if not setup:
        bot.answer_callback_query(call.id, "Error", show_alert=True)
        return
    
    setup["bet"] = bet
    game_type = setup["game"]
    mode = setup["mode"]
    
    # Deduct bet
    update_user_data(uid, points=-bet)
    mark_played(uid, game_type)
    
    # Start game
    if mode == "ai":
        start_game_vs_ai(chat_id, msg_id, uid, game_type, bet)
    else:
        start_game_pvp(chat_id, msg_id, uid, game_type, bet)

# =====================================================
# ROCK PAPER SCISSORS
# =====================================================

def start_rps_ai(chat_id, msg_id, uid, bet):
    lang = get_user_lang(uid)
    game_id = f"rps_ai_{uid}_{int(time.time())}"
    active_games[game_id] = {
        "type": "rps", "mode": "ai", "player": uid, "bet": bet
    }
    user_current_game[uid] = game_id
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║  ✂️ <b>ROCK PAPER SCISSORS</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"💎 <b>Play:</b> {bet}\n"
        f"🎯 <b>Win:</b> +{bet*2}\n\n"
        f"{gt(lang, 'rps_choose')}"
    )
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(
        types.InlineKeyboardButton(gt(lang, "rock"), callback_data=f"rps_r_{game_id}"),
        types.InlineKeyboardButton(gt(lang, "paper"), callback_data=f"rps_p_{game_id}"),
        types.InlineKeyboardButton(gt(lang, "scissors"), callback_data=f"rps_s_{game_id}")
    )
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("rps_"))
def handle_rps_choice(call):
    uid = str(call.from_user.id)
    lang = get_user_lang(uid)
    parts = call.data.split("_", 2)
    player_choice = parts[1]  # r, p, s
    game_id = parts[2]
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if game_id not in active_games:
        return
    
    game = active_games[game_id]
    bet = game["bet"]
    
    # AI choice (70% wins by picking counter)
    counter = {"r": "p", "p": "s", "s": "r"}  # counter to player's choice
    if random.random() < 0.70:  # 70% AI wins
        ai_choice = counter[player_choice]
    elif random.random() < 0.50:  # 15% AI loses
        ai_choice = counter[counter[player_choice]]
    else:  # 15% draw
        ai_choice = player_choice
    
    # Animation
    emojis = {"r": "🪨", "p": "📄", "s": "✂️"}
    animation_frames = [
        "🎰 <b>Playing...</b>",
        f"🪨 vs ✂️",
        f"📄 vs 🪨",
        f"✂️ vs 📄",
    ]
    for f in animation_frames:
        try:
            bot.edit_message_text(f, chat_id, msg_id, parse_mode="HTML")
            time.sleep(0.3)
        except: pass
    
    # Determine winner
    player_emoji = emojis[player_choice]
    ai_emoji = emojis[ai_choice]
    
    if player_choice == ai_choice:
        result = "draw"
        update_user_data(uid, points=bet)  # Refund
        outcome_msg = gt(lang, "draw")
    elif (player_choice == "r" and ai_choice == "s") or \
         (player_choice == "p" and ai_choice == "r") or \
         (player_choice == "s" and ai_choice == "p"):
        result = "win"
        update_user_data(uid, points=bet*2, accumulated_points=bet)
        update_user_rank_and_quests(uid)
        outcome_msg = gt(lang, "you_won", amount=bet)
    else:
        result = "loss"
        outcome_msg = gt(lang, "you_lost")
    
    # Update stats
    update_stats(uid, "rps", result, bet)
    
    # Show result
    final_msg = (
        f"╔═══════════════════════╗\n"
        f"║  ✂️ <b>RESULT</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"👤 You: {player_emoji}\n"
        f"🤖 AI: {ai_emoji}\n\n"
        f"{outcome_msg}"
    )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(gt(lang, "btn_back"), callback_data="game_back"))
    
    try: bot.edit_message_text(final_msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass
    
    # Cleanup
    if game_id in active_games:
        del active_games[game_id]
    if uid in user_current_game:
        del user_current_game[uid]

# =====================================================
# TIC TAC TOE
# =====================================================

def start_ttt_ai(chat_id, msg_id, uid, bet):
    lang = get_user_lang(uid)
    game_id = f"ttt_ai_{uid}_{int(time.time())}"
    active_games[game_id] = {
        "type": "ttt", "mode": "ai", "player": uid, "bet": bet,
        "board": [" "] * 9, "turn": "player"
    }
    user_current_game[uid] = game_id
    show_ttt_board(chat_id, msg_id, game_id)

def show_ttt_board(chat_id, msg_id, game_id):
    if game_id not in active_games:
        return
    game = active_games[game_id]
    uid = game["player"]
    lang = get_user_lang(uid)
    board = game["board"]
    
    turn_msg = gt(lang, "your_turn") if game["turn"] == "player" else gt(lang, "opponent_turn")
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║  ⭕ <b>TIC TAC TOE</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"💎 Play: {game['bet']} | Win: +{game['bet']*2}\n\n"
        f"{turn_msg}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=3)
    display = {" ": "⬜", "X": "❌", "O": "⭕"}
    for row in range(3):
        buttons = []
        for col in range(3):
            idx = row * 3 + col
            emoji = display[board[idx]]
            if board[idx] == " " and game["turn"] == "player":
                buttons.append(types.InlineKeyboardButton(emoji, callback_data=f"ttt_{idx}_{game_id}"))
            else:
                buttons.append(types.InlineKeyboardButton(emoji, callback_data="ttt_none"))
        m.add(*buttons)
    
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass

def check_ttt_winner(board):
    lines = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    for line in lines:
        if board[line[0]] == board[line[1]] == board[line[2]] != " ":
            return board[line[0]]
    if " " not in board:
        return "draw"
    return None

def ai_ttt_move(board):
    """Smart AI with 70% win rate"""
    # Try to win first (70% of the time)
    if random.random() < 0.7:
        # Check winning move
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                if check_ttt_winner(board) == "O":
                    return i
                board[i] = " "
        # Block player
        for i in range(9):
            if board[i] == " ":
                board[i] = "X"
                if check_ttt_winner(board) == "X":
                    board[i] = "O"
                    return i
                board[i] = " "
    
    # Take center
    if board[4] == " " and random.random() < 0.5:
        return 4
    
    # Random move
    empty = [i for i in range(9) if board[i] == " "]
    if empty:
        return random.choice(empty)
    return None

@bot.callback_query_handler(func=lambda call: call.data.startswith("ttt_"))
def handle_ttt_move(call):
    uid = str(call.from_user.id)
    lang = get_user_lang(uid)
    parts = call.data.split("_", 2)
    
    if parts[1] == "none":
        bot.answer_callback_query(call.id)
        return
    
    try:
        idx = int(parts[1])
        game_id = parts[2]
    except:
        return
    
    if game_id not in active_games:
        return
    
    game = active_games[game_id]
    if game["turn"] != "player" or game["board"][idx] != " ":
        return
    
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    # Player move
    game["board"][idx] = "X"
    winner = check_ttt_winner(game["board"])
    
    if winner:
        end_ttt_game(chat_id, msg_id, game_id, winner)
        return
    
    # AI turn
    game["turn"] = "ai"
    show_ttt_board(chat_id, msg_id, game_id)
    time.sleep(1)
    
    ai_idx = ai_ttt_move(game["board"])
    if ai_idx is not None:
        game["board"][ai_idx] = "O"
        winner = check_ttt_winner(game["board"])
        if winner:
            end_ttt_game(chat_id, msg_id, game_id, winner)
            return
    
    game["turn"] = "player"
    show_ttt_board(chat_id, msg_id, game_id)

def end_ttt_game(chat_id, msg_id, game_id, winner):
    game = active_games.get(game_id)
    if not game: return
    uid = game["player"]
    lang = get_user_lang(uid)
    bet = game["bet"]
    
    if winner == "X":  # Player wins
        result = "win"
        update_user_data(uid, points=bet*2, accumulated_points=bet)
        update_user_rank_and_quests(uid)
        outcome = gt(lang, "you_won", amount=bet)
    elif winner == "draw":
        result = "draw"
        update_user_data(uid, points=bet)
        outcome = gt(lang, "draw")
    else:
        result = "loss"
        outcome = gt(lang, "you_lost")
    
    update_stats(uid, "ttt", result, bet)
    
    # Show board with result
    display = {" ": "⬜", "X": "❌", "O": "⭕"}
    board_str = ""
    for row in range(3):
        for col in range(3):
            board_str += display[game["board"][row*3+col]]
        board_str += "\n"
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║  ⭕ <b>GAME OVER</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"{board_str}\n"
        f"{outcome}"
    )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(gt(lang, "btn_back"), callback_data="game_back"))
    
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass
    
    if game_id in active_games:
        del active_games[game_id]
    if uid in user_current_game:
        del user_current_game[uid]

# =====================================================
# ANIMAL HUNT GAME
# =====================================================

ANIMALS = ["🐶", "🐱", "🐭", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵"]

def start_hunt_ai(chat_id, msg_id, uid, bet):
    lang = get_user_lang(uid)
    game_id = f"hunt_ai_{uid}_{int(time.time())}"
    active_games[game_id] = {
        "type": "hunt", "mode": "ai", "player": uid, "bet": bet,
        "score": 0, "ai_score": 0, "rounds": 0, "max_rounds": 5,
        "current_animals": []
    }
    user_current_game[uid] = game_id
    
    # Ready message
    ready_msg = f"{gt(lang, 'hunt_desc')}\n\n{gt(lang, 'hunt_ready')}"
    try: bot.edit_message_text(ready_msg, chat_id, msg_id, parse_mode="HTML")
    except: pass
    
    # Countdown
    for i in [3, 2, 1]:
        time.sleep(1)
        try:
            bot.edit_message_text(f"⏰ <b>{i}...</b>", chat_id, msg_id, parse_mode="HTML")
        except: pass
    
    # Start rounds
    play_hunt_round(chat_id, msg_id, game_id)

def play_hunt_round(chat_id, msg_id, game_id):
    if game_id not in active_games:
        return
    game = active_games[game_id]
    uid = game["player"]
    lang = get_user_lang(uid)
    
    if game["rounds"] >= game["max_rounds"]:
        end_hunt_game(chat_id, msg_id, game_id)
        return
    
    game["rounds"] += 1
    
    # Generate 4 animals (1 target, 3 distractors)
    target = random.choice(ANIMALS)
    others = random.sample([a for a in ANIMALS if a != target], 3)
    all_animals = [target] + others
    random.shuffle(all_animals)
    
    game["target"] = target
    game["current_animals"] = all_animals
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║  🐾 <b>Round {game['rounds']}/{game['max_rounds']}</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"🎯 <b>Find:</b> {target}\n\n"
        f"⚡ <b>Click FAST!</b>\n\n"
        f"👤 You: {game['score']} | 🤖 AI: {game['ai_score']}"
    )
    
    m = types.InlineKeyboardMarkup(row_width=4)
    m.add(*[types.InlineKeyboardButton(a, callback_data=f"hunt_{a}_{game_id}") for a in all_animals])
    
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass
    
    # Schedule AI response (70% win chance)
    def ai_response():
        time.sleep(random.uniform(1.5, 2.5))
        if game_id in active_games and active_games[game_id]["rounds"] == game["rounds"]:
            if random.random() < 0.70:  # AI wins this round
                active_games[game_id]["ai_score"] += 1
                # Auto move to next round
                time.sleep(0.5)
                if game_id in active_games:
                    play_hunt_round(chat_id, msg_id, game_id)
    
    threading.Thread(target=ai_response, daemon=True).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("hunt_"))
def handle_hunt_click(call):
    uid = str(call.from_user.id)
    parts = call.data.split("_", 2)
    animal = parts[1]
    game_id = parts[2]
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if game_id not in active_games:
        return
    
    game = active_games[game_id]
    
    if animal == game.get("target"):
        game["score"] += 1
    
    time.sleep(0.3)
    play_hunt_round(chat_id, msg_id, game_id)

def end_hunt_game(chat_id, msg_id, game_id):
    game = active_games.get(game_id)
    if not game: return
    uid = game["player"]
    lang = get_user_lang(uid)
    bet = game["bet"]
    
    if game["score"] > game["ai_score"]:
        result = "win"
        update_user_data(uid, points=bet*2, accumulated_points=bet)
        update_user_rank_and_quests(uid)
        outcome = gt(lang, "you_won", amount=bet)
    elif game["score"] == game["ai_score"]:
        result = "draw"
        update_user_data(uid, points=bet)
        outcome = gt(lang, "draw")
    else:
        result = "loss"
        outcome = gt(lang, "you_lost")
    
    update_stats(uid, "hunt", result, bet)
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"║  🐾 <b>GAME OVER</b>  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"👤 You: <b>{game['score']}</b>\n"
        f"🤖 AI: <b>{game['ai_score']}</b>\n\n"
        f"{outcome}"
    )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(gt(lang, "btn_back"), callback_data="game_back"))
    
    try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
    except: pass
    
    if game_id in active_games:
        del active_games[game_id]
    if uid in user_current_game:
        del user_current_game[uid]

# =====================================================
# GAME STARTERS
# =====================================================

def start_game_vs_ai(chat_id, msg_id, uid, game_type, bet):
    if game_type == "rps":
        start_rps_ai(chat_id, msg_id, uid, bet)
    elif game_type == "ttt":
        start_ttt_ai(chat_id, msg_id, uid, bet)
    elif game_type == "hunt":
        start_hunt_ai(chat_id, msg_id, uid, bet)

def start_game_pvp(chat_id, msg_id, uid, game_type, bet):
    """
    Try to find real player, if not found in 5 seconds,
    play against 'fake' AI opponent that pretends to be a player
    """
    lang = get_user_lang(uid)
    
    # Show searching animation
    for i in [5, 4, 3, 2, 1]:
        try:
            bot.edit_message_text(
                gt(lang, "searching_player", time=i),
                chat_id, msg_id, parse_mode="HTML")
            time.sleep(1)
        except: pass
    
    # After search timeout, connect to "fake player" (AI pretending)
    try:
        bot.edit_message_text(
            f"🎊 <b>Player Found!</b>\n\n"
            f"👤 Opponent: <i>Anonymous Player</i>\n"
            f"⚡ Match starting...",
            chat_id, msg_id, parse_mode="HTML")
        time.sleep(1.5)
    except: pass
    
    # Start game with hidden AI
    if game_type == "rps":
        start_rps_ai(chat_id, msg_id, uid, bet)
    elif game_type == "ttt":
        start_ttt_ai(chat_id, msg_id, uid, bet)
    elif game_type == "hunt":
        start_hunt_ai(chat_id, msg_id, uid, bet)

print("=" * 50)
print("✅ bot4.py loaded!")
print("🎮 Mini Games: Active")
print("✂️ Rock Paper Scissors: Ready")
print("⭕ Tic Tac Toe: Ready")
print("🐾 Animal Hunt: Ready")
print("🤖 AI System: Ready (70% win rate)")
print("=" * 50)
