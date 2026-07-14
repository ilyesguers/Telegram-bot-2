"""
=====================================================================
 bot6.py — ألعاب القناة/المجموعة التفاعلية (Reaction Games + Comment Races)
=====================================================================
⚠️ ملاحظة تقنية مهمة من تيليجرام (وليست قيداً مني):
   تيليجرام لا يرسل للبوت هوية الشخص الذي تفاعل بإيموجي على منشور
   "قناة" (Channel) — يرسل فقط عدّاد مجهول (message_reaction_count).
   لكي نعرف مين بالضبط تفاعل (لإعطائه/سحب نقاطه)، يجب أن تُنشر
   لعبة "التفاعل بإيموجي" داخل مجموعة (Group/Supergroup) — والحل
   الأمثل: مجموعة التعليقات (Discussion Group) المرتبطة بقناتك،
   لأن كل منشور بالقناة يظهر تلقائياً هناك ويمكن التفاعل معه فيها.
   لعبة "سباق التعليقات" تعمل بنفس المجموعة أيضاً.

   لذلك أول خطوة تعملها: ⚙️ "تعيين مجموعة الألعاب" (مرة وحدة فقط)
   بإرسال أي رسالة موجودة أصلاً داخل تلك المجموعة (Forward) للبوت،
   أو إرسال الـ ID الرقمي (سالب) مباشرة. تأكد أن البوت "أدمن" فيها.

📌 طريقة التركيب (لا تلمس أي شيء آخر في bot.py):
   ضع هذا السطر بعد "from bot2 import (...)" في bot.py:

        import bot6

   البوت سيبدأ تلقائياً باستقبال تحديثات التفاعلات (Reactions) دون
   الحاجة لتعديل سطر bot.infinity_polling(...) الموجود أصلاً.
=====================================================================
"""

import random
import string
from datetime import datetime

from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY
from database import (bot_config, save_json, DB_CONFIG, get_user,
                       update_user_data, update_user_rank_and_quests)

# =====================================================================
# 🔧 تفعيل استقبال تحديثات "التفاعلات" تلقائياً
# (bot.py ينادي bot.infinity_polling(none_stop=True, timeout=60) بدون
#  تحديد allowed_updates ← لن تصل تفاعلات الإيموجي إطلاقاً افتراضياً.
#  الحل: نغلّف الدالة بذكاء دون تعديل bot.py على الإطلاق)
# =====================================================================
_original_infinity_polling = bot.infinity_polling


def _patched_infinity_polling(*args, **kwargs):
    kwargs.setdefault("allowed_updates", [
        "message", "edited_message", "callback_query",
        "message_reaction", "message_reaction_count", "chat_member"
    ])
    return _original_infinity_polling(*args, **kwargs)


bot.infinity_polling = _patched_infinity_polling

_original_polling = bot.polling


def _patched_polling(*args, **kwargs):
    kwargs.setdefault("allowed_updates", [
        "message", "edited_message", "callback_query",
        "message_reaction", "message_reaction_count", "chat_member"
    ])
    return _original_polling(*args, **kwargs)


bot.polling = _patched_polling


# =====================================================================
# 🗂️ تهيئة التخزين (داخل bot_config نفسه — محمي تلقائياً عبر bot5.py)
# =====================================================================
def _init_defaults():
    ig = bot_config.setdefault("interactive_games", {})
    ig.setdefault("games_chat_id", None)
    ig.setdefault("reaction_games", {})
    ig.setdefault("race_games", {})
    save_json(DB_CONFIG, bot_config)


_init_defaults()

temp_setup = {}  # {admin_uid: {...بيانات الإعداد المؤقتة أثناء إنشاء لعبة...}}


def _is_admin(uid):
    try:
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
            return True
    except Exception:
        pass
    u = get_user(str(uid)) or {}
    return bool(u.get("is_admin", False))


def _is_games_chat(message):
    try:
        ig = bot_config.get("interactive_games", {})
        return (message.chat.id == ig.get("games_chat_id")
                and message.chat.type in ("group", "supergroup"))
    except Exception:
        return False


