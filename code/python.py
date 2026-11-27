__id__ = "hide_pinned_messages"
__name__ = "HidePins"
__description__ = "Скрывает панель закреплённых сообщений в чатах"
__author__ = "@itNotMax - @MaxExteraPlugins"
__version__ = "1.0.6"
__min_version__ = "12.10.6"
__icon__ = "MaxExteraPluginsStickers/2"

import json
from base_plugin import BasePlugin, HookResult, HookStrategy, MethodHook
from hook_utils import find_class, get_private_field
from client_utils import get_last_fragment
from android_utils import run_on_ui_thread
from ui.settings import Header, Divider, Custom, SimpleSettingFactory
from ui.bulletin import BulletinHelper
from java import dynamic_proxy, jclass

VIEW_GONE = 8


class L:
    _STRINGS = {
        "header_hide_pins": {
            "ru": "Скрыть закреплённые сообщения",
            "en": "Hide pinned messages",
        },
        "private_chats": {
            "ru": "Личные чаты",
            "en": "Private Chats",
        },
        "groups": {
            "ru": "Группы",
            "en": "Groups",
        },
        "channels": {
            "ru": "Каналы",
            "en": "Channels",
        },
        "state_on": {
            "ru": "Вкл",
            "en": "On",
        },
        "state_off": {
            "ru": "Выкл",
            "en": "Off",
        },
        "divider_hint": {
            "ru": "Нажмите на пункт, чтобы настроить исключения. Требуется перезаход в чат для применения.",
            "en": "Tap an item to configure exceptions. Re-entering the chat is required to apply.",
        },
        "exceptions_updated": {
            "ru": "Исключения обновлены",
            "en": "Exceptions updated",
        },
    }

    @staticmethod
    def is_ru() -> bool:
        try:
            from org.telegram.messenger import LocaleController
            lang = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            return lang in ("ru", "be", "uk", "kk")
        except Exception:
            return True

    @classmethod
    def g(cls, key: str) -> str:
        entry = cls._STRINGS.get(key, {})
        if cls.is_ru():
            return entry.get("ru", entry.get("en", key))
        return entry.get("en", key)

    @classmethod
    def exceptions_count(cls, n: int) -> str:
        if cls.is_ru():
            mod10 = n % 10
            mod100 = n % 100
            if mod10 == 1 and mod100 != 11:
                word = "исключение"
            elif 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
                word = "исключения"
            else:
                word = "исключений"
            return f"{n} {word}"
        word = "exception" if n == 1 else "exceptions"
        return f"{n} {word}"


def detect_chat_type(chat_activity):
    try:
        if get_private_field(chat_activity, "currentUser") is not None: return "private"

        current_chat = get_private_field(chat_activity, "currentChat")

        if current_chat is not None:
            if getattr(current_chat, "broadcast", False) and not getattr(current_chat, "megagroup", False):
                return "channel"
            return "group"
    except Exception:
        pass
    return "unknown"


def detect_peer_info(peer):
    if peer is None:
        return "unknown", None

    try:
        name = type(peer).__name__
        if "PeerUser" in name:
            uid = getattr(peer, "user_id", None)
            return "private", (int(uid) if uid else None)
        if "PeerChat" in name:
            cid = getattr(peer, "chat_id", None)
            return "group", (-int(cid) if cid else None)
        if "PeerChannel" in name:
            cid = getattr(peer, "channel_id", None)
            return "channel", (-int(cid) if cid else None)
    except Exception:
        pass

    return "unknown", None


def detect_dialog_type(dialog_id, controller=None):
    try:
        did = int(dialog_id)
        if did > 0:
            return "private"
        if did < 0 and controller is not None:
            from java.lang import Long as JLong
            mc = controller.getMessagesController()
            if mc is not None:
                chat = mc.getChat(JLong(-did))
                if chat is not None:
                    if getattr(chat, "broadcast", False) and not getattr(chat, "megagroup", False):
                        return "channel"
                    return "group"
    except Exception:
        pass
    return "unknown"


class PinnedViewHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            activity = param.thisObject
            if activity is None:
                return
            chat_type = detect_chat_type(activity)
            dialog_id = None
            try:
                dialog_id = int(activity.getDialogId())
            except Exception:
                pass
            if not self.plugin.should_hide(chat_type, dialog_id):
                return
            for name in ["pinnedMessageView", "pinnedMessageContainer", "topChatPanelView"]:
                v = get_private_field(activity, name)
                if v is not None:
                    try:
                        v.setVisibility(VIEW_GONE)
                    except Exception:
                        pass
                    return
        except Exception:
            pass


class LoadPinnedHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        try:
            args = param.args
            if args is None or len(args) == 0:
                return
            dialog_id = int(args[0])
            chat_type = detect_dialog_type(dialog_id, param.thisObject)
            if chat_type == "unknown":
                if (self.plugin.get_setting("hide_private", True)
                        and self.plugin.get_setting("hide_groups", True)
                        and self.plugin.get_setting("hide_channels", True)
                        and not self.plugin._has_any_exceptions()):
                    if len(args) == 3:
                        param.setResult(None)
                return
            if self.plugin.should_hide(chat_type, dialog_id):
                if len(args) == 3:
                    param.setResult(None)
                else:
                    from java.util import ArrayList
                    param.setResult(ArrayList())
        except Exception:
            pass



# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================

# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================

# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================
class AuthorChannelHelper:
    CONFIG_URL = "https://raw.githubusercontent.com/MaxExteraPlugins/config/main/links.json"

    DEFAULT_LINKS = {
        "channel_username": "MaxExteraPlugins",
        "channel_url": "https://t.me/MaxExteraPlugins",
        "header": {"ru": "MaxExteraPlugins", "en": "MaxExteraPlugins"},
        "buttons": [
            {"title": {"ru": "Канал автора", "en": "Author's Channel"}, "icon": "msg_channel", "url": "https://t.me/MaxExteraPlugins"},
            {"title": {"ru": "Поддержать автора", "en": "Support author"}, "icon": "msg_share", "url": "https://t.me/itNotMax"},
            {"title": {"ru": "Сообщить о баге", "en": "Report a bug"}, "icon": "msg_help", "url": "https://t.me/itNotMax"}
        ]
    }

    _TEXTS = {
        "install_card_title": {"ru": "Подпишитесь на канал", "en": "Subscribe to channel"},
        "install_card_msg": {
            "ru": (
                "Мы делаем плагины бесплатными и доступными для всех: пожалуйста, "
                "поддержите нас подпиской на официальный канал @MaxExteraPlugins.\n\n"
                "Там публикуются обновления, важные новости и анонсы новых плагинов."
            ),
            "en": (
                "We keep our plugins free and accessible for everyone: please "
                "support us by subscribing to our official channel @MaxExteraPlugins.\n\n"
                "Updates, news, and new plugin announcements are published there."
            )
        },
        "open_channel_btn": {"ru": "Перейти на канал", "en": "Open channel"},
        "remind_later_btn": {"ru": "Напомнить позже", "en": "Remind later"},
        "never_show_btn": {"ru": "Больше не показывать", "en": "Don't show again"},
        "sub_thank_you": {"ru": "Спасибо за подписку на наш канал!", "en": "Thank you for subscribing to our channel!"},
        "settings_channel": {"ru": "Канал автора", "en": "Author's Channel"},
        "settings_donate": {"ru": "Поддержать автора", "en": "Support author"},
        "settings_bug_report": {"ru": "Сообщить о баге", "en": "Report a bug"}
    }

    @classmethod
    def is_ru(cls) -> bool:
        try:
            from org.telegram.messenger import LocaleController
            lang = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            return lang in ("ru", "be", "uk", "kk")
        except Exception:
            return True

    @classmethod
    def tr(cls, key: str) -> str:
        entry = cls._TEXTS.get(key, {})
        return entry.get("ru" if cls.is_ru() else "en", entry.get("en", key))

    def __init__(self, plugin, icon_sticker=None):
        self.plugin = plugin
        self.icon_sticker = icon_sticker or getattr(plugin, "__icon__", "MaxExteraPluginsStickers/1")
        self._stopped = False
        self._active_dialog = None

    def on_load(self):
        self._stopped = False
        self._active_dialog = None
        self._load_remote_links_async()
        self._check_initial_subscription_flow()

    def on_event(self, event_type):
        try:
            name = str(event_type).upper()
            if name.endswith("START") or name.endswith("RESUME"):
                if self.is_subscribed() and not self.plugin.get_setting("was_subscribed", False):
                    self.plugin.set_setting("was_subscribed", True)
                    self._dismiss_active_dialog()
                    self._notify_subscribed()
        except Exception:
            pass

    def on_unload(self):
        self._stopped = True
        self._dismiss_active_dialog()

    def is_allowed(self) -> bool:
        return True

    def _get_links(self) -> dict:
        raw = self.plugin.get_setting("remote_links_cache", None)
        if raw:
            try:
                import json
                data = json.loads(raw)
                if isinstance(data, dict): return data
            except Exception:
                pass
        return self.DEFAULT_LINKS

    def _load_remote_links_async(self):
        def worker():
            try:
                import urllib.request, json
                req = urllib.request.Request(self.CONFIG_URL, headers={"User-Agent": "MaxExteraPlugins"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, dict):
                            self.plugin.set_setting("remote_links_cache", json.dumps(data))
                            self._resolve_channel_in_telegram(data.get("channel_username", "MaxExteraPlugins"))
            except Exception:
                pass
        import threading
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _open_url(self, url: str, view=None):
        try:
            from org.telegram.messenger.browser import Browser
            from org.telegram.messenger import ApplicationLoader
            from client_utils import get_last_fragment
            ctx = None
            if view is not None:
                ctx = view.getContext()
            if ctx is None:
                frag = get_last_fragment()
                if frag is not None:
                    ctx = frag.getParentActivity()
            if ctx is None:
                ctx = ApplicationLoader.applicationContext
            Browser.openUrl(ctx, url)
        except Exception:
            pass

    def _resolve_channel_in_telegram(self, username: str):
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            from org.telegram.tgnet import TLRPC, ConnectionsManager, RequestDelegate
            clean_user = username.lstrip("@")
            acc = int(UserConfig.selectedAccount)
            mc = MessagesController.getInstance(acc)
            if not mc: return
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = clean_user
            helper_ref = self
            class Delegate(RequestDelegate):
                def run(self, response, error):
                    if error is None and response is not None:
                        chats = getattr(response, "chats", None)
                        if chats is not None and chats.size() > 0:
                            for a in range(UserConfig.MAX_ACCOUNT_COUNT):
                                try:
                                    if UserConfig.getInstance(a).isClientActivated():
                                        MessagesController.getInstance(a).putChats(chats, False)
                                except Exception:
                                    pass
                            c = chats.get(0)
                            cid = getattr(c, "id", 0)
                            if cid > 0:
                                helper_ref.plugin.set_setting("resolved_channel_id", int(cid))
            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController, MessagesStorage
            from java.lang import Long as JLong
            links = self._get_links()
            target = str(links.get("channel_username", "MaxExteraPlugins") or "MaxExteraPlugins").lower().lstrip("@")
            saved_cid = int(self.plugin.get_setting("resolved_channel_id", 0) or 0)

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                try:
                    uconf = UserConfig.getInstance(acc)
                    if not uconf.isClientActivated():
                        continue

                    mc = MessagesController.getInstance(acc)
                    storage = MessagesStorage.getInstance(acc)

                    # 1. In-memory check by resolved_channel_id
                    if saved_cid and mc is not None:
                        try:
                            c = mc.getChat(JLong(saved_cid))
                            if c is not None:
                                left = bool(getattr(c, "left", True))
                                kicked = bool(getattr(c, "kicked", False))
                                if not left and not kicked:
                                    return True
                        except Exception:
                            pass

                    # 2. In-memory check by username
                    if mc is not None:
                        try:
                            chat = mc.getUserOrChat(target)
                            if chat is not None:
                                cid = int(getattr(chat, "id", 0) or 0)
                                if cid and not saved_cid:
                                    saved_cid = cid
                                    self.plugin.set_setting("resolved_channel_id", cid)
                                left = bool(getattr(chat, "left", True))
                                kicked = bool(getattr(chat, "kicked", False))
                                if not left and not kicked:
                                    return True
                        except Exception:
                            pass

                    # 3. In-memory dialogs check
                    if mc is not None:
                        try:
                            dialog_lists = []
                            d_chan = getattr(mc, "dialogsChannelsOnly", None)
                            if d_chan is not None and d_chan.size() > 0:
                                dialog_lists.append(d_chan)
                            d_all = getattr(mc, "allDialogs", None)
                            if d_all is not None and d_all.size() > 0:
                                dialog_lists.append(d_all)

                            for d_list in dialog_lists:
                                limit = min(d_list.size(), 300)
                                for i in range(limit):
                                    d = d_list.get(i)
                                    did = getattr(d, "id", 0)
                                    if did < 0:
                                        cid = -did
                                        if saved_cid and cid == saved_cid:
                                            c = mc.getChat(JLong(cid))
                                            if c is not None:
                                                left = bool(getattr(c, "left", True))
                                                kicked = bool(getattr(c, "kicked", False))
                                                if not left and not kicked:
                                                    return True
                                        else:
                                            c = mc.getChat(JLong(cid))
                                            if c is not None:
                                                uname = str(getattr(c, "username", "") or "").lower()
                                                if uname == target:
                                                    if not saved_cid:
                                                        saved_cid = cid
                                                        self.plugin.set_setting("resolved_channel_id", cid)
                                                    left = bool(getattr(c, "left", True))
                                                    kicked = bool(getattr(c, "kicked", False))
                                                    if not left and not kicked:
                                                        return True
                        except Exception:
                            pass

                    # 4. Storage check (SQLite on disk)
                    if storage is not None:
                        if saved_cid:
                            try:
                                if storage.containsLocalDialog(JLong(-saved_cid)):
                                    c_sync = storage.getChatSync(JLong(saved_cid))
                                    if c_sync is not None:
                                        left = bool(getattr(c_sync, "left", True))
                                        kicked = bool(getattr(c_sync, "kicked", False))
                                        if not left and not kicked:
                                            return True
                                    else:
                                        return True
                            except Exception:
                                pass

                        try:
                            db = storage.getDatabase()
                            if db is not None:
                                if saved_cid:
                                    try:
                                        cur = db.queryFinalized("SELECT did FROM dialogs WHERE did = ?", [JLong(-saved_cid)])
                                        if cur is not None:
                                            has_row = bool(cur.next())
                                            cur.dispose()
                                            if has_row:
                                                return True
                                    except Exception:
                                        pass

                                try:
                                    cur = db.queryFinalized("SELECT uid, name FROM chats WHERE LOWER(name) LIKE ?", ["%" + target + "%"])
                                    if cur is not None:
                                        while cur.next():
                                            c_id = cur.longValue(0)
                                            if c_id > 0:
                                                if not saved_cid:
                                                    saved_cid = int(c_id)
                                                    self.plugin.set_setting("resolved_channel_id", saved_cid)
                                                cur_d = db.queryFinalized("SELECT did FROM dialogs WHERE did = ?", [JLong(-c_id)])
                                                if cur_d is not None:
                                                    in_dlg = bool(cur_d.next())
                                                    cur_d.dispose()
                                                    if in_dlg:
                                                        cur.dispose()
                                                        return True
                                        cur.dispose()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def prepend_settings(self, original_items=None) -> list:
        from ui.settings import Header, Text, Divider

        if original_items and any(getattr(x, "text", "") == "MaxExteraPlugins" for x in original_items if type(x).__name__ == "Header"):
            return original_items

        links = self._get_links()
        buttons_config = links.get("buttons")

        author_items = []
        if isinstance(buttons_config, list):
            for btn in buttons_config:
                if not isinstance(btn, dict): continue
                raw_url = btn.get("url")
                if isinstance(raw_url, dict):
                    keys = [
                        getattr(self.plugin, "id", None),
                        globals().get("__id__", None),
                        globals().get("__name__", None),
                        self.plugin.__class__.__name__
                    ]
                    keys += [k.lower() for k in keys if isinstance(k, str)]
                    resolved_url = ""
                    for k in keys:
                        if k and k in raw_url:
                            resolved_url = str(raw_url[k] or "").strip()
                            if resolved_url:
                                break
                    url = resolved_url
                elif isinstance(raw_url, str):
                    url = raw_url.strip()
                else:
                    url = ""

                if not url: continue

                title_data = btn.get("title")
                if isinstance(title_data, dict):
                    title = title_data.get("ru" if self.is_ru() else "en") or title_data.get("en") or title_data.get("ru") or ""
                elif isinstance(title_data, str) and title_data:
                    title = title_data
                else:
                    title = btn.get("title_ru" if self.is_ru() else "title_en") or btn.get("title_ru") or btn.get("title_en") or ""

                if not title: continue
                icon = str(btn.get("icon") or "msg_channel").strip()

                def make_click(u):
                    return lambda v=None: self._open_url(u, v)

                author_items.append(Text(text=title, icon=icon, on_click=make_click(url)))
        else:
            for k, text_key, icon_name in [
                ("channel_url", "settings_channel", "msg_channel"),
                ("donate_url", "settings_donate", "msg_share"),
                ("bug_report_url", "settings_bug_report", "msg_help")
            ]:
                u = str(links.get(k) or "").strip()
                if u:
                    author_items.append(Text(text=self.tr(text_key), icon=icon_name, on_click=lambda v=None, target_u=u: self._open_url(target_u, v)))

        res = []
        if author_items:
            hdr = links.get("header") or "MaxExteraPlugins"
            if isinstance(hdr, dict):
                hdr_text = hdr.get("ru" if self.is_ru() else "en") or hdr.get("ru") or hdr.get("en") or "MaxExteraPlugins"
            else:
                hdr_text = str(hdr)
            res.append(Header(text=hdr_text))
            res.extend(author_items)
            res.append(Divider())

        cleaned_items = []
        if original_items:
            skipping_info = False
            for item in original_items:
                item_cls = type(item).__name__
                if item_cls == "Header":
                    txt = str(getattr(item, "text", "") or getattr(item, "title", "") or "").lower()
                    if "информ" in txt or "inform" in txt:
                        skipping_info = True
                        continue
                    else:
                        skipping_info = False
                elif skipping_info and item_cls == "Divider":
                    skipping_info = False
                    continue

                if not skipping_info:
                    cleaned_items.append(item)

        res.extend(cleaned_items)
        return res

    def _dismiss_active_dialog(self):
        try:
            if self._active_dialog is not None:
                self._active_dialog.dismiss()
        except Exception:
            pass
        self._active_dialog = None

    def _is_dialog_active(self) -> bool:
        try:
            if self._active_dialog is not None:
                return bool(self._active_dialog.isShowing())
        except Exception:
            pass
        return False

    def _notify_subscribed(self):
        try:
            from ui.bulletin import BulletinHelper
            BulletinHelper.show_success(self.tr("sub_thank_you"))
        except Exception:
            pass

    def _check_initial_subscription_flow(self):
        def flow():
            try:
                if self.plugin.get_setting("never_show_sub_prompt", False):
                    return

                current_ver = str(getattr(self.plugin, "__version__", globals().get("__version__", "1.0.0")) or "1.0.0")
                last_prompted_ver = self.plugin.get_setting("last_prompted_version", None)

                # Only show on install (last_prompted_ver is None) or update (last_prompted_ver != current_ver)
                if last_prompted_ver is not None and str(last_prompted_ver) == current_ver:
                    return

                if self.is_subscribed():
                    self.plugin.set_setting("last_prompted_version", current_ver)
                    self.plugin.set_setting("was_subscribed", True)
                    return

                self._show_subscription_prompt(current_ver)
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(flow, 1500)

    def _create_card_content(self, act, title_text, message_text):
        try:
            from android.widget import LinearLayout, TextView, ImageView
            from android.view import Gravity
            from org.telegram.messenger import AndroidUtilities
            from org.telegram.ui.ActionBar import Theme
            from client_utils import create_sticker_drawable

            dp = AndroidUtilities.dp

            layout = LinearLayout(act)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setGravity(Gravity.CENTER_HORIZONTAL)
            layout.setPadding(dp(24), dp(20), dp(24), dp(10))

            sticker_drawable = None
            if self.icon_sticker:
                try:
                    sticker_drawable = create_sticker_drawable(self.icon_sticker, dp(120), dp(120))
                except Exception:
                    pass

            if sticker_drawable is not None:
                iv = ImageView(act)
                iv.setImageDrawable(sticker_drawable)
                lp_iv = LinearLayout.LayoutParams(dp(120), dp(120))
                lp_iv.gravity = Gravity.CENTER_HORIZONTAL
                lp_iv.bottomMargin = dp(14)
                layout.addView(iv, lp_iv)

            if title_text:
                tt = TextView(act)
                tt.setText(title_text)
                tt.setTextSize(19.0)
                tt.setTypeface(AndroidUtilities.bold())
                tt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                tt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_t = LinearLayout.LayoutParams(-1, -2)
                lp_t.bottomMargin = dp(8)
                layout.addView(tt, lp_t)

            if message_text:
                mt = TextView(act)
                mt.setText(message_text)
                mt.setTextSize(15.0)
                mt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                mt.setLineSpacing(float(dp(3)), 1.0)
                mt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_m = LinearLayout.LayoutParams(-1, -2)
                mt.setLayoutParams(lp_m)
                layout.addView(mt)

            return layout
        except Exception:
            return None

    def _show_subscription_prompt(self, current_ver: str):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("install_card_title"), self.tr("install_card_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("install_card_title"))
                    b.set_message(self.tr("install_card_msg"))

                def on_open_channel(dialog, which):
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_prompted_version", current_ver)
                    self._open_url(url)

                def on_remind_later(dialog, which):
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_prompted_version", current_ver)

                def on_never_show(dialog, which):
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("never_show_sub_prompt", True)
                    self.plugin.set_setting("last_prompted_version", current_ver)

                b.set_positive_button(self.tr("open_channel_btn"), on_open_channel)
                b.set_neutral_button(self.tr("remind_later_btn"), on_remind_later)
                b.set_negative_button(self.tr("never_show_btn"), on_never_show)

                def on_dismiss(builder):
                    self.plugin.set_setting("last_prompted_version", current_ver)
                try:
                    b.set_on_dismiss_listener(on_dismiss)
                except Exception:
                    pass

                self._active_dialog = b.show()
                self.plugin.set_setting("last_prompted_version", current_ver)
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)

class Plugin(BasePlugin):

    _CATEGORY_META = {
        "private": ("hide_private", "private_chats", "msg_openprofile"),
        "group": ("hide_groups", "groups", "msg_groups"),
        "channel": ("hide_channels", "channels", "msg_channel"),
    }

    def on_app_event(self, event_type):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_event(event_type)

    def _get_exceptions(self, chat_type):
        if chat_type not in self._CATEGORY_META:
            return set()
        cache = getattr(self, "_exceptions_cache", None)
        if cache is None:
            self._exceptions_cache = {}
            cache = self._exceptions_cache
        if chat_type not in cache:
            raw = self.get_setting(f"exceptions_{chat_type}", "[]")
            try:
                data = json.loads(raw) if raw else []
                cache[chat_type] = set(int(x) for x in data)
            except Exception:
                cache[chat_type] = set()
        return cache[chat_type]

    def _save_exceptions(self, chat_type, ids_set):
        if not hasattr(self, "_exceptions_cache"):
            self._exceptions_cache = {}
        cleaned = set(int(x) for x in ids_set if x)
        self._exceptions_cache[chat_type] = cleaned
        self.set_setting(f"exceptions_{chat_type}", json.dumps(sorted(cleaned)))

    def _has_any_exceptions(self):
        return any(len(self._get_exceptions(c)) > 0 for c in self._CATEGORY_META)

    def should_hide(self, chat_type, dialog_id=None):
        meta = self._CATEGORY_META.get(chat_type)
        if meta is None:
            return True
        setting_key = meta[0]
        base = bool(self.get_setting(setting_key, True))
        if dialog_id is not None:
            try:
                did = int(dialog_id)
                if did in self._get_exceptions(chat_type):
                    return not base
            except Exception:
                pass
        return base

    def on_plugin_load(self):
        self._exceptions_cache = {}
        self._touch_x = {}
        self._notif_factory = None
        self._author_helper = AuthorChannelHelper(self, icon_sticker="MaxExteraPluginsStickers/2")
        self._author_helper.on_load()
        try:
            self.add_hook("TL_updatePinnedMessages")
            self.add_hook("TL_updatePinnedChannelMessages")
        except Exception:
            pass

        try:
            cls = find_class("org.telegram.ui.ChatActivity")
            if cls is not None:
                self.hook_all_methods(cls, "updatePinnedMessageView", PinnedViewHook(self))
        except Exception:
            pass

        try:
            cls2 = find_class("org.telegram.messenger.MediaDataController")
            if cls2 is not None:
                self.hook_all_methods(cls2, "loadPinnedMessages", LoadPinnedHook(self))
        except Exception:
            pass

    def on_plugin_unload(self):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_unload()
        factory = getattr(self, "_notif_factory", None)
        if factory is not None:
            try:
                factory.release()
            except Exception:
                pass
            self._notif_factory = None

    def on_update_hook(self, update_name, account, update):
        try:
            if update_name in ("TL_updatePinnedMessages", "TL_updatePinnedChannelMessages"):
                peer = getattr(update, "peer", None)
                chat_type, dialog_id = detect_peer_info(peer)
                if self.should_hide(chat_type, dialog_id):
                    return HookResult(strategy=HookStrategy.CANCEL)
        except Exception:
            pass
        return HookResult()

    def _format_subtext(self, chat_type, enabled):
        state = L.g("state_on") if enabled else L.g("state_off")
        count = len(self._get_exceptions(chat_type))
        if count > 0:
            return f"{state}, {L.exceptions_count(count)}"
        return state

    def _get_notif_factory(self):
        factory = getattr(self, "_notif_factory", None)
        if factory is not None:
            return factory

        plugin = self
        if not hasattr(self, "_touch_x"):
            self._touch_x = {}

        from android.view import View, MotionEvent
        from java.lang import System
        from org.telegram.messenger import R as TgR
        from org.telegram.ui.Cells import NotificationsCheckCell

        class TouchTracker(dynamic_proxy(View.OnTouchListener)):
            def onTouch(t_self, v, event):
                try:
                    action = event.getActionMasked()
                    if action == MotionEvent.ACTION_DOWN or action == MotionEvent.ACTION_UP:
                        plugin._touch_x[System.identityHashCode(v)] = float(event.getX())
                except Exception:
                    pass
                return False

        def create_view(context, list_view, current_account, class_guid, resources_provider):
            cell = NotificationsCheckCell(context, 21, 70, True, resources_provider)
            cell.setOnTouchListener(TouchTracker())
            return cell

        def bind_view(view, item, divider, adapter, list_view):
            try:
                cat = str(item.object) if item.object is not None else "private"
                meta = plugin._CATEGORY_META.get(cat, plugin._CATEGORY_META["private"])
                setting_key, label_key, icon_name = meta
                checked = bool(plugin.get_setting(setting_key, True))
                icon_res = getattr(TgR.drawable, icon_name, 0)
                subtext = plugin._format_subtext(cat, checked)
                view.setAnimationsEnabled(False)
                view.setTextAndValueAndIconAndCheck(
                    L.g(label_key),
                    subtext,
                    icon_res,
                    checked,
                    0,
                    False,
                    bool(divider),
                    False,
                )
                view.setAnimationsEnabled(True)
            except Exception:
                pass

        def on_factory_click(plugin_java, item, view):
            try:
                cat = str(item.object) if item is not None and item.object is not None else "private"
                plugin._on_category_click(cat, view)
            except Exception:
                pass

        self._notif_factory = SimpleSettingFactory(
            create_view,
            bind_view,
            is_clickable=True,
            is_shadow=False,
            on_click=on_factory_click,
        )
        return self._notif_factory

    def _on_category_click(self, chat_type, view=None):
        meta = self._CATEGORY_META.get(chat_type)
        if meta is None:
            return
        setting_key = meta[0]

        tapped_switch = False
        if view is not None:
            try:
                from java.lang import System
                from org.telegram.messenger import AndroidUtilities, LocaleController
                x = getattr(self, "_touch_x", {}).get(System.identityHashCode(view), None)
                w = view.getMeasuredWidth()
                if x is not None and w > 0:
                    dp76 = AndroidUtilities.dp(76)
                    is_rtl = bool(LocaleController.isRTL)
                    if (is_rtl and x <= dp76) or (not is_rtl and x >= w - dp76):
                        tapped_switch = True
            except Exception:
                pass

        if tapped_switch:
            new_val = not bool(self.get_setting(setting_key, True))
            self.set_setting(setting_key, new_val)
            try:
                view.setChecked(new_val)
                view.setValue(self._format_subtext(chat_type, new_val))
            except Exception:
                pass
        else:
            self._open_exceptions_picker(chat_type, view)

    def _open_exceptions_picker(self, chat_type, cell_view=None):
        plugin = self

        def _ui():
            try:
                frag = get_last_fragment()
                if frag is None:
                    return

                USA = jclass("org.telegram.ui.UsersSelectActivity")
                DelCls = jclass("org.telegram.ui.UsersSelectActivity$FilterUsersActivityDelegate")
                from java.util import ArrayList
                from java.lang import Long as JLong

                preselected = ArrayList()
                for did in sorted(plugin._get_exceptions(chat_type)):
                    preselected.add(JLong(int(did)))

                act = USA(False, preselected, 0)
                if chat_type == "private":
                    try:
                        act.asPrivateChats()
                    except Exception:
                        pass
                try:
                    act.noChatTypes = True
                except Exception:
                    pass
                try:
                    act.doNotNewChats = True
                except Exception:
                    pass

                class PickerDelegate(dynamic_proxy(DelCls)):
                    def didSelectChats(s_self, dids, flags):
                        try:
                            new_ids = set()
                            if dids is not None:
                                for i in range(dids.size()):
                                    try:
                                        did = int(dids.get(i))
                                        if did != 0:
                                            new_ids.add(did)
                                    except Exception:
                                        pass
                            def apply_saved():
                                plugin._save_exceptions(chat_type, new_ids)
                                if cell_view is not None:
                                    try:
                                        setting_key = plugin._CATEGORY_META[chat_type][0]
                                        checked = bool(plugin.get_setting(setting_key, True))
                                        cell_view.setValue(plugin._format_subtext(chat_type, checked))
                                    except Exception:
                                        pass
                                BulletinHelper.show_info(L.g("exceptions_updated"))
                            run_on_ui_thread(apply_saved)
                        except Exception:
                            pass

                act.setDelegate(PickerDelegate())
                frag.presentFragment(act)
            except Exception:
                pass

        run_on_ui_thread(_ui)

    def create_settings(self):
        try:
            items = self._inner_create_settings()
        except Exception:
            items = []
        if hasattr(self, '_author_helper'):
            return self._author_helper.prepend_settings(items)
        return items

    def _inner_create_settings(self):
        factory = self._get_notif_factory()
        return [
            Header(text=L.g("header_hide_pins")),
            Custom(
                factory=factory.instance.java,
                factory_args="private",
            ),
            Custom(
                factory=factory.instance.java,
                factory_args="group",
            ),
            Custom(
                factory=factory.instance.java,
                factory_args="channel",
            ),
            Divider(
                text=L.g("divider_hint"),
            ),
        ]
