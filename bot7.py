"""
=====================================================================
 bot7.py — لوحة التحكم الشاملة بالأعضاء (User Control Panel)
=====================================================================
🎯 تحكم كامل بأي عضو: نقاطه، مكافأته اليومية، سلسلته، رتبته، VIP،
   صلاحياته، حظره، لغته، إشعاراته، مشترياته، تذاكره، إحالاته،
   مراسلته مباشرة، أو حتى حذف حسابه نهائياً.

📌 طريقة التركيب (لا تلمس أي شيء آخر في bot.py):
   ضع هذا السطر بعد "import bot6" (أو بعد "from bot2 import (...)"):

        import bot7
=====================================================================
"""

from telebot import types
from config import bot, ADMIN_PRIMARY, ADMIN_SECONDARY, RANKS
from database import (get_user, update_user_data, update_user_rank_and_quests,
                       search_user, ban_user, unban_user, engine, text,
                       bot_config)

try:
    from bot2 import activate_vip, deactivate_vip, get_vip_days_left, is_vip_active
    _VIP_AVAILABLE = True
except Exception:
    _VIP_AVAILABLE = False


def _is_admin(uid):
    try:
        if int(uid) in [ADMIN_PRIMARY, ADMIN_SECONDARY]:
            return True
    except Exception:
        pass
    u = get_user(str(uid)) or {}
    return bool(u.get("is_admin", False))


def _set_field_raw(uid, field, value):
    """تعديل مباشر لحقل رقمي/نصي بدقة (وليس تجميع/إضافة)"""
    allowed = {"points", "accumulated_points", "streak_days", "last_claim", "banned_until"}
    if field not in allowed:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(f"UPDATE users SET {field} = :v WHERE uid = :uid"),
                         {"v": value, "uid": str(uid)})
            conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ bot7 set field error: {e}")
        return False


def _profile_text(u):
    target = u.get("uid")
    role = "👑 المالك" if int(target) == ADMIN_PRIMARY else ("🛡️ أدمن" if u.get("is_admin") else "👤 عضو")
    ban = "⛔ محظور دائم" if u.get("banned") else ("⏱️ محظور مؤقت" if u.get("banned_until") else "🟢 نشط")
    vip_txt = "❌"
    if _VIP_AVAILABLE:
        try:
            if is_vip_active(target):
                vip_txt = f"👑 نعم ({get_vip_days_left(target)} يوم متبقي)"
        except Exception:
            pass
    return (
        "╔═══════════════════════╗\n"
        "║ 🧑‍💻 ملف العضو الكامل ║\n"
        "╚═══════════════════════╝\n\n"
        f"🆔 الآيدي: {target}\n"
        f"📝 المعرف: @{u.get('username', 'N/A')}\n"
        f"🎖️ الصلاحية: {role}\n"
        f"🔴 الحالة: {ban}\n"
        f"👑 VIP: {vip_txt}\n\n"
        f"💰 الرصيد: {u.get('points', 0)} 💎\n"
        f"📊 التراكمي: {u.get('accumulated_points', 0)} 💎\n"
        f"🏆 الرتبة: {u.get('rank', '—')} (خصم {int((u.get('rank_discount') or 0) * 100)}%)\n"
        f"🔥 سلسلة الأيام: {u.get('streak_days', 0)}\n"
        f"🕐 آخر مطالبة يومية: {u.get('last_claim') or '—'}\n"
        f"👥 عدد دعواته: {u.get('invite_count', 0)}\n"
        f"💵 أرباح الإحالة: {u.get('referral_earnings', 0)}\n"
        f"🔗 مدعو من: {u.get('invited_by') or '—'}\n"
        f"🛒 عدد المشتريات: {u.get('purchases_count', 0)}\n"
        f"💸 إجمالي إنفاقه: {u.get('total_spent', 0)}\n"
        f"🌐 اللغة: {u.get('lang', 'ar')}\n"
        f"🔔 الإشعارات: {'✅ مفعلة' if u.get('notifications_on', True) else '❌ معطلة'}\n"
        f"🎨 الثيم: {u.get('theme', 'dark')}\n"
        f"✅ موثّق: {'نعم' if u.get('verified') else 'لا'}\n"
        f"📅 تاريخ الانضمام: {(u.get('join_date') or '—')[:10]}\n"
        f"🕓 آخر نشاط: {(u.get('last_active') or '—')[:16]}\n"
        f"🎯 المهام المكتملة: {u.get('completed_quests') or '—'}"
    )