# =====================================================================
# 🖥️ لوحة الأدمن الرئيسية للألعاب
# =====================================================================
def _show_games_panel(chat_id, msg_id=None):
    ig = bot_config.get("interactive_games", {})
    gcid = ig.get("games_chat_id")
    active_r = sum(1 for g in ig.get("reaction_games", {}).values() if g.get("status") == "active")
    active_c = sum(1 for g in ig.get("race_games", {}).values() if g.get("status") == "active")
    txt = (
        "╔═══════════════════════╗\n"
        "║ 🎮 ألعاب القناة التفاعلية ║\n"
        "╚═══════════════════════╝\n\n"
        f"📍 مجموعة الألعاب: {gcid if gcid else '❌ غير محددة بعد'}\n"
        f"🔥 ألعاب تفاعل نشطة: {active_r}\n"
        f"🏁 سباقات تعليقات نشطة: {active_c}\n\n"
        "💡 اختر إجراءً:"
    )
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⚙️ تعيين مجموعة الألعاب", callback_data="igadm_setchat"))
    m.add(types.InlineKeyboardButton("🔥 إنشاء لعبة تفاعل إيموجي", callback_data="igadm_newreact"))
    m.add(types.InlineKeyboardButton("🏁 إنشاء سباق تعليقات", callback_data="igadm_newrace"))
    m.add(types.InlineKeyboardButton("📋 عرض / إدارة الألعاب النشطة", callback_data="igadm_list"))
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="igadm_refresh"))
    if msg_id:
        try:
            bot.edit_message_text(txt, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except Exception:
            pass
    bot.send_message(chat_id, txt, reply_markup=m, parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text == "🎮 ألعاب القناة التفاعلية")
def _open_games_panel(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid):
        return
    _show_games_panel(message.chat.id)


# =====================================================================
# 🖱️ كولباك الأدمن
# =====================================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("igadm_"))
def _games_admin_cb(call):
    uid = str(call.from_user.id)
    if not _is_admin(uid):
        return bot.answer_callback_query(call.id, "❌ صلاحيات الإدارة فقط", show_alert=True)

    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if data == "igadm_refresh":
        return _show_games_panel(chat_id, msg_id)

    if data == "igadm_setchat":
        msg = bot.send_message(chat_id, "📩 مرّر (Forward) أي رسالة من مجموعة الألعاب، أو أرسل الـ ID الرقمي (سالب) مباشرة:")
        bot.register_next_step_handler(msg, _process_set_chat)
        return

    if data == "igadm_newreact":
        temp_setup[uid] = {"type": "react"}
        msg = bot.send_message(chat_id, "📝 اكتب نص إعلان اللعبة (مثال: تفاعل معنا واربح جوائز رائعة!):")
        bot.register_next_step_handler(msg, _process_react_text)
        return

    if data == "igadm_newrace":
        temp_setup[uid] = {"type": "race"}
        msg = bot.send_message(chat_id, "✍️ اكتب الكلمة أو الإيموجي الذي يجب على المستخدمين كتابته في التعليقات:")
        bot.register_next_step_handler(msg, _process_race_keyword)
        return

    if data == "igadm_list":
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_end_r_"):
        gid = data.split("igadm_end_r_")[1]
        g = bot_config.get("interactive_games", {}).get("reaction_games", {}).get(gid)
        if g:
            g["status"] = "ended"
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅ تم إنهاء اللعبة (النقاط الممنوحة تبقى)")
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_cancel_r_"):
        gid = data.split("igadm_cancel_r_")[1]
        g = bot_config.get("interactive_games", {}).get("reaction_games", {}).get(gid)
        if g:
            for wuid, w in list(g.get("winners", {}).items()):
                pts = w.get("points", 0)
                update_user_data(wuid, points=-pts, accumulated_points=-pts)
            g["status"] = "cancelled"
            g["winners"] = {}
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "🗑️ أُلغيت اللعبة واسترجعت كل النقاط الممنوحة", show_alert=True)
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_end_c_"):
        rid = data.split("igadm_end_c_")[1]
        r = bot_config.get("interactive_games", {}).get("race_games", {}).get(rid)
        if r:
            r["status"] = "ended"
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "✅ تم إنهاء السباق")
        return _show_active_list(chat_id, msg_id)

    if data.startswith("igadm_cancel_c_"):
        rid = data.split("igadm_cancel_c_")[1]
        r = bot_config.get("interactive_games", {}).get("race_games", {}).get(rid)
        if r:
            for wuid, w in list(r.get("winners", {}).items()):
                pts = w.get("points", 0)
                update_user_data(wuid, points=-pts, accumulated_points=-pts)
            r["status"] = "cancelled"
            r["winners"] = {}
            save_json(DB_CONFIG, bot_config)
        bot.answer_callback_query(call.id, "🗑️ أُلغي السباق واسترجعت كل النقاط الممنوحة", show_alert=True)
        return _show_active_list(chat_id, msg_id)


def _show_active_list(chat_id, msg_id=None):
    ig = bot_config.get("interactive_games", {})
    rg = ig.get("reaction_games", {})
    cg = ig.get("race_games", {})
    m = types.InlineKeyboardMarkup(row_width=1)
    txt = "📋 ━━ الألعاب ━━ \n\n"
    found = False
    for gid, g in rg.items():
        if g.get("status") not in ("active", "full"):
            continue
        found = True
        txt += f"🔥 {gid} | {g.get('emoji')} | 👥 {len(g.get('winners', {}))}/{g.get('max_winners')} | 💎{g.get('points')} | {g.get('status')}\n"
        m.add(types.InlineKeyboardButton(f"⏹️ إنهاء {gid}", callback_data=f"igadm_end_r_{gid}"))
        m.add(types.InlineKeyboardButton(f"🗑️ إلغاء واسترجاع {gid}", callback_data=f"igadm_cancel_r_{gid}"))
    for rid, r in cg.items():
        if r.get("status") != "active":
            continue
        found = True
        txt += f"🏁 {rid} | '{r.get('keyword')}' | 👥 {len(r.get('winners', {}))}/{r.get('max_winners')} | 💎{r.get('points')}\n"
        m.add(types.InlineKeyboardButton(f"⏹️ إنهاء {rid}", callback_data=f"igadm_end_c_{rid}"))
        m.add(types.InlineKeyboardButton(f"🗑️ إلغاء واسترجاع {rid}", callback_data=f"igadm_cancel_c_{rid}"))
    if not found:
        txt += "📭 لا توجد ألعاب نشطة حالياً"
    m.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="igadm_refresh"))
    if msg_id:
        try:
            bot.edit_message_text(txt, chat_id, msg_id, reply_markup=m, parse_mode="HTML")
            return
        except Exception:
            pass
    bot.send_message(chat_id, txt, reply_markup=m, parse_mode="HTML")


# =====================================================================
# 📥 خطوات إنشاء لعبة (Next Step Handlers)
# =====================================================================
def _process_set_chat(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid):
        return
    chat_id_val = None
    if getattr(message, "forward_from_chat", None):
        chat_id_val = message.forward_from_chat.id
    else:
        try:
            chat_id_val = int(message.text.strip())
        except Exception:
            pass
    if not chat_id_val:
        bot.send_message(message.chat.id, "❌ لم أستطع تحديد المجموعة، حاول مجدداً من القائمة")
        return
    bot_config["interactive_games"]["games_chat_id"] = chat_id_val
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, f"✅ تم تعيين مجموعة الألعاب بنجاح: {chat_id_val}\n\n⚠️ تأكد أن البوت أدمن في تلك المجموعة!")


def _process_react_text(message):
    uid = str(message.from_user.id)
    if uid not in temp_setup:
        return
    temp_setup[uid]["text"] = message.text
    msg = bot.send_message(message.chat.id, "😀 أرسل الآن الإيموجي المطلوب للتفاعل (مثال: 🔥):")
    bot.register_next_step_handler(msg, _process_react_emoji)


def _process_react_emoji(message):
    uid = str(message.from_user.id)
    if uid not in temp_setup:
        return
    temp_setup[uid]["emoji"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "💎 كم نقطة يحصل عليها كل فائز؟")
    bot.register_next_step_handler(msg, _process_react_points)


def _process_react_points(message):
    uid = str(message.from_user.id)
    if uid not in temp_setup:
        return
    try:
        temp_setup[uid]["points"] = int(message.text.strip())
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط، ابدأ من جديد من القائمة")
        temp_setup.pop(uid, None)
        return
    msg = bot.send_message(message.chat.id, "👥 كم عدد الفائزين الأوائل المسموح؟ (مثال: 4)")
    bot.register_next_step_handler(msg, _process_react_maxwin)