def _profile_keyboard(uid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"ucp_addpts_{uid}"),
        types.InlineKeyboardButton("➖ خصم نقاط", callback_data=f"ucp_subpts_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("✏️ تحديد رصيد بدقة", callback_data=f"ucp_setpts_{uid}"),
        types.InlineKeyboardButton("🔄 إعادة ضبط اليومية", callback_data=f"ucp_resetdaily_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("🔥 تعديل السلسلة", callback_data=f"ucp_setstreak_{uid}"),
        types.InlineKeyboardButton("🏆 تغيير الرتبة", callback_data=f"ucp_rank_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("👑 منح VIP", callback_data=f"ucp_vipgrant_{uid}"),
        types.InlineKeyboardButton("❌ سحب VIP", callback_data=f"ucp_vipremove_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("🛡️ تبديل صلاحية الأدمن", callback_data=f"ucp_admintoggle_{uid}"),
        types.InlineKeyboardButton("🔔 تبديل الإشعارات", callback_data=f"ucp_notiftoggle_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("⛔ حظر دائم", callback_data=f"ucp_banperm_{uid}"),
        types.InlineKeyboardButton("⏱️ حظر 24 ساعة", callback_data=f"ucp_bantemp_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("🟢 فك الحظر", callback_data=f"ucp_unban_{uid}"),
        types.InlineKeyboardButton("🌐 تغيير اللغة", callback_data=f"ucp_lang_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("📜 سجل مشترياته", callback_data=f"ucp_purchases_{uid}"),
        types.InlineKeyboardButton("🎫 تذاكره", callback_data=f"ucp_tickets_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("👥 قائمة إحالاته", callback_data=f"ucp_referrals_{uid}"),
        types.InlineKeyboardButton("📩 مراسلته مباشرة", callback_data=f"ucp_dm_{uid}")
    )
    m.add(
        types.InlineKeyboardButton("🔄 تحديث الملف", callback_data=f"ucp_refresh_{uid}"),
        types.InlineKeyboardButton("🗑️ حذف الحساب نهائياً", callback_data=f"ucp_delete_{uid}")
    )
    return m


def _show_profile(chat_id, uid, msg_id=None):
    u = get_user(uid)
    if not u:
        bot.send_message(chat_id, "❌ العضو غير موجود")
        return
    txt = _profile_text(u)
    kb = _profile_keyboard(uid)
    if msg_id:
        try:
            bot.edit_message_text(txt, chat_id, msg_id, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass
    bot.send_message(chat_id, txt, reply_markup=kb, parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text == "🧑‍💻 التحكم الشامل بالأعضاء")
def _open_user_control(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid):
        return
    msg = bot.send_message(message.chat.id, "🔍 أرسل آيدي العضو أو يوزره (بدون @):")
    bot.register_next_step_handler(msg, _search_and_show)


def _search_and_show(message):
    uid = str(message.from_user.id)
    if not _is_admin(uid):
        return
    q = message.text.strip()
    u = search_user(q)
    if not u:
        bot.send_message(message.chat.id, "❌ لم يتم العثور على العضو")
        return
    _show_profile(message.chat.id, str(u["uid"]))


@bot.callback_query_handler(func=lambda c: c.data.startswith("ucp_"))
def _ucp_callbacks(call):
    admin_uid = str(call.from_user.id)
    if not _is_admin(admin_uid):
        return bot.answer_callback_query(call.id, "❌ صلاحيات الإدارة فقط", show_alert=True)

    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    parts = data.split("_")
    action = parts[1]
    target = "_".join(parts[2:])

    if action == "refresh":
        return _show_profile(chat_id, target, msg_id)

    if action == "addpts":
        msg = bot.send_message(chat_id, f"💎 كم نقطة تريد إضافتها لـ {target}؟")
        bot.register_next_step_handler(msg, _apply_add_points, target)
        return

    if action == "subpts":
        msg = bot.send_message(chat_id, f"💎 كم نقطة تريد خصمها من {target}؟")
        bot.register_next_step_handler(msg, _apply_sub_points, target)
        return

    if action == "setpts":
        msg = bot.send_message(chat_id, f"✏️ أرسل الرصيد الجديد بدقة لـ {target}:")
        bot.register_next_step_handler(msg, _apply_set_points, target)
        return

    if action == "resetdaily":
        _set_field_raw(target, "last_claim", None)
        bot.answer_callback_query(call.id, "✅ يمكنه أخذ المكافأة اليومية فوراً الآن!", show_alert=True)
        return _show_profile(chat_id, target, msg_id)

    if action == "setstreak":
        msg = bot.send_message(chat_id, f"🔥 أرسل رقم السلسلة الجديد لـ {target}:")
        bot.register_next_step_handler(msg, _apply_set_streak, target)
        return

    if action == "rank":
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("🔹 عضو عادي (بدون رتبة)", callback_data=f"ucprank_reset_{target}"))
        for rk, info in RANKS.items():
            m.add(types.InlineKeyboardButton(info["name_ar"], callback_data=f"ucprank_{rk}_{target}"))
        bot.send_message(chat_id, "🏆 اختر الرتبة الجديدة:", reply_markup=m)
        return

    if action == "vipgrant":
        msg = bot.send_message(chat_id, f"👑 كم يوم تريد منحه VIP لـ {target}؟")
        bot.register_next_step_handler(msg, _apply_vip_grant, target)
        return

    if action == "vipremove":
        if _VIP_AVAILABLE:
            deactivate_vip(target)
            bot.answer_callback_query(call.id, "✅ تم سحب VIP", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ نظام VIP غير متاح حالياً", show_alert=True)
        return _show_profile(chat_id, target, msg_id)

    if action == "admintoggle":
        u = get_user(target) or {}
        new_val = not u.get("is_admin", False)
        update_user_data(target, is_admin=new_val)
        bot.answer_callback_query(call.id, "✅ تمت الترقية" if new_val else "✅ تمت الإزالة", show_alert=True)
        return _show_profile(chat_id, target, msg_id)

    if action == "notiftoggle":
        u = get_user(target) or {}
        new_val = not u.get("notifications_on", True)
        update_user_data(target, notifications_on=new_val)
        bot.answer_callback_query(call.id, "✅ تم التبديل", show_alert=True)
        return _show_profile(chat_id, target, msg_id)

    if action == "banperm":
        ban_user(target, permanent=True)
        bot.answer_callback_query(call.id, "⛔ تم الحظر الدائم", show_alert=True)
        return _show_profile(chat_id, target, msg_id)

    if action == "bantemp":
        ban_user(target, permanent=False, hours=24)
        bot.answer_callback_query(call.id, "⏱️ تم الحظر 24 ساعة", show_alert=True)
        return _show_profile(chat_id, target, msg_id)

    if action == "unban":
        unban_user(target)
        bot.answer_callback_query(call.id, "🟢 تم فك الحظر", show_alert=True)
        return _show_profile(chat_id, target, msg_id)

    if action == "lang":
        m = types.InlineKeyboardMarkup(row_width=2)
        m.add(
            types.InlineKeyboardButton("🇸🇦 عربي", callback_data=f"ucplang_ar_{target}"),
            types.InlineKeyboardButton("🇺🇸 EN", callback_data=f"ucplang_en_{target}")
        )
        m.add(
            types.InlineKeyboardButton("🇫🇷 FR", callback_data=f"ucplang_fr_{target}"),
            types.InlineKeyboardButton("🇪🇸 ES", callback_data=f"ucplang_es_{target}")
        )
        m.add(types.InlineKeyboardButton("🇻🇳 VI", callback_data=f"ucplang_vi_{target}"))
        bot.send_message(chat_id, "🌐 اختر اللغة الجديدة:", reply_markup=m)
        return

    if action == "purchases":
        sales = [s for s in bot_config.get("sales_log", []) if str(s.get("uid")) == str(target)]
        if not sales:
            bot.send_message(chat_id, "📭 لا توجد مشتريات مسجّلة")
            return
        txt = f"🛒 مشتريات {target}:\n\n"
        for s in sales[-15:]:
            txt += f"• {s.get('product', '?')} / {s.get('plan', '?')} — {s.get('price', '?')}💎 — {str(s.get('date', ''))[:16]}\n"
        bot.send_message(chat_id, txt, parse_mode="HTML")
        return

    if action == "tickets":
        tks = [(tid, tk) for tid, tk in bot_config.get("tickets", {}).items() if str(tk.get("uid")) == str(target)]
        if not tks:
            bot.send_message(chat_id, "📭 لا توجد تذاكر")
            return
        txt = f"🎫 تذاكر {target}:\n\n"
        for tid, tk in tks[-15:]:
            txt += f"• #{tid} — {tk.get('status', '?')} — {str(tk.get('text', ''))[:40]}\n"
        bot.send_message(chat_id, txt, parse_mode="HTML")
        return

    if action == "referrals":
        rows = []
        try:
            with engine.connect() as conn:
                rows = conn.execute(text("SELECT uid, username FROM users WHERE invited_by = :u"), {"u": str(target)}).fetchall()
        except Exception:
            rows = []
        if not rows:
            bot.send_message(chat_id, "📭 لم يدعُ أحداً بعد")
            return
        txt = f"👥 دعوات {target} ({len(rows)}):\n\n"
        for r in rows[:30]:
            txt += f"• {r[0]} — @{r[1] or 'N/A'}\n"
        bot.send_message(chat_id, txt, parse_mode="HTML")
        return

    if action == "dm":
        msg = bot.send_message(chat_id, f"📩 اكتب الرسالة التي تريد إرسالها لـ {target}:")
        bot.register_next_step_handler(msg, _apply_dm, target)
        return

    if action == "delete":
        m = types.InlineKeyboardMarkup(row_width=2)
        m.add(
            types.InlineKeyboardButton("✅ نعم، احذف نهائياً", callback_data=f"ucpdel_yes_{target}"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data=f"ucp_refresh_{target}")
        )
        bot.send_message(chat_id, f"⚠️ هل أنت متأكد من حذف الحساب {target} نهائياً؟ هذا الإجراء لا يمكن التراجع عنه!", reply_markup=m)
        return


@bot.callback_query_handler(func=lambda c: c.data.startswith("ucpdel_yes_"))
def _ucp_delete_confirm(call):
    admin_uid = str(call.from_user.id)
    if not _is_admin(admin_uid):
        return
    target = call.data.split("ucpdel_yes_")[1]
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM users WHERE uid = :u"), {"u": str(target)})
            conn.commit()
        bot.answer_callback_query(call.id, "🗑️ تم حذف الحساب نهائياً", show_alert=True)
        bot.edit_message_text(f"🗑️ تم حذف الحساب {target} نهائياً من قاعدة البيانات", call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ucprank_"))
def _ucp_rank_pick(call):
    admin_uid = str(call.from_user.id)
    if not _is_admin(admin_uid):
        return
    _, rest = call.data.split("ucprank_", 1)
    if rest.startswith("reset_"):
        target = rest.split("reset_")[1]
        update_user_data(target, rank="عضو عادي 🔹", rank_discount=0.0)
    else:
        rk, target = rest.split("_", 1)
        info = RANKS.get(rk)
        if info:
            update_user_data(target, rank=info["name_ar"], rank_discount=info["discount"])
    bot.answer_callback_query(call.id, "✅ تم تغيير الرتبة", show_alert=True)
    _show_profile(call.message.chat.id, target)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ucplang_"))
def _ucp_lang_pick(call):
    admin_uid = str(call.from_user.id)
    if not _is_admin(admin_uid):
        return
    _, rest = call.data.split("ucplang_", 1)
    lang, target = rest.split("_", 1)
    update_user_data(target, lang=lang, lang_selected=True)
    bot.answer_callback_query(call.id, "✅ تم تغيير اللغة", show_alert=True)
    _show_profile(call.message.chat.id, target)


def _apply_add_points(message, target):
    try:
        val = int(message.text.strip())
        update_user_data(target, points=val, accumulated_points=val)
        update_user_rank_and_quests(target)
        bot.send_message(message.chat.id, f"✅ أُضيف {val} 💎 لـ {target}")
        _show_profile(message.chat.id, target)
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")


def _apply_sub_points(message, target):
    try:
        val = int(message.text.strip())
        update_user_data(target, points=-val, accumulated_points=-val)
        bot.send_message(message.chat.id, f"✅ خُصم {val} 💎 من {target}")
        _show_profile(message.chat.id, target)
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")


def _apply_set_points(message, target):
    try:
        val = int(message.text.strip())
        _set_field_raw(target, "points", val)
        bot.send_message(message.chat.id, f"✅ الرصيد الآن {val} 💎")
        _show_profile(message.chat.id, target)
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")


def _apply_set_streak(message, target):
    try:
        val = int(message.text.strip())
        _set_field_raw(target, "streak_days", val)
        bot.send_message(message.chat.id, f"✅ السلسلة الآن {val} يوم")
        _show_profile(message.chat.id, target)
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")


def _apply_vip_grant(message, target):
    if not _VIP_AVAILABLE:
        bot.send_message(message.chat.id, "❌ نظام VIP غير متاح حالياً")
        return
    try:
        days = int(message.text.strip())
        activate_vip(target, days)
        bot.send_message(message.chat.id, f"✅ تم منح VIP لمدة {days} يوم")
        try:
            bot.send_message(int(target), f"🎉 تم منحك VIP لمدة {days} يوم من الإدارة!", parse_mode="HTML")
        except Exception:
            pass
        _show_profile(message.chat.id, target)
    except Exception:
        bot.send_message(message.chat.id, "❌ أرقام فقط")


def _apply_dm(message, target):
    try:
        bot.send_message(int(target), f"📩 ━━ رسالة من الإدارة ━━\n\n{message.text}", parse_mode="HTML")
        bot.send_message(message.chat.id, "✅ أُرسلت الرسالة بنجاح")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ فشل الإرسال: {e}")


print("=" * 55)
print("✅ bot7.py — لوحة التحكم الشاملة بالأعضاء جاهزة!")
print("=" * 55)