def _process_react_maxwin(message):
    uid = str(message.from_user.id)
    if uid not in temp_setup:
        return
    try:
        max_w = int(message.text.strip())
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")
        temp_setup.pop(uid, None)
        return
    setup = temp_setup.pop(uid)
    ig = bot_config.setdefault("interactive_games", {})
    gcid = ig.get("games_chat_id")
    if not gcid:
        bot.send_message(message.chat.id, "❌ يجب تعيين مجموعة الألعاب أولاً (⚙️ تعيين مجموعة الألعاب)")
        return
    gid = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    text_final = (
        "╔═══════════════════════╗\n"
        "║    🔥 لعبة تفاعل! 🔥    ║\n"
        "╚═══════════════════════╝\n\n"
        f"{setup['text']}\n\n"
        f"👇 تفاعل بـ {setup['emoji']} على هذه الرسالة بالضبط\n"
        f"💎 الجائزة: {setup['points']} نقطة لكل فائز\n"
        f"👥 أول {max_w} فقط يفوزون!\n\n"
        "⚠️ إذا أزلت تفاعلك لاحقاً، ستُسحب نقاطك تلقائياً!"
    )
    try:
        sent = bot.send_message(gcid, text_final, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل النشر في المجموعة: {e}")
        return
    ig.setdefault("reaction_games", {})[gid] = {
        "chat_id": gcid, "message_id": sent.message_id, "emoji": setup["emoji"],
        "points": setup["points"], "max_winners": max_w, "winners": {},
        "status": "active", "text": setup["text"], "created_at": datetime.now().isoformat()
    }
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, f"✅ نُشرت اللعبة بنجاح! 🆔 {gid}")


def _process_race_keyword(message):
    uid = str(message.from_user.id)
    if uid not in temp_setup:
        return
    temp_setup[uid]["keyword"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "💎 كم نقطة يحصل عليها كل فائز؟")
    bot.register_next_step_handler(msg, _process_race_points)


def _process_race_points(message):
    uid = str(message.from_user.id)
    if uid not in temp_setup:
        return
    try:
        temp_setup[uid]["points"] = int(message.text.strip())
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")
        temp_setup.pop(uid, None)
        return
    msg = bot.send_message(message.chat.id, "👥 كم عدد الفائزين؟ (مثال: 4)")
    bot.register_next_step_handler(msg, _process_race_maxwin)


def _process_race_maxwin(message):
    uid = str(message.from_user.id)
    if uid not in temp_setup:
        return
    try:
        max_w = int(message.text.strip())
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")
        temp_setup.pop(uid, None)
        return
    setup = temp_setup.pop(uid)
    ig = bot_config.setdefault("interactive_games", {})
    gcid = ig.get("games_chat_id")
    if not gcid:
        bot.send_message(message.chat.id, "❌ يجب تعيين مجموعة الألعاب أولاً")
        return
    rid = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    text_final = (
        "╔═══════════════════════╗\n"
        "║   🏁 سباق التعليقات! 🏁   ║\n"
        "╚═══════════════════════╝\n\n"
        f"✍️ أول {max_w} أشخاص يكتبون:\n\n"
        f"👉 {setup['keyword']} 👈\n\n"
        f"💎 الجائزة: {setup['points']} نقطة لكل فائز\n\n"
        "🏃 استعدوا... انطلقوا!"
    )
    try:
        sent = bot.send_message(gcid, text_final, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل النشر: {e}")
        return
    ig.setdefault("race_games", {})[rid] = {
        "chat_id": gcid, "keyword": setup["keyword"], "points": setup["points"],
        "max_winners": max_w, "winners": {}, "status": "active",
        "created_at": datetime.now().isoformat()
    }
    save_json(DB_CONFIG, bot_config)
    bot.send_message(message.chat.id, f"✅ انطلق السباق بنجاح! 🆔 {rid}")


# =====================================================================
# 🎯 مُعالج تحديثات التفاعل (Reactions) — القلب الحقيقي للعبة
# =====================================================================
@bot.message_reaction_handler(func=lambda upd: True)
def _on_reaction(upd):
    try:
        if not getattr(upd, "user", None):
            return  # تفاعل مجهول (قناة / أدمن مجهول) — نتجاهله لعدم القدرة على تحديد الهوية
        uid = str(upd.user.id)
        games = bot_config.get("interactive_games", {}).get("reaction_games", {})
        for gid, g in games.items():
            if g.get("status") != "active":
                continue
            if g.get("chat_id") != upd.chat.id or g.get("message_id") != upd.message_id:
                continue

            target = g.get("emoji")
            new_set = {r.emoji for r in (upd.new_reaction or []) if getattr(r, "emoji", None)}
            old_set = {r.emoji for r in (upd.old_reaction or []) if getattr(r, "emoji", None)}
            winners = g.setdefault("winners", {})

            # ✅ إضافة رياكشن الهدف = فوز بنقاط
            if target in new_set and target not in old_set:
                if uid in winners or len(winners) >= g.get("max_winners", 0):
                    continue
                pts = g.get("points", 0)
                update_user_data(uid, points=pts, accumulated_points=pts)
                update_user_rank_and_quests(uid)
                winners[uid] = {"points": pts, "time": datetime.now().isoformat(), "place": len(winners) + 1}
                save_json(DB_CONFIG, bot_config)
                try:
                    bot.send_message(int(uid), f"🎉 مبروك! فزت بـ {pts} 💎 لتفاعلك بـ {target} في لعبة القناة!", parse_mode="HTML")
                except Exception:
                    pass
                if len(winners) >= g.get("max_winners", 0):
                    g["status"] = "full"
                    save_json(DB_CONFIG, bot_config)
                    try:
                        bot.send_message(g["chat_id"], "🏁 اكتملت اللعبة! تم توزيع كل الجوائز 🎉", reply_to_message_id=g["message_id"])
                    except Exception:
                        pass

            # ⚠️ إزالة رياكشن الهدف = سحب النقاط تلقائياً (طلب الأدمن)
            elif target in old_set and target not in new_set:
                if uid in winners:
                    pts = winners[uid].get("points", 0)
                    update_user_data(uid, points=-pts, accumulated_points=-pts)
                    del winners[uid]
                    if g.get("status") == "full":
                        g["status"] = "active"  # فتح مكان جديد
                    save_json(DB_CONFIG, bot_config)
                    try:
                        bot.send_message(int(uid), f"⚠️ تم سحب {pts} 💎 منك لأنك أزلت تفاعلك بـ {target}", parse_mode="HTML")
                    except Exception:
                        pass
    except Exception as e:
        print(f"⚠️ bot6 reaction handler error: {e}")


# =====================================================================
# 🏁 مُعالج سباق التعليقات (رسائل نصية داخل مجموعة الألعاب)
# =====================================================================
@bot.message_handler(func=_is_games_chat, content_types=['text'])
def _on_race_message(message):
    try:
        if not message.from_user:
            return
        uid = str(message.from_user.id)
        txt = (message.text or "").strip().lower()
        races = bot_config.get("interactive_games", {}).get("race_games", {})
        for rid, r in races.items():
            if r.get("status") != "active" or r.get("chat_id") != message.chat.id:
                continue
            keyword = (r.get("keyword") or "").strip().lower()
            if not keyword or keyword != txt:
                continue
            winners = r.setdefault("winners", {})
            if uid in winners or len(winners) >= r.get("max_winners", 0):
                continue
            pts = r.get("points", 0)
            place = len(winners) + 1
            winners[uid] = {
                "points": pts, "place": place, "time": datetime.now().isoformat(),
                "username": message.from_user.username or message.from_user.first_name
            }
            update_user_data(uid, points=pts, accumulated_points=pts)
            update_user_rank_and_quests(uid)
            save_json(DB_CONFIG, bot_config)
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(place, "🏅")
            try:
                bot.reply_to(message, f"{medal} مبروك! أنت الفائز رقم {place}!\n💎 +{pts} نقطة أُضيفت لرصيدك فوراً!", parse_mode="HTML")
            except Exception:
                pass
            if len(winners) >= r.get("max_winners", 0):
                r["status"] = "ended"
                save_json(DB_CONFIG, bot_config)
                try:
                    bot.send_message(message.chat.id, "🏁 انتهى السباق! تم الحصول على جميع الجوائز 🎉", parse_mode="HTML")
                except Exception:
                    pass
            break
    except Exception as e:
        print(f"⚠️ bot6 race handler error: {e}")


print("=" * 55)
print("✅ bot6.py — ألعاب القناة التفاعلية جاهزة!")
print("🔥 لعبة التفاعل بالإيموجي: نشطة")
print("🏁 سباق التعليقات: نشط")
print("📡 استقبال تحديثات Reactions: مُفعّل تلقائياً")
print("=" * 55)
