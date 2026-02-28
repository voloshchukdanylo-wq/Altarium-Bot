import json
import os
import random
import time
import asyncio
from threading import Thread

import discord
from discord import ButtonStyle, Embed, Interaction, SelectOption
from discord.ext import commands, tasks
from discord.ui import Button, Modal, Select, TextInput, View
from flask import Flask

# ================== CONFIG ==================
ALLOWED_GUILD = 1029776124915490928
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

BALANCES_FILE = os.path.join(DATA_DIR, "balances.json")
ROLE_INCOME_FILE = os.path.join(DATA_DIR, "role_income.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
POPULATION_FILE = os.path.join(DATA_DIR, "population.json")
COUNTRY_STATS_FILE = os.path.join(DATA_DIR, "country_stats.json")
PLAYER_STATS_FILE = os.path.join(DATA_DIR, "player_stats.json")
COUNTRY_OWNERS_FILE = os.path.join(DATA_DIR, "country_owners.json")
WIPE_BACKUP_FILE = os.path.join(DATA_DIR, "wipe_backup.json")
PASSIVE_FLOW_FILE = os.path.join(DATA_DIR, "passive_flows.json")
COMMAND_ACCESS_FILE = os.path.join(DATA_DIR, "command_access.json")
SEASONS_FILE = os.path.join(DATA_DIR, "seasons.json")
SPHERE_REQUESTS_FILE = os.path.join(DATA_DIR, "sphere_requests.json")
TICKETS_FILE = os.path.join(DATA_DIR, "tickets.json")
REG_SETTINGS_FILE = os.path.join(DATA_DIR, "reg_settings.json")
PLAYER_STATE_FILE = os.path.join(DATA_DIR, "player_state.json")
INVESTMENTS_FILE = os.path.join(DATA_DIR, "investments.json")
MODERATION_FILE = os.path.join(DATA_DIR, "moderation.json")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.json")
WIPE_BACKUP_TTL = 3600

# ================== KEEP ALIVE ==================
app = Flask(__name__)


@app.route("/")
def home():
    return "Бот онлайн!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    Thread(target=run, daemon=True).start()


# ================== JSON ==================
def load_json(path: str, default):
    if not os.path.exists(path):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
        return default.copy() if isinstance(default, dict) else default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
        return default.copy() if isinstance(default, dict) else default


def save_json(path: str, data):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ================== GLOBAL STATE ==================
balances = load_json(BALANCES_FILE, {"валюта": "💲"})
currency = balances.get("валюта", "💲")
role_income = load_json(ROLE_INCOME_FILE, {"roles": {}, "last_claim": {}})
settings = load_json(
    SETTINGS_FILE,
    {
        "autocollect_channel": None,
        "happiness_tick_seconds": 43200,
        "invite_channel": None,
        "robbery_safe_role_id": None,
        "transfer_role_id": None,
        "sell_role_id": None,
        "economy_log_channel": None,
        "news_channel": None,
        "coin_currency": "Alta-коин",
        "status_text": None,
        "status_emoji": None,
        "status_until": None,
    },
)
items_data = load_json(
    ITEMS_FILE,
    {
        "categories": {"1": "Гражданские", "2": "Военные", "3": "Опциональные"},
        "category_emojis": {"1": "🏢", "2": "⚔️", "3": "🗝️"},
        "items": {},
    },
)
inventory = load_json(INVENTORY_FILE, {})
country_stats = load_json(COUNTRY_STATS_FILE, {})
country_owners = load_json(COUNTRY_OWNERS_FILE, {"country_to_user": {}, "user_to_country": {}})
passive_flows = load_json(PASSIVE_FLOW_FILE, {"users": {}})
command_access = load_json(COMMAND_ACCESS_FILE, {"commands": {}})
seasons_data = load_json(SEASONS_FILE, {"seasons": {}, "active_season": None, "spheres": {}, "user_progress": {}})
sphere_requests = load_json(
    SPHERE_REQUESTS_FILE,
    {"requests": {}, "next_id": 1, "channel_id": None, "curator_role_id": None, "result_channel_id": None},
)
tickets_data = load_json(TICKETS_FILE, {"forms": {}, "next_id": 1, "access_roles": {}, "panel_channel": None})
reg_settings = load_json(REG_SETTINGS_FILE, {"roles": [], "roles_add": [], "roles_remove": [], "wipe_roles": []})
player_state = load_json(PLAYER_STATE_FILE, {"users": {}})
investments = load_json(INVESTMENTS_FILE, {"users": {}})
moderation_data = load_json(MODERATION_FILE, {"log_channel": None, "warns": {}, "warn_limit": {"count": 3, "action": "мут 1ч"}})
ratings_data = load_json(RATINGS_FILE, {"channel_id": None, "targets": [], "last_vote": {}, "votes": {}})

role_income.setdefault("freeze_roles", {})
role_income.setdefault("freeze_last_claim", {})
settings.setdefault("autocollect_channel", None)
settings.setdefault("happiness_tick_seconds", 43200)
settings.setdefault("invite_channel", None)
settings.setdefault("robbery_safe_role_id", None)
settings.setdefault("transfer_role_id", None)
settings.setdefault("sell_role_id", None)
settings.setdefault("economy_log_channel", None)
settings.setdefault("news_channel", None)
settings.setdefault("coin_currency", "Alta-коин")
settings.setdefault("status_text", None)
settings.setdefault("status_emoji", None)
settings.setdefault("status_until", None)
moderation_data.setdefault("log_channel", None)
moderation_data.setdefault("warns", {})
moderation_data.setdefault("warn_limit", {"count": 3, "action": "мут 1ч"})
moderation_data["warn_limit"].setdefault("count", 3)
moderation_data["warn_limit"].setdefault("action", "мут 1ч")
ratings_data.setdefault("channel_id", None)
ratings_data.setdefault("targets", [])
ratings_data.setdefault("last_vote", {})
ratings_data.setdefault("votes", {})
country_owners.setdefault("country_to_user", {})
country_owners.setdefault("user_to_country", {})
sphere_requests.setdefault("result_channel_id", None)
reg_settings.setdefault("roles_add", reg_settings.get("roles", []))
reg_settings.setdefault("roles_remove", [])
reg_settings.setdefault("wipe_roles", [])

items_data.setdefault("categories", {}).setdefault("1", "Гражданские")
items_data.setdefault("categories", {}).setdefault("2", "Военные")
items_data.setdefault("categories", {}).setdefault("3", "Опциональные")
items_data.setdefault("category_emojis", {}).setdefault("1", "🏢")
items_data.setdefault("category_emojis", {}).setdefault("2", "⚔️")
items_data.setdefault("category_emojis", {}).setdefault("3", "🗝️")


# ================== HELPERS ==================
def ensure_user(user_id: str):
    if user_id not in balances or not isinstance(balances[user_id], dict):
        balances[user_id] = {"наличка": 0, "банк": 0, "заморожено": 0, "коины": 0}
        save_json(BALANCES_FILE, balances)
    else:
        balances[user_id].setdefault("заморожено", 0)
        balances[user_id].setdefault("коины", 0)
    return balances[user_id]


def add_balance(user_id: str, amount: int):
    user = ensure_user(user_id)
    user["наличка"] += amount
    save_json(BALANCES_FILE, balances)


def save_items():
    save_json(ITEMS_FILE, items_data)


def save_inventory():
    save_json(INVENTORY_FILE, inventory)


def parse_role_mentions(raw: str):
    if raw.lower() == "скип":
        return []
    role_ids = []
    for token in raw.split():
        token = token.replace("<@&", "").replace(">", "")
        role_ids.append(int(token))
    return role_ids


def format_interval(seconds: int) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}д")
    if hours:
        parts.append(f"{hours}ч")
    if minutes:
        parts.append(f"{minutes}м")
    if secs or not parts:
        parts.append(f"{secs}с")
    return " ".join(parts)


def fmt_num(value: int | float) -> str:
    try:
        num = int(value)
    except Exception:
        num = 0
    return f"{num:,}".replace(",", ".")


def fmt_money(value: int | float) -> str:
    return f"{fmt_num(value)} {currency}"


async def log_economy_change(
    guild: discord.Guild | None,
    member_id: int | str,
    reason: str,
    *,
    cash_delta: int = 0,
    bank_delta: int = 0,
    frozen_delta: int = 0,
):
    channel_id = settings.get("economy_log_channel")
    if not guild or not channel_id:
        return
    channel = guild.get_channel(int(channel_id))
    if not channel:
        return

    user = ensure_user(str(member_id))
    embed = Embed(title="📒 Лог экономики", color=0x3498DB)
    embed.description = f"Участник: <@{member_id}>\nПричина: {reason}"
    embed.add_field(
        name="Изменения",
        value=(
            f"Наличка: **{cash_delta:+,}**\n"
            f"Банк: **{bank_delta:+,}**\n"
            f"Заморожено: **{frozen_delta:+,}**"
        ).replace(",", "."),
        inline=False,
    )
    embed.add_field(
        name="Текущее состояние",
        value=(
            f"Наличка: **{fmt_money(user.get('наличка', 0))}**\n"
            f"Банк: **{fmt_money(user.get('банк', 0))}**\n"
            f"Заморожено: **{fmt_money(user.get('заморожено', 0))}**"
        ),
        inline=False,
    )
    try:
        await channel.send(embed=embed)
    except Exception:
        pass


def parse_interval(text: str) -> int:
    raw = text.strip().lower().replace(" ", "")
    if raw.isdigit():
        value = int(raw)
        if value <= 0:
            raise ValueError("Значение должно быть больше 0")
        return value

    units = {
        "с": 1,
        "sec": 1,
        "s": 1,
        "м": 60,
        "min": 60,
        "m": 60,
        "ч": 3600,
        "h": 3600,
        "д": 86400,
        "d": 86400,
    }
    for suffix, mult in units.items():
        if raw.endswith(suffix):
            num = raw[: -len(suffix)]
            if not num.isdigit():
                break
            value = int(num)
            if value <= 0:
                raise ValueError("Значение должно быть больше 0")
            return value * mult
    raise ValueError("Формат времени: 24ч / 30м / 10с / 1д")


def parse_select_emoji(raw_value: str | None):
    if not raw_value:
        return None

    value = str(raw_value).strip()
    if not value:
        return None

    parsed = discord.PartialEmoji.from_str(value)
    if parsed and parsed.id is not None:
        return parsed

    if value.startswith("<") and value.endswith(">"):
        return None

    return value


def get_passive_entries(user_id: str):
    return passive_flows.setdefault("users", {}).setdefault(user_id, [])


def save_passive_flows():
    save_json(PASSIVE_FLOW_FILE, passive_flows)


def normalize_command_name(name: str) -> str:
    return name.strip().lower().lstrip("!")


def get_command_access(command_name: str):
    cmd_key = normalize_command_name(command_name)
    access = command_access.setdefault("commands", {}).setdefault(
        cmd_key,
        {"users": [], "roles": [], "denied_users": [], "denied_roles": []},
    )
    access.setdefault("users", [])
    access.setdefault("roles", [])
    access.setdefault("denied_users", [])
    access.setdefault("denied_roles", [])
    return access


def has_custom_command_access(member: discord.Member, command_name: str) -> bool:
    access = get_command_access(command_name)
    user_id = str(member.id)
    role_ids = {str(role.id) for role in member.roles}
    return user_id in access.get("users", []) or bool(role_ids.intersection(set(access.get("roles", []))))


def has_custom_command_deny(member: discord.Member, command_name: str) -> bool:
    access = get_command_access(command_name)
    user_id = str(member.id)
    role_ids = {str(role.id) for role in member.roles}
    denied_users = set(access.get("denied_users", []))
    denied_roles = set(access.get("denied_roles", []))
    return user_id in denied_users or bool(role_ids.intersection(denied_roles))


def save_command_access():
    save_json(COMMAND_ACCESS_FILE, command_access)


def save_seasons_data():
    save_json(SEASONS_FILE, seasons_data)


def save_sphere_requests():
    save_json(SPHERE_REQUESTS_FILE, sphere_requests)


def save_tickets_data():
    save_json(TICKETS_FILE, tickets_data)


def save_reg_settings():
    save_json(REG_SETTINGS_FILE, reg_settings)


def save_ratings_data():
    save_json(RATINGS_FILE, ratings_data)


def ensure_player_state(user_id: str):
    users = player_state.setdefault("users", {})
    state = users.setdefault(
        user_id,
        {
            "shield_until": 0,
            "happiness": 50,
            "happiness_pause_until": 0,
            "soldiers": 0,
            "admin_description": "",
            "war_mode": False,
            "last_happiness_tick": int(time.time()),
            "last_mobilization_cost_tick": int(time.time()),
        },
    )
    state.setdefault("shield_until", 0)
    state.setdefault("happiness", 50)
    state.setdefault("happiness_pause_until", 0)
    state.setdefault("soldiers", 0)
    state.setdefault("admin_description", "")
    state.setdefault("war_mode", False)
    state.setdefault("last_happiness_tick", int(time.time()))
    state.setdefault("last_mobilization_cost_tick", int(time.time()))
    return state


def save_player_state():
    save_json(PLAYER_STATE_FILE, player_state)


def ensure_investments(user_id: str):
    return investments.setdefault("users", {}).setdefault(user_id, [])


def save_investments():
    save_json(INVESTMENTS_FILE, investments)


INVESTMENT_BANKS = {
    "alta-bank": {"name": "Alta-Bank", "cost": 100_000_000, "profit_pct": 5, "delay_chance": 0.0, "burn_chance": 0.0},
    "neo-bank": {"name": "Neo-Bank", "cost": 150_000_000, "profit_pct": 10, "delay_chance": 0.5, "burn_chance": 0.0},
    "fantom-bank": {"name": "Fantom-Bank", "cost": 170_000_000, "profit_pct": 25, "delay_chance": 0.0, "burn_chance": 0.4},
}


def get_population_growth_percent(happiness: int) -> int:
    table = {
        0: None,
        5: -10,
        10: -8,
        15: -7,
        20: -6,
        25: -5,
        30: -4,
        35: -3,
        40: -2,
        45: -1,
        50: 0,
        55: 1,
        60: 2,
        65: 3,
        70: 4,
        75: 5,
        80: 6,
        85: 7,
        90: 8,
        95: 9,
        100: 10,
    }
    step = max(0, min(100, int(happiness)))
    step = (step // 5) * 5
    if step == 0:
        return None
    return table.get(step, 0)


def get_mobilization_happiness_penalty(population_value: int, soldiers: int) -> int:
    total = population_value + soldiers
    if total <= 0:
        return 0
    pct = (soldiers / total) * 100
    if pct < 10:
        return 5
    if pct < 15:
        return 10
    if pct < 20:
        return 15
    return 20


def mark_request_processed_embed(embed: Embed, status_text: str):
    if not embed:
        embed = Embed(title="Заявка")
    fields = [f for f in embed.fields if f.name != "Статус"]
    embed.clear_fields()
    for f in fields:
        embed.add_field(name=f.name, value=f.value, inline=f.inline)
    embed.add_field(name="Статус", value=status_text, inline=False)
    return embed


def get_available_cash(user: dict) -> int:
    return int(user.get("наличка", 0)) - int(user.get("заморожено", 0))


def parse_money_value(value_text: str, base_amount: int) -> int:
    text = str(value_text).strip().replace(" ", "")
    if text.endswith("%"):
        pct_raw = text[:-1]
        pct = float(pct_raw.replace(",", "."))
        return int(round(base_amount * pct / 100.0))
    return int(text)


def apply_freeze_roles_for_member(guild: discord.Guild, member: discord.Member, now_ts: int, income_pool: int):
    user_id = str(member.id)
    user = ensure_user(user_id)
    frozen_total = 0
    frozen_details = []
    freeze_cfg = role_income.setdefault("freeze_roles", {})
    freeze_last = role_income.setdefault("freeze_last_claim", {}).setdefault(user_id, {})

    for rid, freeze_data in freeze_cfg.items():
        role = guild.get_role(int(rid))
        if not role or role not in member.roles:
            continue

        cooldown = int(freeze_data.get("cooldown", 0))
        if cooldown <= 0:
            continue

        last = int(freeze_last.get(rid, 0))
        if now_ts - last < cooldown:
            continue

        try:
            requested = parse_money_value(str(freeze_data.get("value", 0)), user.get("наличка", 0))
        except Exception:
            requested = 0

        if requested <= 0:
            freeze_last[rid] = now_ts
            continue

        available_income = max(0, income_pool)
        moved = min(available_income, requested)
        freeze_last[rid] = now_ts
        if moved <= 0:
            continue

        user["заморожено"] = user.get("заморожено", 0) + moved
        income_pool -= moved
        frozen_total += moved
        frozen_details.append(f"• {role.mention}: +{fmt_money(moved)} в заморозку")

    return frozen_total, frozen_details, income_pool


def format_seconds_left(seconds: int) -> str:
    return format_interval(max(0, int(seconds)))


def add_embed_lines_chunked(embed: Embed, field_name: str, lines: list[str], inline: bool = False, limit: int = 1024):
    if not lines:
        return

    chunks = []
    current = ""
    for raw_line in lines:
        line = str(raw_line) if raw_line is not None else " "
        candidate = line if not current else f"{current}\n{line}"

        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)

        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current = line

    if current:
        chunks.append(current)

    for idx, chunk in enumerate(chunks):
        chunk_name = field_name if idx == 0 else f"{field_name} (продолжение {idx + 1})"
        embed.add_field(name=chunk_name, value=chunk or " ", inline=inline)


def chunk_lines_for_embed(lines: list[str], limit: int = 1024) -> list[str]:
    if not lines:
        return []

    pages = []
    current = ""
    for raw_line in lines:
        line = str(raw_line) if raw_line is not None else " "
        candidate = line if not current else f"{current}\n{line}"
        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            pages.append(current)

        while len(line) > limit:
            pages.append(line[:limit])
            line = line[limit:]
        current = line

    if current:
        pages.append(current)

    return pages


def wipe_user_data(user_id: str, guild: discord.Guild = None):
    prev_user = balances.get(user_id, {}) if isinstance(balances.get(user_id), dict) else {}
    balances[user_id] = {
        "наличка": 0,
        "банк": 0,
        "заморожено": 0,
        "коины": int(prev_user.get("коины", 0)),
    }
    inventory.pop(user_id, None)
    pop = load_json(POPULATION_FILE, {})
    pop.pop(user_id, None)
    players = load_json(PLAYER_STATS_FILE, {})
    players.pop(user_id, None)
    passive_flows.setdefault("users", {}).pop(user_id, None)
    seasons_data.setdefault("user_progress", {}).pop(user_id, None)
    player_state.setdefault("users", {}).pop(user_id, None)
    investments.setdefault("users", {}).pop(user_id, None)
    old_country = country_owners.setdefault("user_to_country", {}).pop(user_id, None)
    if old_country:
        country_owners.setdefault("country_to_user", {}).pop(old_country, None)
    save_json(BALANCES_FILE, balances)
    save_inventory()
    save_json(POPULATION_FILE, pop)
    save_json(PLAYER_STATS_FILE, players)
    save_passive_flows()
    save_seasons_data()
    save_player_state()
    save_investments()
    save_country_owners()

    if guild is not None:
        member = guild.get_member(int(user_id))
        if member:
            role_ids = [int(rid) for rid in reg_settings.get("wipe_roles", []) if str(rid).isdigit()]
            roles_to_remove = [r for r in member.roles if r.id in role_ids]
            try:
                if roles_to_remove:
                    asyncio.create_task(member.remove_roles(*roles_to_remove, reason="Вайп игрока"))
            except Exception:
                pass
            try:
                asyncio.create_task(member.edit(nick=None, reason="Вайп игрока"))
            except Exception:
                pass


def ensure_investment_items():
    changed = False
    templates = [
        ("Alta-Bank", 100_000_000, "Безрисковый банк: +5%/сутки."),
        ("Neo-Bank", 150_000_000, "+10%/сутки, 50% шанс задержки вывода на сутки."),
        ("Fantom-Bank", 170_000_000, "+25%/сутки, 40% шанс полного сгорания."),
    ]
    for key, price, desc in templates:
        if key not in items_data.setdefault("items", {}):
            items_data["items"][key] = {
                "key": key,
                "price": price,
                "description": desc,
                "category": "3",
                "stock": -1,
                "expires_at": None,
                "require_roles": [],
                "give_roles": [],
                "remove_roles": [],
                "use_text": "🏦 Инвестиционный банк куплен.",
                "created_at": int(time.time()),
            }
            changed = True
    if changed:
        save_items()


def resolve_item_key(query: str):
    items = list(items_data.get("items", {}).keys())
    if not items:
        return []
    q = query.strip().lower()
    exact = [k for k in items if k.lower() == q]
    if exact:
        return exact
    starts = [k for k in items if k.lower().startswith(q)]
    if starts:
        return starts
    contains = [k for k in items if q in k.lower()]
    return contains


class CommandDenied(commands.CheckFailure):
    """Raised when custom deny rule blocks command usage."""


class ProcessCancelView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=None)
        self.author_id = int(author_id)
        self.cancelled = False
        self._cancel_event = asyncio.Event()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Только инициатор может отменить процесс.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Отмена", style=ButtonStyle.danger, emoji="🛑")
    async def cancel(self, interaction: Interaction, button: Button):
        self.cancelled = True
        self._cancel_event.set()
        await interaction.response.send_message("Процесс отменён.", ephemeral=True)
        self.stop()

    async def wait_cancel(self, timeout: int):
        await asyncio.wait_for(self._cancel_event.wait(), timeout=timeout)


async def ask_with_cancel(ctx, prompt: str, timeout: int = 300, title: str = "📝 Вопрос"):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    view = ProcessCancelView(ctx.author.id)
    await ctx.send(
        embed=Embed(
            title=title,
            description=f"{prompt}\n\nВведите `отмена` или нажмите кнопку ниже.",
            color=0x3498DB,
        ),
        view=view,
    )

    msg_task = asyncio.create_task(bot.wait_for("message", check=check, timeout=timeout))
    cancel_task = asyncio.create_task(view.wait_cancel(timeout=timeout))
    done, pending = await asyncio.wait({msg_task, cancel_task}, return_when=asyncio.FIRST_COMPLETED)

    for task in pending:
        task.cancel()

    if cancel_task in done:
        await ctx.send(embed=Embed(title="🛑 Отменено", description="Процесс остановлен пользователем.", color=0x808080))
        return None, True

    if msg_task in done:
        try:
            msg = msg_task.result()
        except Exception:
            await ctx.send(embed=Embed(title="⏰ Таймаут", description="Время ожидания истекло. Процесс отменён.", color=0xFFAA00))
            return None, True
        content = msg.content.strip()
        if content.lower() == "отмена":
            await ctx.send(embed=Embed(title="🛑 Отменено", description="Процесс остановлен пользователем.", color=0x808080))
            return None, True
        return content, False

    await ctx.send(embed=Embed(title="⏰ Таймаут", description="Время ожидания истекло. Процесс отменён.", color=0xFFAA00))
    return None, True


# ================== CHECKS & EVENTS ==================
@bot.check
async def only_allowed_guild(ctx):
    return bool(ctx.guild and ctx.guild.id == ALLOWED_GUILD)


@bot.check
async def check_custom_command_denies(ctx):
    if ctx.command and has_custom_command_deny(ctx.author, ctx.command.qualified_name):
        raise CommandDenied("Вам запрещено использовать эту команду.")
    return True


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")
    ensure_investment_items()
    status_text = (settings.get("status_text") or "").strip()
    status_emoji = (settings.get("status_emoji") or "").strip()
    status_until = settings.get("status_until")
    if status_text and (status_until is None or int(status_until) > int(time.time())):
        activity_text = f"{status_emoji} {status_text}".strip()
        try:
            await bot.change_presence(activity=discord.CustomActivity(name=activity_text))
        except Exception:
            pass
    else:
        settings["status_text"] = None
        settings["status_emoji"] = None
        settings["status_until"] = None
        save_json(SETTINGS_FILE, settings)
    if not auto_role_income_loop.is_running():
        auto_role_income_loop.start()


@bot.event
async def on_member_join(member: discord.Member):
    if member.guild.id != ALLOWED_GUILD:
        return

    channel_id = settings.get("invite_channel")
    channel = member.guild.get_channel(int(channel_id)) if channel_id else None
    if not channel:
        return

    embed = Embed(
        title="👋 Добро пожаловать!",
        description=f"{member.mention}, добро пожаловать на сервер **{member.guild.name}**!",
        color=0x00FF88,
    )
    embed.add_field(name="Участник", value=f"{member} (`{member.id}`)", inline=False)
    avatar = member.display_avatar.url if member.display_avatar else None
    if avatar:
        embed.set_thumbnail(url=avatar)

    try:
        await channel.send(embed=embed)
    except Exception:
        pass


@bot.event
async def on_member_remove(member: discord.Member):
    if member.guild.id != ALLOWED_GUILD:
        return

    try:
        wipe_user_data(str(member.id), member.guild)
    except Exception:
        pass

    channel_id = settings.get("invite_channel")
    channel = member.guild.get_channel(int(channel_id)) if channel_id else None
    if not channel:
        return

    embed = Embed(
        title="👋 До свидания",
        description=f"{member.mention}, удачи! Будем рады видеть снова.",
        color=0xFFAA00,
    )
    embed.add_field(name="Участник", value=f"{member} (`{member.id}`)", inline=False)
    avatar = member.display_avatar.url if member.display_avatar else None
    if avatar:
        embed.set_thumbnail(url=avatar)

    try:
        await channel.send(embed=embed)
    except Exception:
        pass


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    if message.guild.id == ALLOWED_GUILD:
        news_channel_id = settings.get("news_channel")
        if news_channel_id and message.channel.id == int(news_channel_id):
            if len((message.content or "").strip()) < 150:
                original = message.content or ""
                try:
                    await message.delete()
                except Exception:
                    pass
                warn = Embed(
                    title="❌ Недостаточно символов",
                    description=(
                        f"{message.author.mention}, для публикации новости нужно минимум **150** символов.\n\n"
                        f"Ваш текст (скопируйте и дополните):\n```\n{original[:1500]}\n```"
                    ),
                    color=0xFF0000,
                )
                try:
                    await message.channel.send(embed=warn, delete_after=25)
                except Exception:
                    pass
            else:
                st = ensure_player_state(str(message.author.id))
                st["news_published"] = int(st.get("news_published", 0)) + 1
                save_player_state()

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.CommandOnCooldown):
        retry = int(error.retry_after)
        await ctx.send(
            embed=Embed(
                title="❌ Слишком рано!",
                description=f"{ctx.author.mention}, подожди **{retry // 60} мин {retry % 60} сек**!",
                color=0xFF0000,
            )
        )
        return

    if isinstance(error, CommandDenied):
        await ctx.send(
            embed=Embed(
                title="⛔ Доступ запрещён",
                description="Вам запрещено использовать эту команду.",
                color=0xFF0000,
            )
        )
        return

    if isinstance(error, commands.MissingPermissions) and ctx.command is not None:
        if has_custom_command_access(ctx.author, ctx.command.qualified_name):
            try:
                await ctx.reinvoke()
                return
            except commands.UserInputError as e:
                error = e
            except Exception:
                pass
            else:
                return

        if not isinstance(error, commands.UserInputError):
            await ctx.send(
                embed=Embed(
                    title="⛔ Недостаточно прав",
                    description="У вас нет прав для использования этой команды.",
                    color=0xFF0000,
                )
            )
            return

    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            embed=Embed(
                title="⛔ Ошибка доступа",
                description="Вы не можете использовать эту команду.",
                color=0xFF0000,
            )
        )
        return

    if isinstance(error, commands.UserInputError) and ctx.command is not None:
        usage_parts = []
        for pname, param in ctx.command.clean_params.items():
            is_optional = param.default is not param.empty
            part = f"[{pname}]" if is_optional else f"<{pname}>"
            usage_parts.append(part)
        usage = f"!{ctx.command.qualified_name} {' '.join(usage_parts)}".strip()

        examples = {
            "рег": "!рег @Игрок \"Германская Империя\" \"Сезон 1939\"",
            "результатзаявокканал": "!результатзаявокканал #канал",
            "принять": "!принять 12",
            "отклонить": "!отклонить 12 недостаточно подтверждений",
            "баланс": "!баланс @Игрок",
            "счастьестоп": "!счастьестоп @Игрок 24ч",
            "счастьевыдать": "!счастьевыдать @Игрок 70%",
            "мобилизировать": "!мобилизировать 1000",
            "распустить": "!распустить 500",
            "сеттикет": "!сеттикет",
            "тикетотправить": "!тикетотправить #канал",
            "удалитьтикет": "!удалитьтикет <ID или название>",
            "инвестировать": "!инвестировать 5000 Alta-Bank",
            "списоксезонов": "!списоксезонов",
            "тайнканал": "!тайнканал #канал",
            "рассылка": "!рассылка Текст объявления",
            "кдгод": "!кдгод 24ч",
            "мут": "!мут @игрок 4ч причина",
            "бан": "!бан @игрок - причина",
            "кик": "!кик @игрок - причина",
            "варн": "!варн @игрок - причина",
            "модерлогканал": "!модерлогканал #канал",
            "варнпредел": "!варнпредел 3 мут 1ч",
            "наказания": "!наказания",
            "размут": "!размут @игрок причина",
            "разбан": "!разбан 123456789012345678 причина",
            "снятьварн": "!снятьварн @игрок 1 причина",
            "занятстраны": "!занятстраны",
            "свободстраны": "!свободстраны",
            "население": "!население начислить @игрок 1000",
            "население начислить": "!население начислить @игрок 1000",
            "население забрать": "!население забрать @игрок 500",
            "солдаты": "!солдаты начислить @игрок 100",
            "солдаты начислить": "!солдаты начислить @игрок 100",
            "солдаты забрать": "!солдаты забрать @игрок 50",
            "статы": "!статы",
            "удалитьстат": "!удалитьстат \"Германская Империя\"",
            "инвентарь": "!инвентарь @Игрок",
            "хелп": "!хелп",
            "инвайтканал": "!инвайтканал #канал",
            "грабеж": "!грабеж @игрок",
            "грабежсейвроль": "!грабежсейвроль @роль",
            "передать": "!передать @игрок 5000",
            "передатьроль": "!передатьроль @роль",
            "продать": "!продать @игрок 2 Панцер 25000",
            "продатьроль": "!продатьроль @роль",
            "редактироватьпредмет": "!редактироватьпредмет Панцер цена",
            "предметинфо": "!предметинфо Панцер",
            "логэко": "!логэко #канал",
        }
        example = examples.get(ctx.command.qualified_name)
        details = f"**Синтаксис:**\n`{usage}`"
        if example:
            details += f"\n\n**Пример:**\n`{example}`"
        details += (
            "\n\nПроверьте порядок аргументов, типы значений и упоминания ролей/игроков."
            "\nЕсли текстовый аргумент содержит 2+ слова, указывайте его в кавычках: `\"...\"`."
        )

        await ctx.send(
            embed=Embed(
                title="❌ Неверный формат команды",
                description=details,
                color=0xFF0000,
            )
        )
        return

    raise error


# ================== BASE COMMANDS ==================
@bot.command()
async def пинг(ctx):
    await ctx.send(embed=Embed(title="🏓 Пинг", description="**Понг!**", color=0x3498DB))


@bot.command()
async def привет(ctx):
    await ctx.send(
        embed=Embed(
            title="👋 Приветствие",
            description=f"Привет, {ctx.author.mention}!\n\nРад тебя видеть на сервере.",
            color=0x3498DB,
        )
    )


@bot.command(name="хелп")
async def хелп(ctx):
    categories = {
        "База": {"пинг", "привет", "хелп", "баланс", "профиль", "статистика", "топ"},
        "Экономика": {"работа", "депозит", "снять", "валюта", "коллект", "доходсписок", "начислить", "забрать", "доходдобавить", "доходудалить", "заморозкароль", "заморозкарольудалить", "заморозкавывести", "кдгод", "автоколлектканал", "грабеж", "грабежсейвроль", "передать", "передатьроль", "логэко"},
        "Магазин / Инвентарь": {"категориядобавить", "категорияудалить", "создатьпредмет", "редактироватьпредмет", "предметинфо", "магазин", "купить", "пополнитьпредмет", "удалитьпредмет", "инвентарь", "использовать", "выдать", "изъять", "инвестировать", "продать", "продатьпредмет", "продатьроль"},
        "Сезоны / Сферы": {"создатьсезон", "списоксезонов", "установитьсезон", "удалитьсезон", "создатьсферу", "редактсферу", "удалитьсферу", "сферы", "заявкиканал", "результатзаявокканал", "принять", "отклонить"},
        "Тикеты / Переговоры": {"сеттикет", "тикетотправить", "тикетотправиить", "тикетроль", "тикетнероль", "тикетроли", "удалитьтикет", "тайнканал"},
        "Модерация": {"мут", "размут", "бан", "разбан", "кик", "варн", "снятьварн", "варнпредел", "наказания", "модерлогканал", "рассылка"},
        "Регистрация / Страны": {"создатьстат", "удалитьстат", "статы", "рег", "регроли", "занятстраны", "свободстраны", "счастьевыдать", "счастьестоп", "мобилизировать", "распустить", "население", "солдаты"},
        "Пассивные операции": {"пасдоход", "пасрасход", "пасдоходубрать", "пасрасходубрать"},
        "Права": {"разрешить", "запретить", "разрешения"},
        "Вайпы": {"вайп", "отменитьвайп", "отменавайпа", "вайпигрок"},
    }

    all_names = sorted({cmd.name for cmd in bot.commands if not cmd.hidden}, key=lambda x: x.casefold())
    grouped = {cat: [] for cat in categories.keys()}
    other = []

    for name in all_names:
        placed = False
        for cat, names in categories.items():
            if name in names:
                grouped[cat].append(name)
                placed = True
                break
        if not placed:
            other.append(name)

    embed = Embed(title="📘 Справка по командам", description="Ниже все команды бота по категориям.", color=0x3498DB)

    def add_field_chunk(title: str, cmd_names: list[str]):
        if not cmd_names:
            return
        lines = [f"`!{n}`" for n in sorted(dict.fromkeys(cmd_names), key=lambda x: x.casefold())]
        chunk = ""
        for line in lines:
            candidate = f"{chunk}\n{line}".strip()
            if len(candidate) > 1000:
                embed.add_field(name=title, value=chunk, inline=False)
                chunk = line
                title = f"{title} (продолжение)"
            else:
                chunk = candidate
        if chunk:
            embed.add_field(name=title, value=chunk, inline=False)

    for cat_name in categories.keys():
        add_field_chunk(cat_name, grouped[cat_name])

    if other:
        add_field_chunk("Прочее", other)

    await ctx.send(embed=embed)


class BalancePagesView(View):
    def __init__(self, pages: list[Embed], author_id: int):
        super().__init__(timeout=180)
        self.pages = pages
        self.author_id = author_id
        self.index = 0

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Только автор команды может листать страницы.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: Interaction, button: Button):
        self.index = (self.index - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: Interaction, button: Button):
        self.index = (self.index + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)


# ================== ECONOMY ==================
@bot.command()
@commands.cooldown(1, 1800, commands.BucketType.user)
async def работа(ctx):
    user = ensure_user(str(ctx.author.id))
    earnings = random.randint(7000000, 7000000)
    user["наличка"] += earnings
    save_json(BALANCES_FILE, balances)

    await ctx.send(
        embed=Embed(
            title="💼 Работа выполнена!",
            description=f"{ctx.author.mention}, заработал **{fmt_money(earnings)}**!",
            color=0x00FF00,
        )
    )
    await log_economy_change(ctx.guild, ctx.author.id, "Команда !работа", cash_delta=earnings)


@bot.command(name="баланс")
async def balance(ctx, *, target: str = None):
    if target:
        try:
            role = await commands.RoleConverter().convert(ctx, target)
        except Exception:
            role = None

        if role is not None:
            members = [m for m in ctx.guild.members if (not m.bot and role in m.roles)]
            if not members:
                await ctx.send(
                    embed=Embed(
                        title=f"💰 Баланс роли — {role.name}",
                        description="С этой ролью нет игроков.",
                        color=0x3498DB,
                    )
                )
                return

            total_cash = 0
            total_bank = 0
            total_frozen = 0
            for m in members:
                u = ensure_user(str(m.id))
                total_cash += int(u.get("наличка", 0))
                total_bank += int(u.get("банк", 0))
                total_frozen += int(u.get("заморожено", 0))

            total_sum = total_cash + total_bank
            total_available = total_cash - total_frozen
            embed = Embed(title=f"💰 Баланс роли — {role.name}", color=0x00FF00)
            embed.description = (
                f"**👥 Игроков с ролью:** {len(members)}\n\n"
                f"**💵 Общая наличка:** {fmt_money(total_cash)}\n\n"
                f"**🏦 Общий банк:** {fmt_money(total_bank)}\n\n"
                f"**📊 Общий баланс:** {fmt_money(total_sum)}\n\n"
                f"**🧊 Общая заморозка:** {fmt_money(total_frozen)}\n\n"
                f"**✅ Общий доступный баланс:** {fmt_money(total_available)}"
            )
            await ctx.send(embed=embed)
            return

        try:
            member = await commands.MemberConverter().convert(ctx, target)
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Не удалось найти игрока или роль для просмотра баланса.", color=0xFF0000))
            return
    else:
        member = ctx.author

    user_id = str(member.id)
    user = ensure_user(user_id)
    total = user["наличка"] + user["банк"]
    frozen = user.get("заморожено", 0)
    available = user["наличка"] - frozen

    entries = get_passive_entries(user_id)
    expenses = [entry for entry in entries if entry.get("type") == "expense"]
    incomes = [entry for entry in entries if entry.get("type") == "income"]

    embed = Embed(title=f"💰 Баланс — {member.display_name}", color=0x00FF00)
    embed.description = (
        f"**💵 Наличка:** {fmt_money(user['наличка'])}\n\n"
        f"**🏦 Банк:** {fmt_money(user['банк'])}\n\n"
        f"**📊 Всего:** {fmt_money(total)}\n\n"
        f"**🧊 Заморожено:** {fmt_money(frozen)}\n\n"
        f"**✅ Доступно:** {fmt_money(available)}"
    )

    passive_lines = []
    if expenses:
        passive_lines.append("**Расходы:**")
        for idx, entry in enumerate(expenses, start=1):
            expires_at = entry.get("expires_at")
            ttl_text = "∞" if expires_at is None else format_seconds_left(int(expires_at) - int(time.time()))
            passive_lines.append(
                f"- **расход {idx}:** {fmt_money(entry['amount'])} раз в {format_interval(entry['cooldown'])}\n"
                f"  ↳ {entry.get('description', 'без описания')}\n"
                f"  ↳ действует: {ttl_text}"
            )
    if incomes:
        if passive_lines:
            passive_lines.append("")
        for idx, entry in enumerate(incomes, start=1):
            expires_at = entry.get("expires_at")
            ttl_text = "∞" if expires_at is None else format_seconds_left(int(expires_at) - int(time.time()))
            passive_lines.append(
                f"- **доход {idx}:** {fmt_money(entry['amount'])} раз в {format_interval(entry['cooldown'])}\n"
                f"  ↳ {entry.get('description', 'без описания')}\n"
                f"  ↳ действует: {ttl_text}"
            )

    extra_pages: list[tuple[str, str]] = []
    if passive_lines:
        passive_pages = chunk_lines_for_embed(passive_lines)
        for idx, page_text in enumerate(passive_pages, start=1):
            extra_pages.append((f"Пассивные операции ({idx}/{len(passive_pages)})", page_text))

    invs = ensure_investments(user_id)
    inv_lines = []
    now_ts = int(time.time())
    for inv in invs:
        if inv.get("status") != "active":
            continue
        bank = inv.get("bank_name", "Банк")
        amount = int(inv.get("amount", 0))
        left = max(0, int(inv.get("next_at", now_ts)) - now_ts)
        inv_lines.append(f"• {bank}: {fmt_money(amount)} — результат через {format_seconds_left(left)}")
    if inv_lines:
        inv_pages = chunk_lines_for_embed(inv_lines)
        for idx, page_text in enumerate(inv_pages, start=1):
            extra_pages.append((f"🏦 Инвестиции ({idx}/{len(inv_pages)})", page_text))

    if not extra_pages:
        await ctx.send(embed=embed)
        return

    embeds = []
    total_pages = len(extra_pages)
    for idx, (field_title, field_value) in enumerate(extra_pages, start=1):
        page_embed = Embed(title=embed.title, description=embed.description, color=embed.color)
        page_embed.add_field(name=field_title, value=field_value, inline=False)
        page_embed.set_footer(text=f"Страница {idx}/{total_pages}")
        embeds.append(page_embed)

    if len(embeds) == 1:
        await ctx.send(embed=embeds[0])
        return

    view = BalancePagesView(embeds, ctx.author.id)
    await ctx.send(embed=embeds[0], view=view)


@bot.command()
async def депозит(ctx, amount: str):
    user = ensure_user(str(ctx.author.id))

    try:
        amount_value = parse_money_value(amount, user["наличка"])
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка!", description="Введите число или процент (например `500` или `10%`).", color=0xFF0000))
        return

    if amount_value <= 0 or get_available_cash(user) < amount_value:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка!",
                description=f"{ctx.author.mention}, недостаточно налички или сумма <= 0!",
                color=0xFF0000,
            )
        )
        return

    user["наличка"] -= amount_value
    user["банк"] += amount_value
    save_json(BALANCES_FILE, balances)

    await ctx.send(
        embed=Embed(
            title="🏦 Депозит успешен",
            description=f"{ctx.author.mention} положил **{fmt_money(amount_value)}**!",
            color=0x00FF00,
        )
    )
    await log_economy_change(ctx.guild, ctx.author.id, "Депозит", cash_delta=-amount_value, bank_delta=amount_value)


@bot.command()
async def снять(ctx, amount: str):
    user = ensure_user(str(ctx.author.id))

    try:
        amount_value = parse_money_value(amount, user["банк"])
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка!", description="Введите число или процент (например `500` или `10%`).", color=0xFF0000))
        return

    if amount_value <= 0 or user["банк"] < amount_value:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка!",
                description=f"{ctx.author.mention}, недостаточно средств или сумма <= 0!",
                color=0xFF0000,
            )
        )
        return

    user["банк"] -= amount_value
    user["наличка"] += amount_value
    save_json(BALANCES_FILE, balances)

    await ctx.send(
        embed=Embed(
            title="🏦 Снятие успешно",
            description=f"{ctx.author.mention} снял **{fmt_money(amount_value)}**!",
            color=0x00FF00,
        )
    )
    await log_economy_change(ctx.guild, ctx.author.id, "Снятие", cash_delta=amount_value, bank_delta=-amount_value)


@bot.command()
@commands.has_permissions(administrator=True)
async def валюта(ctx, *, new_currency: str):
    global currency
    currency = new_currency
    balances["валюта"] = currency
    save_json(BALANCES_FILE, balances)

    await ctx.send(
        embed=Embed(
            title="✅ Валюта обновлена!",
            description=f"Новая валюта: {currency}",
            color=0x00FF00,
        )
    )


@bot.command(name="логэко")
@commands.has_permissions(administrator=True)
async def логэко(ctx, channel: discord.TextChannel):
    settings["economy_log_channel"] = channel.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(
        embed=Embed(
            title="✅ Канал логов экономики установлен",
            description=f"Все изменения балансов будут отправляться в {channel.mention}.",
            color=0x00FF00,
        )
    )


@bot.command(name="новостиканал")
@commands.has_permissions(administrator=True)
async def новостиканал(ctx, channel: discord.TextChannel):
    settings["news_channel"] = channel.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(embed=Embed(title="✅ Новостной канал установлен", description=f"Канал новостей: {channel.mention}", color=0x00FF00))


@bot.command(name="валютакоин")
@commands.has_permissions(administrator=True)
async def валютакоин(ctx, *, coin_name: str):
    settings["coin_currency"] = coin_name.strip() or "Alta-коин"
    save_json(SETTINGS_FILE, settings)
    await ctx.send(embed=Embed(title="✅ Серверная валюта обновлена", description=f"Новая серверная валюта: **{settings['coin_currency']}**", color=0x00FF00))


@bot.command(name="начислитькоины")
@commands.has_permissions(administrator=True)
async def начислитькоины(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return
    user = ensure_user(str(member.id))
    user["коины"] = int(user.get("коины", 0)) + amount
    save_json(BALANCES_FILE, balances)
    await ctx.send(embed=Embed(title="✅ Коины начислены", description=f"{member.mention} получил **{fmt_num(amount)} {settings.get('coin_currency', 'Alta-коин')}**.", color=0x00FF00))


@bot.command(name="забратькоины")
@commands.has_permissions(administrator=True)
async def забратькоины(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return
    user = ensure_user(str(member.id))
    user["коины"] = int(user.get("коины", 0)) - amount
    save_json(BALANCES_FILE, balances)
    await ctx.send(embed=Embed(title="⚠️ Коины списаны", description=f"У {member.mention} списано **{fmt_num(amount)} {settings.get('coin_currency', 'Alta-коин')}**.", color=0xFFA500))


@bot.command(name="статус")
@commands.has_permissions(administrator=True)
async def статус(ctx, emoji: str, description: str, duration: str = None):
    until = None
    if duration:
        try:
            until = int(time.time()) + parse_interval(duration)
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Неверный формат времени. Пример: 1ч, 30м, 2д", color=0xFF0000))
            return

    settings["status_emoji"] = emoji
    settings["status_text"] = description
    settings["status_until"] = until
    save_json(SETTINGS_FILE, settings)
    try:
        await bot.change_presence(activity=discord.CustomActivity(name=f"{emoji} {description}".strip()))
    except Exception:
        pass
    ttl_text = "до ручного снятия" if until is None else format_seconds_left(until - int(time.time()))
    await ctx.send(embed=Embed(title="✅ Статус установлен", description=f"**Статус:** {emoji} {description}\n**Срок:** {ttl_text}", color=0x00FF00))


@bot.command(name="статусубрать")
@commands.has_permissions(administrator=True)
async def статусубрать(ctx):
    settings["status_emoji"] = None
    settings["status_text"] = None
    settings["status_until"] = None
    save_json(SETTINGS_FILE, settings)
    try:
        await bot.change_presence(activity=None)
    except Exception:
        pass
    await ctx.send(embed=Embed(title="✅ Статус очищен", color=0x00FF00))


@bot.command(name="разрешить")
@commands.has_permissions(administrator=True)
async def разрешить(ctx, target: str = None, *, command_name: str = None):
    if not target or not command_name:
        await ctx.send(
            embed=Embed(
                title="ℹ️ Использование команды",
                description=(
                    "**Формат:** `!разрешить <@пользователь|@роль> <команда>`\n\n"
                    "**Примеры:**\n"
                    "`!разрешить @Чибрик вайпигрок`\n"
                    "`!разрешить @Куратор доходдобавить`"
                ),
                color=0x3498DB,
            )
        )
        return

    cmd_key = normalize_command_name(command_name)
    cmd_obj = bot.get_command(cmd_key)
    if cmd_obj is None:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Команда `{cmd_key}` не найдена.", color=0xFF0000))
        return

    access = get_command_access(cmd_key)

    user_id = None
    role_id = None
    if ctx.message.role_mentions:
        role_id = str(ctx.message.role_mentions[0].id)
    elif ctx.message.mentions:
        user_id = str(ctx.message.mentions[0].id)
    else:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка",
                description="Нужно указать **упоминание пользователя** или **упоминание роли**.",
                color=0xFF0000,
            )
        )
        return

    if user_id:
        if user_id in access["users"]:
            await ctx.send(embed=Embed(title="ℹ️ Уже разрешено", description="У этого пользователя уже есть доступ к команде.", color=0x3498DB))
            return
        access["users"].append(user_id)
        subject = f"пользователь {ctx.message.mentions[0].mention}"
    else:
        if role_id in access["roles"]:
            await ctx.send(embed=Embed(title="ℹ️ Уже разрешено", description="У этой роли уже есть доступ к команде.", color=0x3498DB))
            return
        access["roles"].append(role_id)
        subject = f"роль {ctx.message.role_mentions[0].mention}"

    save_command_access()
    await ctx.send(
        embed=Embed(
            title="✅ Доступ выдан",
            description=f"{subject} теперь может использовать команду `!{cmd_obj.qualified_name}`.",
            color=0x00FF00,
        )
    )


@bot.command(name="запретить")
@commands.has_permissions(administrator=True)
async def запретить(ctx, target: str = None, *, command_name: str = None):
    if not target or not command_name:
        await ctx.send(
            embed=Embed(
                title="ℹ️ Использование команды",
                description=(
                    "**Формат:** `!запретить <@пользователь|@роль> <команда>`\n\n"
                    "**Примеры:**\n"
                    "`!запретить @Чибрик вайпигрок`\n"
                    "`!запретить @Куратор доходдобавить`"
                ),
                color=0x3498DB,
            )
        )
        return

    cmd_key = normalize_command_name(command_name)
    cmd_obj = bot.get_command(cmd_key)
    if cmd_obj is None:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Команда `{cmd_key}` не найдена.", color=0xFF0000))
        return

    access = get_command_access(cmd_key)

    user_id = None
    role_id = None
    if ctx.message.role_mentions:
        role_id = str(ctx.message.role_mentions[0].id)
    elif ctx.message.mentions:
        user_id = str(ctx.message.mentions[0].id)
    else:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка",
                description="Нужно указать **упоминание пользователя** или **упоминание роли**.",
                color=0xFF0000,
            )
        )
        return

    if user_id:
        if user_id in access["users"]:
            access["users"].remove(user_id)
        if user_id not in access["denied_users"]:
            access["denied_users"].append(user_id)
        subject = f"пользователь {ctx.message.mentions[0].mention}"
    else:
        if role_id in access["roles"]:
            access["roles"].remove(role_id)
        if role_id not in access["denied_roles"]:
            access["denied_roles"].append(role_id)
        subject = f"роль {ctx.message.role_mentions[0].mention}"

    save_command_access()
    await ctx.send(
        embed=Embed(
            title="⛔ Доступ запрещён",
            description=f"{subject} теперь не может использовать команду `!{cmd_obj.qualified_name}`.",
            color=0xFF0000,
        )
    )


@bot.command(name="разрешения")
@commands.has_permissions(administrator=True)
async def разрешения(ctx):
    commands_map = command_access.get("commands", {})
    lines = []

    for cmd_name, access in commands_map.items():
        users = access.get("users", [])
        roles = access.get("roles", [])
        denied_users = access.get("denied_users", [])
        denied_roles = access.get("denied_roles", [])

        if not (users or roles or denied_users or denied_roles):
            continue

        lines.append(f"**!{cmd_name}**")
        if users:
            lines.append(f"✅ Пользователи: {' '.join(f'<@{uid}>' for uid in users)}")
        if roles:
            lines.append(f"✅ Роли: {' '.join(f'<@&{rid}>' for rid in roles)}")
        if denied_users:
            lines.append(f"⛔ Запрет users: {' '.join(f'<@{uid}>' for uid in denied_users)}")
        if denied_roles:
            lines.append(f"⛔ Запрет роли: {' '.join(f'<@&{rid}>' for rid in denied_roles)}")
        lines.append("")

    if not lines:
        await ctx.send(
            embed=Embed(
                title="📋 Разрешения",
                description="Пока нет выданных или запрещённых разрешений.",
                color=0x3498DB,
            )
        )
        return

    description = "\n".join(lines).strip()
    if len(description) > 4000:
        description = description[:3990] + "\n..."

    await ctx.send(
        embed=Embed(
            title="📋 Настроенные разрешения",
            description=description,
            color=0x3498DB,
        )
    )


# ================== SEASONS / SPHERES ==================

def get_active_spheres():
    active = seasons_data.get("active_season")
    return [sp for sp in seasons_data.get("spheres", {}).values() if sp.get("season") == active]


def get_user_sphere_level(user_id: str, sphere_name: str) -> int:
    return int(seasons_data.setdefault("user_progress", {}).setdefault(user_id, {}).get(sphere_name, 0))


def get_user_sphere_level_by_requirement(user_id: str, sphere_name: str) -> int:
    """Возвращает уровень сферы по требованию с учетом регистра/пробелов в названии."""
    progress = seasons_data.setdefault("user_progress", {}).setdefault(user_id, {})
    if sphere_name in progress:
        return int(progress.get(sphere_name, 0))

    normalized = str(sphere_name).strip().casefold()
    for name, level in progress.items():
        if str(name).strip().casefold() == normalized:
            return int(level)
    return 0


def set_user_sphere_level(user_id: str, sphere_name: str, level: int):
    seasons_data.setdefault("user_progress", {}).setdefault(user_id, {})[sphere_name] = level
    save_seasons_data()


@bot.command(name="создатьсезон")
@commands.has_permissions(administrator=True)
async def создатьсезон(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(embed=Embed(title="📅 Создание сезона", description="Укажите год сезона.", color=0x3498DB))
    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
        year = msg.content.strip()
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Не удалось получить название сезона.", color=0xFF0000))
        return

    if not year:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Название сезона не может быть пустым.", color=0xFF0000))
        return

    seasons_data.setdefault("seasons", {}).setdefault(year, {"created_by": str(ctx.author.id), "created_at": int(time.time())})
    save_seasons_data()
    await ctx.send(embed=Embed(title="✅ Сезон создан", description=f"Сезон **{year}** сохранён.", color=0x00FF00))


@bot.command(name="списоксезонов")
async def списоксезонов(ctx):
    seasons = list(seasons_data.get("seasons", {}).keys())
    if not seasons:
        await ctx.send(embed=Embed(title="📅 Сезоны", description="Сезоны ещё не созданы.", color=0xFFA500))
        return

    active = seasons_data.get("active_season")
    lines = []
    for name in seasons:
        marker = " (активный)" if str(name) == str(active) else ""
        lines.append(f"• **{name}**{marker}")

    await ctx.send(embed=Embed(title="📅 Список сезонов", description="\n".join(lines), color=0x3498DB))


@bot.command(name="установитьсезон")
@commands.has_permissions(administrator=True)
async def установитьсезон(ctx, year: str):
    seasons = list(seasons_data.get("seasons", {}).keys())
    if not seasons:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сезоны не созданы. Сначала используйте !создатьсезон.", color=0xFF0000))
        return

    query = year.strip().casefold()
    exact = [s for s in seasons if str(s).casefold() == query]
    starts = [s for s in seasons if str(s).casefold().startswith(query)]
    contains = [s for s in seasons if query in str(s).casefold()]
    matches = exact or starts or contains

    if not matches:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сезон не найден. Используйте `!списоксезонов` для просмотра доступных сезонов.", color=0xFF0000))
        return

    selected = matches[0]
    if len(matches) > 1:
        options = "\n".join(f"{i+1} — {name}" for i, name in enumerate(matches[:20]))
        await ctx.send(embed=Embed(title="🔎 Найдено несколько сезонов", description=f"Уточните номер сезона:\n\n{options}", color=0x3498DB))

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            idx = int(msg.content.strip()) - 1
            if idx < 0 or idx >= min(len(matches), 20):
                raise ValueError
            selected = matches[idx]
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Неверный номер сезона.", color=0xFF0000))
            return

    seasons_data["active_season"] = selected
    save_seasons_data()
    await ctx.send(embed=Embed(title="✅ Активный сезон", description=f"Теперь активен сезон **{selected}**.", color=0x00FF00))


@bot.command(name="удалитьсферу")
@commands.has_permissions(administrator=True)
async def удалитьсферу(ctx, *, sphere_name: str):
    key = sphere_name.strip().lower()
    sphere = seasons_data.get("spheres", {}).get(key)
    if not sphere:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сфера не найдена.", color=0xFF0000))
        return
    del seasons_data["spheres"][key]
    for uid, progress in seasons_data.setdefault("user_progress", {}).items():
        progress.pop(sphere.get("name"), None)
    save_seasons_data()
    await ctx.send(embed=Embed(title="✅ Сфера удалена", description=f"Сфера **{sphere.get('name', sphere_name)}** удалена.", color=0x00FF00))


@bot.command(name="удалитьсезон")
@commands.has_permissions(administrator=True)
async def удалитьсезон(ctx, year: str):
    if year not in seasons_data.get("seasons", {}):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сезон не найден.", color=0xFF0000))
        return
    del seasons_data["seasons"][year]
    to_del = [k for k, v in seasons_data.get("spheres", {}).items() if v.get("season") == year]
    for k in to_del:
        del seasons_data["spheres"][k]
    if seasons_data.get("active_season") == year:
        seasons_data["active_season"] = None
    seasons_data["user_progress"] = {}
    save_seasons_data()
    await ctx.send(embed=Embed(title="✅ Сезон удалён", description=f"Сезон **{year}** удалён вместе со сферами ({len(to_del)} шт.).", color=0x00FF00))


@bot.command(name="заявкиканал")
@commands.has_permissions(administrator=True)
async def заявкиканал(ctx, channel: discord.TextChannel, curator_role: discord.Role = None):
    sphere_requests["channel_id"] = channel.id
    sphere_requests["curator_role_id"] = curator_role.id if curator_role else None
    save_sphere_requests()
    await ctx.send(embed=Embed(title="✅ Канал заявок установлен", description=f"Канал: {channel.mention}", color=0x00FF00))


@bot.command(name="результатзаявокканал")
@commands.has_permissions(administrator=True)
async def результатзаявокканал(ctx, channel: discord.TextChannel):
    sphere_requests["result_channel_id"] = channel.id
    save_sphere_requests()
    await ctx.send(embed=Embed(title="✅ Канал результатов установлен", description=f"Канал: {channel.mention}", color=0x00FF00))


def build_sphere_level_preview_embed(sphere_name: str, season_name: str, levels: list[dict], index: int):
    level_data = levels[index]
    req_lines = [f"{r['sphere']} {r['level']}" for r in level_data.get("requirements", [])] or ["нет"]
    reward_lines = [f"<@&{rid}>" for rid in level_data.get("rewards", [])] or ["нет"]
    return Embed(
        title=f"🧩 {sphere_name} — уровень {index + 1}",
        description=(
            f"{level_data.get('description', '—')}\n\n"
            f"**Сезон:** {season_name}\n"
            f"**Цена:** {level_data.get('price', 0)} {currency}\n"
            f"**Требования:** {', '.join(req_lines)}\n"
            f"**Награды:** {', '.join(reward_lines)}"
        ),
        color=0x3498DB,
    )


class SphereLevelSetupModal(Modal):
    def __init__(self, parent_view: "SphereCreateSetupView", level_index: int):
        super().__init__(title=f"Настройка уровня {level_index + 1}", timeout=600)
        self.parent_view = parent_view
        self.level_index = level_index
        current = parent_view.levels[level_index]

        self.description_input = TextInput(
            label="Описание уровня",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
            default=current.get("description", "")[:1000],
        )
        self.price_input = TextInput(
            label="Цена уровня",
            required=True,
            max_length=20,
            default=str(current.get("price", 0)),
        )
        self.rewards_input = TextInput(
            label="Награды (<@&id> через пробел/скип)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000,
            default=(" ".join(f"<@&{rid}>" for rid in current.get("rewards", [])) or "скип"),
        )
        self.requirements_input = TextInput(
            label="Требования (Сфера:уровень или скип)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000,
            default=(
                ", ".join(f"{r['sphere']}:{r['level']}" for r in current.get("requirements", [])) or "скип"
            ),
        )

        self.add_item(self.description_input)
        self.add_item(self.price_input)
        self.add_item(self.rewards_input)
        self.add_item(self.requirements_input)

    async def on_submit(self, interaction: Interaction):
        try:
            price = int(str(self.price_input).strip())
            if price < 0:
                raise ValueError
        except Exception:
            await interaction.response.send_message("❌ Цена должна быть целым неотрицательным числом.", ephemeral=True)
            return

        rewards_raw = str(self.rewards_input).strip() or "скип"
        try:
            rewards = parse_role_mentions(rewards_raw)
        except Exception:
            await interaction.response.send_message("❌ Неверный формат ролей для награды.", ephemeral=True)
            return

        req_raw = str(self.requirements_input).strip() or "скип"
        requirements = []
        if req_raw.lower() != "скип":
            for token in req_raw.split(","):
                token = token.strip()
                if not token:
                    continue
                if ":" not in token:
                    await interaction.response.send_message("❌ Требование должно быть в формате `Сфера:уровень`.", ephemeral=True)
                    return
                sp, lv = token.split(":", 1)
                try:
                    requirements.append({"sphere": sp.strip(), "level": int(lv.strip())})
                except Exception:
                    await interaction.response.send_message("❌ Неверный уровень в требованиях.", ephemeral=True)
                    return

        self.parent_view.levels[self.level_index] = {
            "level": self.level_index + 1,
            "description": str(self.description_input).strip(),
            "price": price,
            "rewards": rewards,
            "requirements": requirements,
        }
        self.parent_view.completed_levels.add(self.level_index)

        if self.parent_view.control_message:
            try:
                await self.parent_view.control_message.edit(embed=self.parent_view.build_setup_embed(), view=self.parent_view)
            except Exception:
                pass

        await interaction.response.send_message(f"✅ Уровень {self.level_index + 1} сохранён.", ephemeral=True)


class SpherePreviewDecisionView(View):
    def __init__(self, setup_view: "SphereCreateSetupView"):
        super().__init__(timeout=600)
        self.setup_view = setup_view
        self.index = 0

    def build_embed(self):
        return build_sphere_level_preview_embed(
            self.setup_view.sphere_name,
            self.setup_view.season_name,
            self.setup_view.levels,
            self.index,
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.setup_view.author_id:
            await interaction.response.send_message("❌ Только инициатор может управлять предпросмотром.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⬅️", style=ButtonStyle.secondary)
    async def prev(self, interaction: Interaction, button: Button):
        self.index = (self.index - 1) % 5
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="➡️", style=ButtonStyle.secondary)
    async def next(self, interaction: Interaction, button: Button):
        self.index = (self.index + 1) % 5
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Отмена", style=ButtonStyle.danger)
    async def cancel(self, interaction: Interaction, button: Button):
        self.setup_view.result = "cancelled"
        self.setup_view.stop()
        await interaction.response.edit_message(
            embed=Embed(title="🛑 Создание сферы отменено", color=0x808080),
            view=None,
        )
        self.stop()

    @discord.ui.button(label="✏️ Продолжить редактирование", style=ButtonStyle.secondary)
    async def continue_edit(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(
            embed=Embed(title="✏️ Редактирование", description="Продолжайте настройку уровней через кнопки 1-5.", color=0x3498DB),
            view=None,
        )
        self.stop()

    @discord.ui.button(label="✅ Одобрить", style=ButtonStyle.success)
    async def approve(self, interaction: Interaction, button: Button):
        self.setup_view.result = "approved"
        self.setup_view.stop()
        await interaction.response.edit_message(
            embed=Embed(title="✅ Сфера одобрена", description="Финализирую создание сферы...", color=0x00FF00),
            view=None,
        )
        self.stop()


class SphereCreateSetupView(View):
    def __init__(self, author_id: int, sphere_name: str, season_name: str):
        super().__init__(timeout=1800)
        self.author_id = int(author_id)
        self.sphere_name = sphere_name
        self.season_name = season_name
        self.levels = [
            {"level": i + 1, "description": "", "price": 0, "rewards": [], "requirements": []}
            for i in range(5)
        ]
        self.completed_levels = set()
        self.result = "editing"
        self.control_message = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Только инициатор может настраивать сферу.", ephemeral=True)
            return False
        return True

    def build_setup_embed(self):
        lines = []
        for i in range(5):
            mark = "✅" if i in self.completed_levels else "⬜"
            lines.append(f"{mark} Уровень {i + 1}")
        return Embed(
            title=f"🧩 Создание сферы: {self.sphere_name}",
            description=(
                f"**Сезон:** {self.season_name}\n"
                "Нажмите кнопку уровня и заполните форму.\n\n"
                f"{chr(10).join(lines)}\n\n"
                "После заполнения всех уровней нажмите `✅ Готово` для предпросмотра."
            ),
            color=0x3498DB,
        )

    async def _open_level_modal(self, interaction: Interaction, level_index: int):
        await interaction.response.send_modal(SphereLevelSetupModal(self, level_index))

    @discord.ui.button(label="1", style=ButtonStyle.primary, row=0)
    async def level_1(self, interaction: Interaction, button: Button):
        await self._open_level_modal(interaction, 0)

    @discord.ui.button(label="2", style=ButtonStyle.primary, row=0)
    async def level_2(self, interaction: Interaction, button: Button):
        await self._open_level_modal(interaction, 1)

    @discord.ui.button(label="3", style=ButtonStyle.primary, row=0)
    async def level_3(self, interaction: Interaction, button: Button):
        await self._open_level_modal(interaction, 2)

    @discord.ui.button(label="4", style=ButtonStyle.primary, row=0)
    async def level_4(self, interaction: Interaction, button: Button):
        await self._open_level_modal(interaction, 3)

    @discord.ui.button(label="5", style=ButtonStyle.primary, row=0)
    async def level_5(self, interaction: Interaction, button: Button):
        await self._open_level_modal(interaction, 4)

    @discord.ui.button(label="✅ Готово", style=ButtonStyle.success, row=1)
    async def ready(self, interaction: Interaction, button: Button):
        if len(self.completed_levels) < 5:
            await interaction.response.send_message("⚠️ Сначала заполните все 5 уровней.", ephemeral=True)
            return

        preview_view = SpherePreviewDecisionView(self)
        await interaction.response.send_message(embed=preview_view.build_embed(), view=preview_view)

    @discord.ui.button(label="❌ Отмена", style=ButtonStyle.danger, row=1)
    async def stop_process(self, interaction: Interaction, button: Button):
        self.result = "cancelled"
        self.stop()
        await interaction.response.edit_message(
            embed=Embed(title="🛑 Создание сферы отменено", color=0x808080),
            view=None,
        )


@bot.command(name="создатьсферу")
@commands.has_permissions(administrator=True)
async def создатьсферу(ctx):
    name, cancelled = await ask_with_cancel(ctx, "Название сферы?", timeout=180, title="🧩 Создание сферы")
    if cancelled:
        return

    season_year, cancelled = await ask_with_cancel(ctx, "Год сезона?", timeout=180, title="🧩 Создание сферы")
    if cancelled:
        return

    if season_year not in seasons_data.get("seasons", {}):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Такой сезон не создан. Сначала !создатьсезон.", color=0xFF0000))
        return

    setup_view = SphereCreateSetupView(ctx.author.id, name, season_year)
    setup_message = await ctx.send(embed=setup_view.build_setup_embed(), view=setup_view)
    setup_view.control_message = setup_message
    await setup_view.wait()

    try:
        await setup_message.edit(view=None)
    except Exception:
        pass

    if setup_view.result == "cancelled":
        return

    if setup_view.result != "approved":
        await ctx.send(embed=Embed(title="⏰ Время вышло", description="Создание сферы не завершено.", color=0xFFAA00))
        return

    key = name.lower()
    seasons_data.setdefault("spheres", {})[key] = {
        "id": key,
        "name": name,
        "season": season_year,
        "levels": setup_view.levels,
    }
    save_seasons_data()
    await ctx.send(embed=Embed(title="✅ Сфера создана", description=f"Сфера **{name}** добавлена в сезон **{season_year}**.", color=0x00FF00))


@bot.command(name="редактсферу")
@commands.has_permissions(administrator=True)
async def редактсферу(ctx):
    sphere_query, cancelled = await ask_with_cancel(ctx, "Какая сфера?", timeout=180, title="🛠 Редактирование сферы")
    if cancelled:
        return

    sphere_key = str(sphere_query).strip().lower()
    sphere = seasons_data.get("spheres", {}).get(sphere_key)
    if not sphere:
        candidates = [
            k
            for k, v in seasons_data.get("spheres", {}).items()
            if sphere_key in k or sphere_key in str(v.get("name", "")).lower()
        ]
        if len(candidates) == 1:
            sphere_key = candidates[0]
            sphere = seasons_data.get("spheres", {}).get(sphere_key)
        else:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Сфера не найдена.", color=0xFF0000))
            return

    new_name_raw, cancelled = await ask_with_cancel(
        ctx,
        "Новое название сферы? (`скип` — оставить текущее)",
        timeout=180,
        title="🛠 Редактирование сферы",
    )
    if cancelled:
        return
    new_name = sphere.get("name", sphere_key) if new_name_raw.strip().lower() == "скип" else new_name_raw.strip()

    new_season_raw, cancelled = await ask_with_cancel(
        ctx,
        "Новый сезон? (`скип` — оставить текущий)",
        timeout=180,
        title="🛠 Редактирование сферы",
    )
    if cancelled:
        return
    if new_season_raw.strip().lower() == "скип":
        new_season = sphere.get("season")
    else:
        new_season = new_season_raw.strip()
        if new_season not in seasons_data.get("seasons", {}):
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Такой сезон не создан. Сначала !создатьсезон.", color=0xFF0000))
            return

    existing_levels = sphere.get("levels", [])
    setup_view = SphereCreateSetupView(ctx.author.id, new_name, new_season)
    for idx in range(5):
        if idx < len(existing_levels):
            setup_view.levels[idx] = {
                "level": idx + 1,
                "description": existing_levels[idx].get("description", ""),
                "price": int(existing_levels[idx].get("price", 0)),
                "rewards": list(existing_levels[idx].get("rewards", [])),
                "requirements": list(existing_levels[idx].get("requirements", [])),
            }
            setup_view.completed_levels.add(idx)

    setup_message = await ctx.send(embed=setup_view.build_setup_embed(), view=setup_view)
    setup_view.control_message = setup_message
    await setup_view.wait()

    try:
        await setup_message.edit(view=None)
    except Exception:
        pass

    if setup_view.result == "cancelled":
        return

    if setup_view.result != "approved":
        await ctx.send(embed=Embed(title="⏰ Время вышло", description="Редактирование сферы не завершено.", color=0xFFAA00))
        return

    old_name = sphere.get("name", sphere_key)
    old_key = sphere_key
    new_key = new_name.lower()

    updated_sphere = {
        "id": new_key,
        "name": new_name,
        "season": new_season,
        "levels": setup_view.levels,
    }

    if new_key != old_key:
        seasons_data.setdefault("spheres", {}).pop(old_key, None)
    seasons_data.setdefault("spheres", {})[new_key] = updated_sphere

    if new_name != old_name:
        for _, progress_map in seasons_data.setdefault("user_progress", {}).items():
            if old_name in progress_map and new_name not in progress_map:
                progress_map[new_name] = progress_map.pop(old_name)
            elif old_name in progress_map and new_name in progress_map:
                progress_map[new_name] = max(int(progress_map[new_name]), int(progress_map.pop(old_name)))

        for sp in seasons_data.setdefault("spheres", {}).values():
            for lvl in sp.get("levels", []):
                for req in lvl.get("requirements", []):
                    if str(req.get("sphere")) == old_name:
                        req["sphere"] = new_name

    save_seasons_data()
    await ctx.send(embed=Embed(title="✅ Готово", description="Сфера обновлена.", color=0x00FF00))


class SpherePurchaseModal(Modal, title="Заявка на сферу"):
    message_link = TextInput(label="Ссылка на сообщение", placeholder="https://discord.com/channels/...", required=True)

    def __init__(self, sphere_id: str, level: int):
        super().__init__(timeout=300)
        self.sphere_id = sphere_id
        self.level = level

    async def on_submit(self, interaction: Interaction):
        channel_id = sphere_requests.get("channel_id")
        if not channel_id:
            await interaction.response.send_message("Канал заявок не настроен (`!заявкиканал`).", ephemeral=True)
            return

        guild = interaction.guild
        review_channel = guild.get_channel(channel_id)
        if not review_channel:
            await interaction.response.send_message("Канал заявок не найден.", ephemeral=True)
            return

        async def ensure_pending_request_visible(req_obj: dict):
            """Гарантирует, что старая pending-заявка снова видна кураторам после изменений схемы."""
            if req_obj.get("status") != "pending":
                return

            review_ch = None
            review_msg_id = req_obj.get("review_message_id")
            if req_obj.get("review_channel_id"):
                review_ch = guild.get_channel(int(req_obj.get("review_channel_id")))

            if review_ch and review_msg_id:
                try:
                    await review_ch.fetch_message(int(review_msg_id))
                    return
                except Exception:
                    pass

            fallback_channel_id = sphere_requests.get("channel_id") or req_obj.get("source_channel_id")
            fallback_channel = guild.get_channel(int(fallback_channel_id)) if fallback_channel_id else None
            if not fallback_channel:
                return

            user_m = guild.get_member(int(req_obj.get("user_id", 0)))
            sphere_old = seasons_data.get("spheres", {}).get(str(req_obj.get("sphere_id")))
            sphere_label = sphere_old.get("name") if sphere_old else str(req_obj.get("sphere_id", "—"))
            curator_mentions = []
            if sphere_requests.get("curator_role_id"):
                curator_mentions.append(f"<@&{sphere_requests['curator_role_id']}>")
            sphere_access = get_command_access("сферы")
            curator_mentions.extend([f"<@&{rid}>" for rid in sphere_access.get("roles", [])])
            curator_mentions.extend([f"<@{uid}>" for uid in sphere_access.get("users", [])])
            curator_ping = " ".join(dict.fromkeys(curator_mentions))

            user_mention = user_m.mention if user_m else f"<@{req_obj.get('user_id')}>"
            rebuilt = Embed(
                title="📨 Восстановленная заявка на сферу",
                description=(
                    f"**ID:** {req_obj.get('id')}\n"
                    f"**Участник:** {user_mention}\n"
                    f"**Сфера:** {sphere_label}\n"
                    f"**Уровень:** {req_obj.get('level')}\n"
                    f"**Ссылка:** {req_obj.get('message_link', '—')}"
                ),
                color=0x3498DB,
            )
            msg = await fallback_channel.send(content=curator_ping or None, embed=rebuilt, view=SphereReviewView(str(req_obj.get("id"))))
            req_obj["review_channel_id"] = fallback_channel.id
            req_obj["review_message_id"] = msg.id
            save_sphere_requests()

        for req in sphere_requests.get("requests", {}).values():
            if (
                int(req.get("user_id", 0)) == interaction.user.id
                and str(req.get("sphere_id")) == self.sphere_id
                and int(req.get("level", 0)) == int(self.level)
                and req.get("status") == "pending"
            ):
                await ensure_pending_request_visible(req)
                await interaction.response.send_message(
                    f"Нельзя подать две одинаковые заявки одновременно: заявка #{req.get('id')} уже на рассмотрении.",
                    ephemeral=True,
                )
                return

        req_id = str(sphere_requests.get("next_id", 1))
        sphere_requests["next_id"] = int(req_id) + 1
        sphere_requests.setdefault("requests", {})[req_id] = {
            "id": req_id,
            "user_id": interaction.user.id,
            "guild_id": guild.id,
            "source_channel_id": interaction.channel_id,
            "sphere_id": self.sphere_id,
            "level": self.level,
            "message_link": str(self.message_link),
            "status": "pending",
        }
        save_sphere_requests()

        sphere = seasons_data["spheres"][self.sphere_id]
        curator_mentions = []
        if sphere_requests.get("curator_role_id"):
            curator_mentions.append(f"<@&{sphere_requests['curator_role_id']}>")
        sphere_access = get_command_access("сферы")
        curator_mentions.extend([f"<@&{rid}>" for rid in sphere_access.get("roles", [])])
        curator_mentions.extend([f"<@{uid}>" for uid in sphere_access.get("users", [])])
        curator_ping = " ".join(dict.fromkeys(curator_mentions))
        embed = Embed(
            title="📨 Новая заявка на сферу",
            description=(
                f"**ID:** {req_id}\n"
                f"**Участник:** {interaction.user.mention}\n"
                f"**Сфера:** {sphere['name']}\n"
                f"**Уровень:** {self.level}\n"
                f"**Ссылка:** {self.message_link}"
            ),
            color=0x3498DB,
        )
        review_message = await review_channel.send(content=curator_ping or None, embed=embed, view=SphereReviewView(req_id))
        sphere_requests["requests"][req_id]["review_channel_id"] = review_channel.id
        sphere_requests["requests"][req_id]["review_message_id"] = review_message.id
        save_sphere_requests()
        await interaction.response.send_message(embed=Embed(title="✅ Заявка отправлена", description=f"Заявка #{req_id} отправлена кураторам.", color=0x00FF00), ephemeral=True)


class RejectReasonModal(Modal, title="Причина отклонения"):
    reason = TextInput(label="Причина", style=discord.TextStyle.paragraph, required=True)

    def __init__(self, request_id: str):
        super().__init__(timeout=300)
        self.request_id = request_id

    async def on_submit(self, interaction: Interaction):
        req = sphere_requests.get("requests", {}).get(self.request_id)
        if not req or req.get("status") != "pending":
            await interaction.response.send_message("Заявка не найдена или уже обработана.", ephemeral=True)
            return
        req["status"] = "rejected"
        req["reason"] = str(self.reason)
        req["processed_by"] = interaction.user.id
        save_sphere_requests()

        result_channel_id = sphere_requests.get("result_channel_id") or req.get("source_channel_id")
        ch = interaction.guild.get_channel(result_channel_id)
        user = interaction.guild.get_member(req["user_id"])
        if ch and user:
            await ch.send(content=user.mention)
            await ch.send(
                embed=Embed(
                    title="❌ ОТКЛОНЕНО",
                    description=f"Заявка #{self.request_id} отклонена.\n**Причина:** {self.reason}",
                    color=0xFF0000,
                )
            )

        review_channel = interaction.guild.get_channel(req.get("review_channel_id")) if req.get("review_channel_id") else None
        if review_channel and req.get("review_message_id"):
            try:
                msg = await review_channel.fetch_message(req.get("review_message_id"))
                processed_embed = mark_request_processed_embed(
                    msg.embeds[0] if msg.embeds else Embed(title="Заявка"),
                    f"**Отклонено**\nКуратор: {interaction.user.mention}\nПричина: {self.reason}",
                )
                processed_embed.color = discord.Color.red()
                await msg.edit(embed=processed_embed, view=None)
            except Exception:
                pass

        await interaction.response.send_message("Заявка отклонена.", ephemeral=True)


class SphereReviewView(View):
    def __init__(self, request_id: str):
        super().__init__(timeout=None)
        self.request_id = request_id

    @discord.ui.button(label="✅ Принять", style=ButtonStyle.success)
    async def approve(self, interaction: Interaction, button: Button):
        req = sphere_requests.get("requests", {}).get(self.request_id)
        if not req or req.get("status") != "pending":
            await interaction.response.send_message("Заявка не найдена или уже обработана.", ephemeral=True)
            return

        user = ensure_user(str(req["user_id"]))
        sphere = seasons_data["spheres"].get(req["sphere_id"])
        if not sphere:
            await interaction.response.send_message("Сфера не найдена.", ephemeral=True)
            return
        level_data = sphere["levels"][req["level"] - 1]
        price = int(level_data["price"])
        if get_available_cash(user) < price:
            await interaction.response.send_message("Недостаточно доступных средств у игрока.", ephemeral=True)
            return

        user["наличка"] -= price
        set_user_sphere_level(str(req["user_id"]), sphere["name"], req["level"])
        save_json(BALANCES_FILE, balances)

        guild = interaction.guild
        member = guild.get_member(req["user_id"])
        if member:
            for rid in level_data.get("rewards", []):
                role = guild.get_role(int(rid))
                if role:
                    await member.add_roles(role)

        req["status"] = "approved"
        req["processed_by"] = interaction.user.id
        save_sphere_requests()

        result_channel_id = sphere_requests.get("result_channel_id") or req.get("source_channel_id")
        result_channel = guild.get_channel(result_channel_id)
        if result_channel and member:
            await result_channel.send(content=member.mention)
            await result_channel.send(
                embed=Embed(
                    title="✅ ОДОБРЕНО",
                    description=f"Заявка #{self.request_id} по сфере **{sphere['name']}** уровня **{req['level']}** одобрена.",
                    color=0x00FF00,
                )
            )

        processed_embed = interaction.message.embeds[0] if interaction.message and interaction.message.embeds else Embed(title="Заявка")
        processed_embed = mark_request_processed_embed(
            processed_embed,
            f"**Одобрено**\nКуратор: {interaction.user.mention}",
        )
        processed_embed.color = discord.Color.green()
        await interaction.message.edit(embed=processed_embed, view=None)
        await interaction.response.send_message("Заявка принята.", ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=ButtonStyle.danger)
    async def reject(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(RejectReasonModal(self.request_id))




async def _edit_sphere_review_message(guild: discord.Guild, req: dict, status_text: str, color: discord.Color):
    review_channel = guild.get_channel(req.get("review_channel_id")) if req.get("review_channel_id") else None
    if not review_channel or not req.get("review_message_id"):
        return
    try:
        msg = await review_channel.fetch_message(req.get("review_message_id"))
        processed_embed = mark_request_processed_embed(
            msg.embeds[0] if msg.embeds else Embed(title="Заявка"),
            status_text,
        )
        processed_embed.color = color
        await msg.edit(embed=processed_embed, view=None)
    except Exception:
        pass


@bot.command(name="принять")
@commands.has_permissions(administrator=True)
async def принять_заявку(ctx, request_id: str):
    req = sphere_requests.get("requests", {}).get(str(request_id))
    if not req:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Заявка не найдена.", color=0xFF0000))
        return
    if req.get("status") != "pending":
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Эта заявка уже обработана.", color=0xFF0000))
        return

    sphere = seasons_data.get("spheres", {}).get(req.get("sphere_id"))
    if not sphere:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сфера по заявке не найдена.", color=0xFF0000))
        return

    level_idx = int(req.get("level", 0)) - 1
    if level_idx < 0 or level_idx >= len(sphere.get("levels", [])):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Некорректный уровень в заявке.", color=0xFF0000))
        return

    user = ensure_user(str(req["user_id"]))
    level_data = sphere["levels"][level_idx]
    price = int(level_data.get("price", 0))
    if get_available_cash(user) < price:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="У игрока недостаточно доступных средств.", color=0xFF0000))
        return

    user["наличка"] -= price
    set_user_sphere_level(str(req["user_id"]), sphere["name"], int(req["level"]))
    save_json(BALANCES_FILE, balances)

    member = ctx.guild.get_member(req["user_id"])
    if member:
        for rid in level_data.get("rewards", []):
            role = ctx.guild.get_role(int(rid))
            if role:
                await member.add_roles(role)

    req["status"] = "approved"
    req["processed_by"] = ctx.author.id
    save_sphere_requests()

    result_channel_id = sphere_requests.get("result_channel_id") or req.get("source_channel_id")
    result_channel = ctx.guild.get_channel(result_channel_id)
    if result_channel and member:
        await result_channel.send(content=member.mention)
        await result_channel.send(
            embed=Embed(
                title="✅ ОДОБРЕНО",
                description=f"Заявка #{request_id} по сфере **{sphere['name']}** уровня **{req['level']}** одобрена.",
                color=0x00FF00,
            )
        )

    await _edit_sphere_review_message(ctx.guild, req, f"**Одобрено**\nКуратор: {ctx.author.mention}", discord.Color.green())
    await ctx.send(embed=Embed(title="✅ Готово", description=f"Заявка #{request_id} одобрена.", color=0x00FF00))


@bot.command(name="отклонить")
@commands.has_permissions(administrator=True)
async def отклонить_заявку(ctx, request_id: str, *, reason: str):
    req = sphere_requests.get("requests", {}).get(str(request_id))
    if not req:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Заявка не найдена.", color=0xFF0000))
        return
    if req.get("status") != "pending":
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Эта заявка уже обработана.", color=0xFF0000))
        return

    req["status"] = "rejected"
    req["reason"] = str(reason)
    req["processed_by"] = ctx.author.id
    save_sphere_requests()

    result_channel_id = sphere_requests.get("result_channel_id") or req.get("source_channel_id")
    ch = ctx.guild.get_channel(result_channel_id)
    user = ctx.guild.get_member(req["user_id"])
    if ch and user:
        await ch.send(content=user.mention)
        await ch.send(
            embed=Embed(
                title="❌ ОТКЛОНЕНО",
                description=f"Заявка #{request_id} отклонена.\n**Причина:** {reason}",
                color=0xFF0000,
            )
        )

    await _edit_sphere_review_message(ctx.guild, req, f"**Отклонено**\nКуратор: {ctx.author.mention}\nПричина: {reason}", discord.Color.red())
    await ctx.send(embed=Embed(title="✅ Готово", description=f"Заявка #{request_id} отклонена.", color=0x00FF00))

class SphereLevelsView(View):
    def __init__(self, user_id: int, sphere_id: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.sphere_id = sphere_id
        self.index = 0

    def build_embed(self):
        sphere = seasons_data["spheres"][self.sphere_id]
        level_data = sphere["levels"][self.index]
        req_lines = [f"{r['sphere']} {r['level']}" for r in level_data.get("requirements", [])] or ["нет"]
        reward_lines = [f"<@&{rid}>" for rid in level_data.get("rewards", [])] or ["нет"]
        return Embed(
            title=f"🧩 {sphere['name']} — уровень {self.index + 1}",
            description=(
                f"{level_data['description']}\n\n"
                f"**Цена:** {level_data['price']} {currency}\n"
                f"**Требования:** {', '.join(req_lines)}\n"
                f"**Награды:** {', '.join(reward_lines)}"
            ),
            color=0x3498DB,
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это меню не для вас.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⬅️", style=ButtonStyle.secondary)
    async def prev(self, interaction: Interaction, button: Button):
        self.index = (self.index - 1) % 5
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="➡️", style=ButtonStyle.secondary)
    async def next(self, interaction: Interaction, button: Button):
        self.index = (self.index + 1) % 5
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Приобрести сферу", style=ButtonStyle.success)
    async def buy(self, interaction: Interaction, button: Button):
        sphere = seasons_data["spheres"][self.sphere_id]
        wanted_level = self.index + 1
        current = get_user_sphere_level(str(interaction.user.id), sphere["name"])
        if wanted_level != current + 1:
            await interaction.response.send_message("Можно покупать только следующий уровень по очереди.", ephemeral=True)
            return
        reqs = sphere["levels"][self.index].get("requirements", [])
        for req in reqs:
            current_req_level = get_user_sphere_level_by_requirement(str(interaction.user.id), req["sphere"])
            required_level = int(req["level"])
            if current_req_level < required_level:
                await interaction.response.send_message(
                    f"Не выполнено требование: **{req['sphere']}** уровень **{required_level}+** (сейчас: {current_req_level}).",
                    ephemeral=True,
                )
                return
        await interaction.response.send_modal(SpherePurchaseModal(self.sphere_id, wanted_level))


@bot.command(name="сферы")
async def сферы(ctx):
    active = seasons_data.get("active_season")
    spheres = get_active_spheres()
    if not active:
        await ctx.send(embed=Embed(title="ℹ️ Сферы", description="Активный сезон не установлен (`!установитьсезон`).", color=0x3498DB))
        return
    if not spheres:
        await ctx.send(embed=Embed(title="ℹ️ Сферы", description=f"Для сезона {active} сфер пока нет.", color=0x3498DB))
        return

    options = [SelectOption(label=sp["name"], value=sp["id"]) for sp in spheres[:25]]
    select = Select(placeholder="Выберите сферу", options=options)

    async def callback(interaction: Interaction):
        sphere_id = select.values[0]
        view = SphereLevelsView(interaction.user.id, sphere_id)
        await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)

    select.callback = callback
    view = View(timeout=180)
    view.add_item(select)
    await ctx.send(embed=Embed(title=f"🧩 Сферы сезона {active}", description="Выберите сферу из списка.", color=0x3498DB), view=view)


@bot.command(name="понизитьсферу")
@commands.has_permissions(administrator=True)
async def понизитьсферу(ctx, member: discord.Member):
    user_id = str(member.id)
    progress = seasons_data.setdefault("user_progress", {}).setdefault(user_id, {})
    current = [(name, int(level)) for name, level in progress.items() if int(level) > 0]
    if not current:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="У игрока нет прокачанных сфер.", color=0xFF0000))
        return

    lines = "\n".join(f"• {name}: {level}" for name, level in sorted(current, key=lambda x: x[0].casefold()))
    await ctx.send(
        embed=Embed(
            title=f"📉 Понижение сфер — {member.display_name}",
            description=(
                f"Текущие уровни:\n{lines}\n\n"
                "Введите новое значение в формате: `Сфера:уровень`\n"
                "Пример: `Здравоохранение: 3`"
            ),
            color=0x3498DB,
        )
    )

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=180)
        raw = msg.content.strip()
        if ":" not in raw:
            raise ValueError("Неверный формат")
        sphere_name, level_text = [x.strip() for x in raw.split(":", 1)]
        if sphere_name not in progress:
            raise ValueError("Сфера не найдена у игрока")
        new_level = int(level_text)
        old_level = int(progress.get(sphere_name, 0))
        if new_level < 0 or new_level >= old_level:
            raise ValueError("Новый уровень должен быть меньше текущего и не ниже 0")
        progress[sphere_name] = new_level
        save_seasons_data()
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Не удалось понизить сферу: {e}", color=0xFF0000))
        return

    await ctx.send(embed=Embed(title="✅ Сфера понижена", description=f"{member.mention}: **{sphere_name}** → уровень **{new_level}**.", color=0x00FF00))


# ================== TICKETS ==================
class TicketFormModal(Modal):
    def __init__(self, form_id: str):
        form = tickets_data.get("forms", {}).get(form_id, {})
        super().__init__(title=form.get("name", "Тикет"), timeout=600)
        self.form_id = form_id
        self.inputs = []
        for q in form.get("questions", [])[:5]:
            inp = TextInput(label=q[:45], required=True, max_length=1000)
            self.inputs.append(inp)
            self.add_item(inp)

    async def on_submit(self, interaction: Interaction):
        form = tickets_data.get("forms", {}).get(self.form_id)
        if not form:
            await interaction.response.send_message("Форма тикета не найдена.", ephemeral=True)
            return

        guild = interaction.guild
        category = guild.get_channel(int(form.get("category_id", 0))) if form.get("category_id") else None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        for rid in tickets_data.get("access_roles", {}).get(self.form_id, []):
            role = guild.get_role(int(rid))
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        ticket_channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}".lower().replace(" ", "-")[:80],
            category=category,
            overwrites=overwrites,
        )

        answers = []
        for idx, q in enumerate(form.get("questions", [])[: len(self.inputs)]):
            answers.append(f"**{q}**\n{self.inputs[idx].value}")

        embed = Embed(title=f"🎫 Тикет: {form['name']}", color=0x3498DB)
        embed.add_field(name="Участник", value=interaction.user.mention, inline=False)
        embed.add_field(name="Ответы", value="\n\n".join(answers)[:1024] if answers else "—", inline=False)

        role_mentions = []
        for rid in tickets_data.get("access_roles", {}).get(self.form_id, []):
            role = guild.get_role(int(rid))
            if role:
                role_mentions.append(role.mention)

        ping_line = " ".join(role_mentions) if role_mentions else None
        await ticket_channel.send(content=ping_line, embed=embed, view=TicketCloseView(interaction.user.id))
        await interaction.response.send_message(embed=Embed(title="✅ Тикет создан", description=f"Ваш канал: {ticket_channel.mention}", color=0x00FF00), ephemeral=True)


class TicketCloseView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=None)
        self.author_id = int(author_id)

    @discord.ui.button(label="Закончить", style=ButtonStyle.danger)
    async def close_ticket(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.author_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Только автор тикета или модератор может закрыть тикет.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Тикет закрывается...", ephemeral=True)
        try:
            await interaction.channel.delete(reason=f"Тикет закрыт пользователем {interaction.user}")
        except Exception:
            pass


class TicketSelect(Select):
    def __init__(self):
        forms = list(tickets_data.get("forms", {}).values())[:25]
        options = []
        for f in forms:
            label = f["name"][:100]
            emoji = parse_select_emoji((f.get("emoji") or "").strip()[:64])
            if emoji is not None:
                options.append(SelectOption(label=label, value=f["id"], emoji=emoji))
            else:
                options.append(SelectOption(label=label, value=f["id"]))
        super().__init__(placeholder="Выберите тип тикета", options=options)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(TicketFormModal(self.values[0]))


@bot.command(name="сеттикет")
@commands.has_permissions(administrator=True)
async def сеттикет(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(embed=Embed(title="🎫 Настройка тикета", description="Название формы?", color=0x3498DB))
    name = (await bot.wait_for("message", check=check, timeout=300)).content.strip()
    await ctx.send(embed=Embed(title="🎫 Настройка тикета", description="Эмодзи при выборе формы? (например 🎯 или <:name:id>, либо `скип`)", color=0x3498DB))
    emoji_raw = (await bot.wait_for("message", check=check, timeout=300)).content.strip()
    form_emoji = "" if emoji_raw.lower() == "скип" else emoji_raw
    await ctx.send(embed=Embed(title="🎫 Настройка тикета", description="Вводите вопросы по одному сообщению. Напишите `Стоп` для завершения.", color=0x3498DB))
    questions = []
    while len(questions) < 10:
        msg = await bot.wait_for("message", check=check, timeout=300)
        txt = msg.content.strip()
        if txt.lower() == "стоп":
            break
        questions.append(txt)
    if not questions:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Добавьте хотя бы 1 вопрос.", color=0xFF0000))
        return

    await ctx.send(embed=Embed(title="🎫 Настройка тикета", description="Категория приватных каналов (mention/ID):", color=0x3498DB))
    cat_msg = await bot.wait_for("message", check=check, timeout=300)
    category = await commands.CategoryChannelConverter().convert(ctx, cat_msg.content.strip())

    form_id = str(tickets_data.get("next_id", 1))
    tickets_data["next_id"] = int(form_id) + 1
    tickets_data.setdefault("forms", {})[form_id] = {
        "id": form_id,
        "name": name,
        "emoji": form_emoji,
        "questions": questions,
        "category_id": category.id,
    }
    tickets_data.setdefault("access_roles", {}).setdefault(form_id, [])
    save_tickets_data()
    emoji_line = f"\nЭмодзи: {form_emoji}" if form_emoji else ""
    await ctx.send(embed=Embed(title="✅ Форма создана", description=f"ID: {form_id}\nНазвание: {name}{emoji_line}", color=0x00FF00))


@bot.command(name="тикетотправить", aliases=["тикетотправиить"])
@commands.has_permissions(administrator=True)
async def тикетотправить(ctx, channel: discord.TextChannel):
    if not tickets_data.get("forms"):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Нет форм тикетов. Используйте `!сеттикет`.", color=0xFF0000))
        return
    v = View(timeout=None)
    v.add_item(TicketSelect())
    await channel.send(embed=Embed(title="🎫 Тикеты", description="Выберите тип заявки", color=0x3498DB), view=v)
    await ctx.send(embed=Embed(title="✅ Готово", description=f"Панель тикетов отправлена в {channel.mention}", color=0x00FF00))


@bot.command(name="тикетроль")
@commands.has_permissions(administrator=True)
async def тикетроль(ctx, role: discord.Role):
    if not tickets_data.get("forms"):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сначала создайте формы: `!сеттикет`.", color=0xFF0000))
        return
    for form_id in tickets_data["forms"].keys():
        lst = tickets_data.setdefault("access_roles", {}).setdefault(form_id, [])
        if str(role.id) not in [str(x) for x in lst]:
            lst.append(str(role.id))
    save_tickets_data()
    await ctx.send(embed=Embed(title="✅ Доступ выдан", description=f"{role.mention} может просматривать тикеты.", color=0x00FF00))


@bot.command(name="тикетнероль")
@commands.has_permissions(administrator=True)
async def тикетнероль(ctx, role: discord.Role):
    changed = False
    for form_id, lst in tickets_data.setdefault("access_roles", {}).items():
        if str(role.id) in [str(x) for x in lst]:
            tickets_data["access_roles"][form_id] = [str(x) for x in lst if str(x) != str(role.id)]
            changed = True
    save_tickets_data()
    await ctx.send(embed=Embed(title="✅ Обновлено", description=(f"{role.mention} больше не может просматривать тикеты." if changed else "Роль не найдена в доступах."), color=0x00FF00))


@bot.command(name="тикетроли")
@commands.has_permissions(administrator=True)
async def тикетроли(ctx):
    forms = tickets_data.get("forms", {})
    if not forms:
        await ctx.send(embed=Embed(title="ℹ️ Тикеты", description="Нет форм тикетов.", color=0x3498DB))
        return
    lines = []
    for form_id, form in forms.items():
        role_mentions = []
        for rid in tickets_data.get("access_roles", {}).get(form_id, []):
            role = ctx.guild.get_role(int(rid))
            if role:
                role_mentions.append(role.mention)
        lines.append(f"**{form['name']}** — {', '.join(role_mentions) if role_mentions else 'нет ролей'}")
    await ctx.send(embed=Embed(title="🎫 Роли доступа к тикетам", description="\n".join(lines), color=0x3498DB))


@bot.command(name="удалитьтикет")
@commands.has_permissions(administrator=True)
async def удалитьтикет(ctx, *, ticket_ref: str):
    forms = tickets_data.get("forms", {})
    if not forms:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Нет форм тикетов для удаления.", color=0xFF0000))
        return

    raw_ref = ticket_ref.strip()
    normalized_ref = raw_ref.casefold()
    matched_id = None

    if raw_ref in forms:
        matched_id = raw_ref
    else:
        for form_id, form in forms.items():
            if form.get("name", "").casefold() == normalized_ref:
                matched_id = form_id
                break

    if matched_id is None:
        close_matches = []
        for form_id, form in forms.items():
            form_name = form.get("name", "")
            if normalized_ref in form_name.casefold():
                close_matches.append(f"`{form_id}` — {form_name}")

        hint = ""
        if close_matches:
            hint = "\n\nВозможные совпадения:\n" + "\n".join(close_matches[:10])

        await ctx.send(
            embed=Embed(
                title="❌ Форма не найдена",
                description=f"Не удалось найти тикет по значению: `{raw_ref}`.{hint}",
                color=0xFF0000,
            )
        )
        return

    removed_form = forms.pop(matched_id)
    tickets_data.setdefault("access_roles", {}).pop(matched_id, None)
    save_tickets_data()

    await ctx.send(
        embed=Embed(
            title="🗑️ Форма тикета удалена",
            description=f"Удалена форма **{removed_form.get('name', 'Без названия')}** (ID: `{matched_id}`).",
            color=0x00FF00,
        )
    )


# ================== SECRET NEGOTIATIONS ==================
def resolve_member_query(guild: discord.Guild, query: str):
    token = (query or "").strip()
    if not token:
        return None

    # mention / id
    digits = token
    if token.startswith("<@") and token.endswith(">"):
        digits = token.replace("<@", "").replace("!", "").replace(">", "")
    if digits.isdigit():
        member = guild.get_member(int(digits))
        if member:
            return member

    q = token.casefold()
    exact = [m for m in guild.members if m.name.casefold() == q or m.display_name.casefold() == q]
    if len(exact) == 1:
        return exact[0]

    contains = [m for m in guild.members if q in m.name.casefold() or q in m.display_name.casefold()]
    if len(contains) == 1:
        return contains[0]

    return None


class NegotiationRoomView(View):
    def __init__(self, organizer_id: int):
        super().__init__(timeout=None)
        self.organizer_id = int(organizer_id)

    @discord.ui.button(label="Закончить переговоры", style=ButtonStyle.danger)
    async def finish(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.organizer_id:
            await interaction.response.send_message("❌ Только организатор может закончить переговоры.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Переговоры завершены. Канал удаляется...", ephemeral=True)
        try:
            await interaction.channel.delete(reason=f"Переговоры завершены организатором {interaction.user}")
        except Exception:
            pass

    @discord.ui.button(label="Выйти с переговоров", style=ButtonStyle.secondary)
    async def leave(self, interaction: Interaction, button: Button):
        channel = interaction.channel
        await channel.set_permissions(
            interaction.user,
            view_channel=False,
            send_messages=False,
            read_message_history=False,
            reason=f"Участник вышел из переговоров: {interaction.user}",
        )
        await interaction.response.send_message("Вы вышли из переговоров. Доступ к каналу закрыт.", ephemeral=True)


class NegotiationCreateModal(Modal):
    def __init__(self):
        super().__init__(title="Тайные переговоры", timeout=600)
        self.participants = TextInput(
            label="Участники (через запятую)",
            placeholder="@chibrik, bremenski, krutoj",
            required=True,
            max_length=400,
        )
        self.topic = TextInput(
            label="Тема переговоров",
            placeholder="План раздела",
            required=True,
            max_length=200,
        )
        self.add_item(self.participants)
        self.add_item(self.topic)

    async def on_submit(self, interaction: Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ Команда доступна только на сервере.", ephemeral=True)
            return

        raw_names = [x.strip() for x in self.participants.value.split(",") if x.strip()]
        if not raw_names:
            await interaction.response.send_message("❌ Укажите хотя бы одного участника.", ephemeral=True)
            return

        unresolved = []
        members = []
        seen_ids = set()
        for token in raw_names:
            member = resolve_member_query(guild, token)
            if not member:
                unresolved.append(token)
                continue
            if member.id not in seen_ids:
                seen_ids.add(member.id)
                members.append(member)

        if unresolved:
            await interaction.response.send_message(
                f"❌ Не удалось найти участников: {', '.join(unresolved)}", ephemeral=True
            )
            return

        organizer = interaction.user
        if organizer.id not in seen_ids:
            members.append(organizer)
            seen_ids.add(organizer.id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
        }
        for m in members:
            overwrites[m] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        category = interaction.channel.category if interaction.channel else None
        channel_name = f"переговоры-{organizer.display_name}".lower().replace(" ", "-")[:90]
        room = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        ping_line = " ".join(m.mention for m in members)
        embed = Embed(title="🤝 Тайные переговоры", description=f"**Главная тема переговоров:** {self.topic.value}", color=0x3498DB)
        embed.add_field(name="Организатор", value=organizer.mention, inline=False)

        await room.send(content=ping_line, embed=embed, view=NegotiationRoomView(organizer.id))
        await interaction.response.send_message(
            embed=Embed(title="✅ Переговоры назначены", description=f"Канал создан: {room.mention}", color=0x00FF00),
            ephemeral=True,
        )


class NegotiationPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Назначить переговоры", style=ButtonStyle.primary)
    async def create(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(NegotiationCreateModal())


@bot.command(name="тайнканал")
@commands.has_permissions(administrator=True)
async def тайнканал(ctx, channel: discord.TextChannel):
    panel = NegotiationPanelView()
    embed = Embed(
        title="🕵️ Тайные переговоры",
        description="Нажмите кнопку ниже, чтобы назначить тайные переговоры.",
        color=0x3498DB,
    )
    await channel.send(embed=embed, view=panel)
    await ctx.send(embed=Embed(title="✅ Готово", description=f"Панель переговоров отправлена в {channel.mention}", color=0x00FF00))


class RatingModal(Modal):
    def __init__(self, target_id: str):
        self.target_id = str(target_id)
        super().__init__(title="Оценка администрации", timeout=300)
        self.role_input = TextInput(label="Назначение участника", required=True, max_length=120)
        self.score_input = TextInput(label="Оценка (1-10)", required=True, max_length=2)
        self.comment_input = TextInput(label="Комментарий", required=True, style=discord.TextStyle.paragraph, max_length=1000)
        self.add_item(self.role_input)
        self.add_item(self.score_input)
        self.add_item(self.comment_input)

    async def on_submit(self, interaction: Interaction):
        target = interaction.guild.get_member(int(self.target_id)) if interaction.guild else None
        if not target:
            await interaction.response.send_message("❌ Администратор не найден.", ephemeral=True)
            return

        now_ts = int(time.time())
        voter_id = str(interaction.user.id)
        last_vote = int(ratings_data.setdefault("last_vote", {}).get(voter_id, 0))
        if now_ts - last_vote < 4 * 3600:
            await interaction.response.send_message(f"⏳ Повторная оценка доступна через {format_seconds_left(4*3600 - (now_ts - last_vote))}.", ephemeral=True)
            return

        try:
            score = int(str(self.score_input.value).strip())
            if score < 1 or score > 10:
                raise ValueError
        except Exception:
            await interaction.response.send_message("❌ Оценка должна быть числом от 1 до 10.", ephemeral=True)
            return

        ratings_data.setdefault("last_vote", {})[voter_id] = now_ts
        target_votes = ratings_data.setdefault("votes", {}).setdefault(str(target.id), [])
        target_votes.append({
            "from": voter_id,
            "score": score,
            "comment": str(self.comment_input.value),
            "role_text": str(self.role_input.value),
            "time": now_ts,
        })
        save_ratings_data()

        channel = interaction.guild.get_channel(int(ratings_data.get("channel_id"))) if ratings_data.get("channel_id") else None
        if channel:
            embed = Embed(title="📝 Новая оценка", color=0x3498DB)
            embed.add_field(name="Оценка от", value=interaction.user.mention, inline=False)
            embed.add_field(name="Назначение", value=str(self.role_input.value), inline=False)
            embed.add_field(name="Оценка", value=f"{score}/10", inline=True)
            embed.add_field(name="Комментарий", value=str(self.comment_input.value), inline=False)
            try:
                await channel.send(content=target.mention, embed=embed)
            except Exception:
                pass

        await interaction.response.send_message("✅ Оценка отправлена.", ephemeral=True)


class RatingSelect(Select):
    def __init__(self, guild: discord.Guild):
        options = []
        for uid in ratings_data.get("targets", [])[:25]:
            m = guild.get_member(int(uid))
            if m:
                options.append(SelectOption(label=m.display_name, value=str(m.id)))
        super().__init__(placeholder="Выберите администратора", min_values=1, max_values=1, options=options or [SelectOption(label="Список пуст", value="0")])

    async def callback(self, interaction: Interaction):
        if self.values[0] == "0":
            await interaction.response.send_message("Список для оценок пуст.", ephemeral=True)
            return
        await interaction.response.send_modal(RatingModal(self.values[0]))


class RatingsPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Оценить администратора", style=ButtonStyle.primary)
    async def open(self, interaction: Interaction, button: Button):
        view = View(timeout=120)
        view.add_item(RatingSelect(interaction.guild))
        await interaction.response.send_message("Выберите администратора из списка:", view=view, ephemeral=True)


@bot.command(name="оценкиканал")
@commands.has_permissions(administrator=True)
async def оценкиканал(ctx, channel: discord.TextChannel):
    ratings_data["channel_id"] = channel.id
    save_ratings_data()
    panel_embed = Embed(title="⭐ Оценка администрации", description="Нажмите кнопку ниже, чтобы оценить администратора.", color=0x3498DB)
    await channel.send(embed=panel_embed, view=RatingsPanelView())
    await ctx.send(embed=Embed(title="✅ Канал оценок установлен", description=f"Канал: {channel.mention}", color=0x00FF00))


@bot.command(name="оценкаадмина")
@commands.has_permissions(administrator=True)
async def оценкаадмина(ctx, *, members_csv: str):
    ids = []
    for token in members_csv.split(","):
        raw = token.strip()
        if not raw:
            continue
        member = resolve_member_query(ctx.guild, raw)
        if member:
            ids.append(str(member.id))
    ratings_data["targets"] = list(dict.fromkeys(ids))
    save_ratings_data()
    mentions = [ctx.guild.get_member(int(uid)).mention for uid in ratings_data["targets"] if ctx.guild.get_member(int(uid))]
    await ctx.send(embed=Embed(title="✅ Список оценок обновлён", description=(", ".join(mentions) if mentions else "Список пуст."), color=0x00FF00))


@bot.command(name="мойстат")
async def мойстат(ctx):
    uid = str(ctx.author.id)
    if uid not in ratings_data.get("targets", []):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Вы не являетесь уполномоченным участником системы оценок.", color=0xFF0000))
        return

    votes = ratings_data.setdefault("votes", {}).get(uid, [])
    if not votes:
        await ctx.send(embed=Embed(title="📊 Мой стат", description="Оценок пока нет.", color=0x3498DB))
        return
    avg = sum(int(v.get("score", 0)) for v in votes) / len(votes)
    await ctx.send(embed=Embed(title="📊 Мой стат", description=f"Средняя оценка: **{avg:.2f}/10**\nВсего оценок: **{len(votes)}**", color=0x3498DB))


# ================== PASSIVE INCOME / EXPENSE ==================
async def _setup_passive_flow(ctx, flow_type: str):
    title = "пассивного дохода" if flow_type == "income" else "пассивного расхода"

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(embed=Embed(title="⚙️ Настройка", description=f"Укажите игрока для {title} (mention).", color=0x3498DB))

    try:
        msg_member = await bot.wait_for("message", check=check, timeout=180)
        converter = commands.MemberConverter()
        member = await converter.convert(ctx, msg_member.content.strip())
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Не удалось определить игрока.", color=0xFF0000))
        return

    await ctx.send(embed=Embed(title="⚙️ Настройка", description=f"Укажите сумму {title}.", color=0x3498DB))
    try:
        msg_amount = await bot.wait_for("message", check=check, timeout=180)
        amount_raw = msg_amount.content.strip()
        parsed_preview = parse_money_value(amount_raw, 100)
        if parsed_preview <= 0:
            raise ValueError
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сумма должна быть числом или % > 0 (пример: `500` или `10%`).", color=0xFF0000))
        return

    await ctx.send(embed=Embed(title="⚙️ Настройка", description=f"Укажите кулдаун {title} (например: 24ч, 30м, 10с).", color=0x3498DB))
    try:
        msg_cd = await bot.wait_for("message", check=check, timeout=180)
        cooldown = parse_interval(msg_cd.content.strip())
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Неверный формат времени. Пример: 24ч / 30м / 10с / 1д.", color=0xFF0000))
        return

    await ctx.send(embed=Embed(title="⚙️ Настройка", description="Укажите описание (например: аренда, налоги, дотация).", color=0x3498DB))
    try:
        msg_desc = await bot.wait_for("message", check=check, timeout=180)
        description = msg_desc.content.strip() or "без описания"
    except Exception:
        description = "без описания"

    await ctx.send(
        embed=Embed(
            title="⚙️ Настройка",
            description=(
                "На сколько времени выдать эту пассивную операцию?\n"
                "Пример: `7д`, `24ч`, `30м`.\n"
                "Если без срока — введите `скип`."
            ),
            color=0x3498DB,
        )
    )
    try:
        msg_ttl = await bot.wait_for("message", check=check, timeout=180)
        raw_ttl = msg_ttl.content.strip().lower()
        if raw_ttl == "скип":
            expires_at = None
        else:
            ttl_seconds = parse_interval(raw_ttl)
            expires_at = int(time.time()) + ttl_seconds
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Неверный формат срока действия. Используйте `7д`, `24ч` или `скип`.", color=0xFF0000))
        return

    ensure_user(str(member.id))
    entry = {
        "id": f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
        "type": flow_type,
        "amount": amount_raw,
        "cooldown": cooldown,
        "last_run": int(time.time()),
        "created_by": str(ctx.author.id),
        "description": description,
        "expires_at": expires_at,
    }
    get_passive_entries(str(member.id)).append(entry)
    save_passive_flows()

    action_word = "Доход" if flow_type == "income" else "Расход"
    await ctx.send(
        embed=Embed(
            title=f"✅ Пассивный {action_word.lower()} создан",
            description=(
                f"**Игрок:** {member.mention}\n\n"
                f"**{action_word}:** {amount_raw} раз в {format_interval(cooldown)}\n\n"
                f"**Описание:** {description}\n"
                f"**Срок действия:** {('∞' if expires_at is None else format_interval(max(0, expires_at - int(time.time()))))}"
            ),
            color=0x00FF00,
        )
    )


@bot.command(name="пасдоход")
@commands.has_permissions(administrator=True)
async def пасдоход(ctx):
    await _setup_passive_flow(ctx, "income")


@bot.command(name="пасрасход")
@commands.has_permissions(administrator=True)
async def пасрасход(ctx):
    await _setup_passive_flow(ctx, "expense")


async def _remove_passive_flow(ctx, flow_type: str, number: int):
    if number <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Номер должен быть больше 0.", color=0xFF0000))
        return

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    flow_label = "доход" if flow_type == "income" else "расход"
    await ctx.send(embed=Embed(title="⚙️ Удаление", description=f"Укажите игрока, у которого убрать пассивный {flow_label} №{number}.", color=0x3498DB))

    try:
        msg_member = await bot.wait_for("message", check=check, timeout=180)
        converter = commands.MemberConverter()
        member = await converter.convert(ctx, msg_member.content.strip())
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Не удалось определить игрока.", color=0xFF0000))
        return

    user_id = str(member.id)
    entries = get_passive_entries(user_id)
    typed_entries = [e for e in entries if e.get("type") == flow_type]

    if not typed_entries:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У игрока нет пассивных операций типа: {flow_label}.", color=0xFF0000))
        return

    if number > len(typed_entries):
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Такого номера нет. Доступно: 1..{len(typed_entries)}.", color=0xFF0000))
        return

    target_entry = typed_entries[number - 1]
    entries.remove(target_entry)
    save_passive_flows()

    await ctx.send(
        embed=Embed(
            title="✅ Пассивная операция удалена",
            description=(
                f"**Игрок:** {member.mention}\n\n"
                f"**Тип:** {flow_label}\n"
                f"**Сумма:** {target_entry.get('amount', 0)} {currency}\n"
                f"**Период:** {format_interval(int(target_entry.get('cooldown', 0)))}\n"
                f"**Описание:** {target_entry.get('description', 'без описания')}\n"
                f"**Срок действия:** "
                f"{('∞' if target_entry.get('expires_at') is None else format_seconds_left(int(target_entry.get('expires_at')) - int(time.time())))}"
            ),
            color=0x00FF00,
        )
    )


@bot.command(name="пасдоходубрать")
@commands.has_permissions(administrator=True)
async def пасдоходубрать(ctx, number: int):
    await _remove_passive_flow(ctx, "income", number)


@bot.command(name="пасрасходубрать")
@commands.has_permissions(administrator=True)
async def пасрасходубрать(ctx, number: int):
    await _remove_passive_flow(ctx, "expense", number)


@bot.command(name="регроли")
@commands.has_permissions(administrator=True)
async def регроли(ctx):
    class RegRolesView(View):
        def __init__(self, author_id: int):
            super().__init__(timeout=180)
            self.author_id = author_id

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("❌ Только автор команды может менять настройки.", ephemeral=True)
                return False
            return True

        async def _handle(self, interaction: Interaction, key: str, action_name: str):
            await interaction.response.send_message(
                embed=Embed(title="📝 Ввод ролей", description="Укажите роли через запятую (упоминания).", color=0x3498DB),
                ephemeral=True,
            )

            def check(m):
                return m.author.id == self.author_id and m.channel.id == interaction.channel_id

            try:
                msg = await bot.wait_for("message", check=check, timeout=180)
            except Exception:
                return

            role_ids = []
            for token in msg.content.split(","):
                raw = token.strip()
                if not raw:
                    continue
                try:
                    role = await commands.RoleConverter().convert(ctx, raw)
                    role_ids.append(str(role.id))
                except Exception:
                    continue

            reg_settings[key] = list(dict.fromkeys(role_ids))
            if key == "roles_add":
                reg_settings["roles"] = reg_settings[key]
            save_reg_settings()
            mentions = [ctx.guild.get_role(int(rid)).mention for rid in reg_settings[key] if ctx.guild.get_role(int(rid))]
            await interaction.followup.send(embed=Embed(title=f"✅ {action_name}", description=(", ".join(mentions) if mentions else "Список пуст."), color=0x00FF00), ephemeral=True)

        @discord.ui.button(label="Добавить роли", style=ButtonStyle.success)
        async def add_roles(self, interaction: Interaction, button: Button):
            await self._handle(interaction, "roles_add", "Роли выдачи при !рег обновлены")

        @discord.ui.button(label="Снять роли", style=ButtonStyle.danger)
        async def remove_roles(self, interaction: Interaction, button: Button):
            await self._handle(interaction, "roles_remove", "Роли снятия при !рег обновлены")

    current_add = [ctx.guild.get_role(int(rid)).mention for rid in reg_settings.get("roles_add", []) if ctx.guild.get_role(int(rid))]
    current_remove = [ctx.guild.get_role(int(rid)).mention for rid in reg_settings.get("roles_remove", []) if ctx.guild.get_role(int(rid))]
    await ctx.send(
        embed=Embed(
            title="⚙️ Настройка !регроли",
            description=(
                f"**Выдавать при !рег:** {', '.join(current_add) if current_add else '—'}\n"
                f"**Снимать при !рег:** {', '.join(current_remove) if current_remove else '—'}"
            ),
            color=0x3498DB,
        ),
        view=RegRolesView(ctx.author.id),
    )


@bot.command(name="вайпроли")
@commands.has_permissions(administrator=True)
async def вайпроли(ctx, *, roles_csv: str):
    role_ids = []
    for token in roles_csv.split(","):
        raw = token.strip()
        if not raw:
            continue
        try:
            role = await commands.RoleConverter().convert(ctx, raw)
            role_ids.append(str(role.id))
        except Exception:
            continue
    reg_settings["wipe_roles"] = list(dict.fromkeys(role_ids))
    save_reg_settings()
    mentions = [ctx.guild.get_role(int(rid)).mention for rid in reg_settings["wipe_roles"] if ctx.guild.get_role(int(rid))]
    await ctx.send(embed=Embed(title="✅ Вайп-роли обновлены", description=(", ".join(mentions) if mentions else "Список пуст."), color=0x00FF00))


@bot.command(name="счастьестоп")
@commands.has_permissions(administrator=True)
async def счастьестоп(ctx, member: discord.Member, duration: str):
    try:
        secs = parse_interval(duration)
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Неверный формат времени: {e}", color=0xFF0000))
        return
    st = ensure_player_state(str(member.id))
    st["happiness_pause_until"] = max(int(st.get("happiness_pause_until", 0)), int(time.time()) + secs)
    save_player_state()
    await ctx.send(embed=Embed(title="✅ Счастье на паузе", description=f"Для {member.mention}: {format_interval(secs)}", color=0x00FF00))


@bot.command(name="счастьевыдать")
@commands.has_permissions(administrator=True)
async def счастьевыдать(ctx, member: discord.Member, amount: str):
    st = ensure_player_state(str(member.id))
    current = int(st.get("happiness", 50))
    try:
        if str(amount).strip().endswith("%"):
            val = int(str(amount).strip().replace("%", ""))
        else:
            val = int(float(amount))
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Введите число или процент (например `70` или `70%`).", color=0xFF0000))
        return
    st["happiness"] = max(0, min(100, val))
    save_player_state()
    await ctx.send(embed=Embed(title="✅ Счастье обновлено", description=f"{member.mention}: {current}% → {st['happiness']}%", color=0x00FF00))


@bot.command(name="мобилизировать")
async def мобилизировать(ctx, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Число должно быть больше 0.", color=0xFF0000))
        return
    user_id = str(ctx.author.id)
    pop = load_json(POPULATION_FILE, {})
    population = int(pop.get(user_id, 0))
    st = ensure_player_state(user_id)
    soldiers = int(st.get("soldiers", 0))
    total = population + soldiers
    max_allowed = int(total * 0.3)
    if soldiers + amount > max_allowed:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Лимит мобилизации: {max_allowed} солдат (30% от общего).", color=0xFF0000))
        return
    if amount > population:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Недостаточно населения для мобилизации.", color=0xFF0000))
        return

    user = ensure_user(user_id)
    war = bool(st.get("war_mode", False))
    per_cost = 50 if war else 20
    total_cost = per_cost * amount
    if get_available_cash(user) < total_cost:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Недостаточно денег. Нужно {total_cost} {currency}.", color=0xFF0000))
        return

    user["наличка"] -= total_cost
    pop[user_id] = population - amount
    st["soldiers"] = soldiers + amount
    st["last_mobilization_cost_tick"] = int(time.time())
    save_json(BALANCES_FILE, balances)
    save_json(POPULATION_FILE, pop)
    save_player_state()
    await ctx.send(embed=Embed(title="🪖 Мобилизация", description=f"Мобилизовано: {amount}\nСтоимость: {total_cost} {currency}", color=0x00FF00))


@bot.command(name="распустить")
async def распустить(ctx, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Число должно быть больше 0.", color=0xFF0000))
        return
    user_id = str(ctx.author.id)
    st = ensure_player_state(user_id)
    soldiers = int(st.get("soldiers", 0))
    if amount > soldiers:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У вас только {soldiers} солдат.", color=0xFF0000))
        return
    pop = load_json(POPULATION_FILE, {})
    pop[user_id] = int(pop.get(user_id, 0)) + amount
    st["soldiers"] = soldiers - amount
    save_json(POPULATION_FILE, pop)
    save_player_state()
    await ctx.send(embed=Embed(title="✅ Распуск", description=f"Распущено {amount} солдат обратно в население.", color=0x00FF00))


@bot.group(name="население", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def население(ctx):
    await ctx.send(embed=Embed(title="ℹ️ Формат команды", description="`!население начислить @игрок <количество>`\n`!население забрать @игрок <количество>`", color=0x3498DB))


@население.command(name="начислить")
@commands.has_permissions(administrator=True)
async def население_начислить(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return

    pop = load_json(POPULATION_FILE, {})
    user_id = str(member.id)
    old_value = int(pop.get(user_id, 0))
    pop[user_id] = old_value + amount
    save_json(POPULATION_FILE, pop)

    await ctx.send(
        embed=Embed(
            title="✅ Население начислено",
            description=(
                f"Игрок: {member.mention}\n"
                f"Было: **{old_value}**\n"
                f"Начислено: **{amount}**\n"
                f"Стало: **{pop[user_id]}**"
            ),
            color=0x00FF00,
        )
    )


@население.command(name="забрать")
@commands.has_permissions(administrator=True)
async def население_забрать(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return

    pop = load_json(POPULATION_FILE, {})
    user_id = str(member.id)
    old_value = int(pop.get(user_id, 0))
    new_value = max(0, old_value - amount)
    pop[user_id] = new_value
    save_json(POPULATION_FILE, pop)

    await ctx.send(
        embed=Embed(
            title="✅ Население уменьшено",
            description=(
                f"Игрок: {member.mention}\n"
                f"Было: **{old_value}**\n"
                f"Списано: **{old_value - new_value}**\n"
                f"Стало: **{new_value}**"
            ),
            color=0x00FF00,
        )
    )


@bot.group(name="солдаты", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def солдаты(ctx):
    await ctx.send(embed=Embed(title="ℹ️ Формат команды", description="`!солдаты начислить @игрок <количество>`\n`!солдаты забрать @игрок <количество>`", color=0x3498DB))


@солдаты.command(name="начислить")
@commands.has_permissions(administrator=True)
async def солдаты_начислить(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return

    state = ensure_player_state(str(member.id))
    old_value = int(state.get("soldiers", 0))
    state["soldiers"] = old_value + amount
    save_player_state()

    await ctx.send(
        embed=Embed(
            title="✅ Солдаты начислены",
            description=(
                f"Игрок: {member.mention}\n"
                f"Было: **{old_value}**\n"
                f"Начислено: **{amount}**\n"
                f"Стало: **{state['soldiers']}**"
            ),
            color=0x00FF00,
        )
    )


@солдаты.command(name="забрать")
@commands.has_permissions(administrator=True)
async def солдаты_забрать(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return

    state = ensure_player_state(str(member.id))
    old_value = int(state.get("soldiers", 0))
    new_value = max(0, old_value - amount)
    state["soldiers"] = new_value
    save_player_state()

    await ctx.send(
        embed=Embed(
            title="✅ Солдаты уменьшены",
            description=(
                f"Игрок: {member.mention}\n"
                f"Было: **{old_value}**\n"
                f"Списано: **{old_value - new_value}**\n"
                f"Стало: **{new_value}**"
            ),
            color=0x00FF00,
        )
    )

class BroadcastConfirmView(View):
    def __init__(self, author_id: int, guild_id: int, message_text: str):
        super().__init__(timeout=120)
        self.author_id = int(author_id)
        self.guild_id = int(guild_id)
        self.message_text = message_text

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Только автор команды может подтвердить/отменить рассылку.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Подтвердить", style=ButtonStyle.success)
    async def confirm(self, interaction: Interaction, button: Button):
        guild = bot.get_guild(self.guild_id)
        if guild is None:
            await interaction.response.edit_message(
                embed=Embed(title="❌ Ошибка", description="Сервер не найден.", color=0xFF0000),
                view=None,
            )
            self.stop()
            return

        await interaction.response.edit_message(
            embed=Embed(title="📨 Рассылка", description="Рассылка запущена...", color=0x3498DB),
            view=None,
        )

        dm_embed = Embed(title="📢 Объявление", description=self.message_text, color=0x3498DB)
        sent_count = 0
        fail_count = 0

        for member in guild.members:
            if member.bot:
                continue
            try:
                await member.send(embed=dm_embed)
                sent_count += 1
            except Exception:
                fail_count += 1

        await interaction.followup.send(
            embed=Embed(
                title="✅ Рассылка завершена",
                description=(
                    f"Успешно отправлено: **{sent_count}**\n"
                    f"Не удалось отправить: **{fail_count}**"
                ),
                color=0x00FF00,
            ),
            ephemeral=True,
        )
        self.stop()

    @discord.ui.button(label="❌ Отменить", style=ButtonStyle.secondary)
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(
            embed=Embed(title="❎ Рассылка отменена", description="Команда откатена, сообщения не отправлялись.", color=0x808080),
            view=None,
        )
        self.stop()


@bot.command(name="рассылка")
@commands.has_permissions(administrator=True)
async def рассылка(ctx, *, message_text: str):
    message_text = message_text.strip()
    if not message_text:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Введите текст объявления.", color=0xFF0000))
        return

    preview_embed = Embed(
        title="📨 Предпросмотр рассылки",
        description=message_text,
        color=0x3498DB,
    )
    preview_embed.set_footer(text="Нажмите 'Подтвердить' для отправки всем участникам сервера в ЛС.")
    await ctx.send(embed=preview_embed, view=BroadcastConfirmView(ctx.author.id, ctx.guild.id, message_text))


def save_country_owners():
    save_json(COUNTRY_OWNERS_FILE, country_owners)


def resolve_country_name(raw_country: str):
    if raw_country in country_stats:
        return raw_country
    q = str(raw_country).strip().casefold()
    for name in country_stats.keys():
        if str(name).casefold() == q:
            return name
    return None


def get_country_type(country_name: str) -> str:
    data = country_stats.get(country_name)
    if isinstance(data, dict):
        ctype = data.get("type")
        if isinstance(ctype, str) and ctype.strip():
            return ctype.strip()
    return "Государство"


def get_country_population_for_season(country_name: str, season_name: str):
    data = country_stats.get(country_name)
    if not isinstance(data, dict):
        return None

    season_key = str(season_name)
    seasons_map = data.get("seasons")
    if isinstance(seasons_map, dict) and season_key in seasons_map:
        return seasons_map.get(season_key)

    if season_key in data and isinstance(data.get(season_key), int):
        return data.get(season_key)

    return None


def set_country_population_for_season(country_name: str, season_name: str, population_value: int, country_type: str = None):
    record = country_stats.setdefault(country_name, {})
    if not isinstance(record, dict):
        record = {}
        country_stats[country_name] = record

    record.setdefault("seasons", {})
    if not isinstance(record.get("seasons"), dict):
        record["seasons"] = {}
    record["seasons"][str(season_name)] = int(population_value)

    if country_type:
        record["type"] = country_type


def get_occupied_country_map():
    country_to_user = country_owners.setdefault("country_to_user", {})
    user_to_country = country_owners.setdefault("user_to_country", {})

    # Ленивая синхронизация из player_stats для старых данных
    players = load_json(PLAYER_STATS_FILE, {})
    changed = False
    for uid, pdata in players.items():
        if not isinstance(pdata, dict) or not pdata:
            continue
        current = user_to_country.get(str(uid))
        if current:
            continue
        first_country = next(iter(pdata.keys()), None)
        if not first_country:
            continue
        if first_country not in country_to_user:
            user_to_country[str(uid)] = first_country
            country_to_user[first_country] = str(uid)
            changed = True

    if changed:
        save_country_owners()

    return country_to_user, user_to_country



def save_moderation_data():
    save_json(MODERATION_FILE, moderation_data)


def get_warn_entries(user_id: str):
    return moderation_data.setdefault("warns", {}).setdefault(user_id, [])


async def send_mod_log(guild: discord.Guild, embed: Embed):
    channel_id = moderation_data.get("log_channel")
    if not channel_id:
        return
    channel = guild.get_channel(int(channel_id)) if guild else None
    if channel:
        try:
            await channel.send(embed=embed)
        except Exception:
            pass


async def resolve_target_member_from_payload(ctx, payload: str):
    import shlex

    raw = (payload or "").strip()

    try:
        parts = shlex.split(raw)
    except Exception:
        parts = raw.split()

    if not parts:
        return None, None, None

    reply_author = None
    if ctx.message.reference and ctx.message.reference.message_id:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            reply_author = ref_msg.author if ref_msg else None
        except Exception:
            reply_author = None

    # Режим ответа на сообщение без дополнительных аргументов: !бан / !кик / !варн / !мут
    if not raw:
        if reply_author is not None:
            return reply_author, None, "Не указана"
        return None, None, None

    converter = commands.MemberConverter()

    def _is_duration_token(token: str) -> bool:
        try:
            parse_interval(token)
            return True
        except Exception:
            return False

    # Режим ответа на сообщение
    if reply_author is not None:
        if not parts:
            return None, None, None
        duration = parts[0] if _is_duration_token(parts[0]) else None
        reason = " ".join(parts[1:] if duration else parts).strip() or "Не указана"
        return reply_author, duration, reason

    # Обычный режим
    if len(parts) < 1:
        return None, None, None

    try:
        member = await converter.convert(ctx, parts[0])
    except Exception:
        return None, None, None

    duration = parts[1] if len(parts) > 1 and _is_duration_token(parts[1]) else None
    reason = " ".join(parts[2:] if duration else parts[1:]).strip() or "Не указана"
    return member, duration, reason


async def resolve_member_reason_from_payload(ctx, payload: str):
    import shlex

    raw = (payload or "").strip()
    if not raw:
        if ctx.message.reference and ctx.message.reference.message_id:
            try:
                ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                return (ref_msg.author if ref_msg else None), "Не указана"
            except Exception:
                return None, None
        return None, None

    try:
        parts = shlex.split(raw)
    except Exception:
        parts = raw.split()

    if not parts:
        return None, None

    reply_author = None
    if ctx.message.reference and ctx.message.reference.message_id:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            reply_author = ref_msg.author if ref_msg else None
        except Exception:
            reply_author = None

    converter = commands.MemberConverter()

    if reply_author is not None:
        reason = " ".join(parts).strip() or "Не указана"
        return reply_author, reason

    if len(parts) < 1:
        return None, None

    try:
        member = await converter.convert(ctx, parts[0])
    except Exception:
        return None, None

    reason = " ".join(parts[1:]).strip() or "Не указана"
    return member, reason


async def apply_warn_limit_action(ctx, member: discord.Member, action_text: str, trigger_reason: str):
    txt = (action_text or "").strip().lower()
    if not txt:
        return "нет действия"

    parts = txt.split()
    action = parts[0]

    if action == "мут":
        if len(parts) < 2:
            return "ошибка настройки: для мута нужен срок"
        try:
            secs = parse_interval(parts[1])
        except Exception:
            return "ошибка настройки: неверный срок мута"
        until = discord.utils.utcnow() + __import__('datetime').timedelta(seconds=secs)
        try:
            await member.timeout(until, reason=trigger_reason)
            return f"автомут на {format_interval(secs)}"
        except Exception:
            return "не удалось выдать автомут"

    if action == "кик":
        try:
            await member.kick(reason=trigger_reason)
            return "автокик"
        except Exception:
            return "не удалось выполнить автокик"

    if action == "бан":
        try:
            await member.ban(reason=trigger_reason, delete_message_days=0)
            return "автобан"
        except Exception:
            return "не удалось выполнить автобан"

    return "неизвестное действие"


@bot.command(name="модерлогканал")
@commands.has_permissions(administrator=True)
async def модерлогканал(ctx, channel: discord.TextChannel):
    moderation_data["log_channel"] = channel.id
    save_moderation_data()
    await ctx.send(embed=Embed(title="✅ Канал модлогов установлен", description=f"Логи будут отправляться в {channel.mention}", color=0x00FF00))


@bot.command(name="варнпредел")
@commands.has_permissions(administrator=True)
async def варнпредел(ctx, count: int, *, action: str):
    if count <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество варнов должно быть > 0.", color=0xFF0000))
        return

    moderation_data.setdefault("warn_limit", {})["count"] = int(count)
    moderation_data["warn_limit"]["action"] = action.strip()
    save_moderation_data()
    await ctx.send(embed=Embed(title="✅ Предел варнов обновлён", description=f"Предел: **{count}**\nНаказание: **{action.strip()}**", color=0x00FF00))


@bot.command(name="мут")
@commands.has_permissions(moderate_members=True)
async def мут(ctx, *, payload: str = ""):
    member, duration, reason = await resolve_target_member_from_payload(ctx, payload)
    if not member:
        await ctx.send(embed=Embed(title="❌ Формат", description="Использование: `!мут @игрок [срок] [причина]` или ответом: `!мут [срок] [причина]`", color=0xFF0000))
        return

    if duration:
        try:
            secs = parse_interval(duration)
        except Exception as e:
            await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Неверный срок: {e}", color=0xFF0000))
            return
    else:
        secs = 28 * 24 * 3600

    until = discord.utils.utcnow() + __import__('datetime').timedelta(seconds=secs)
    try:
        await member.timeout(until, reason=f"{ctx.author}: {reason}")
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Не удалось выдать таймаут: {e}", color=0xFF0000))
        return

    embed = Embed(title="🔇 Выдан мут", color=0xFFA500)
    embed.add_field(name="Нарушитель", value=member.mention, inline=False)
    embed.add_field(name="Срок", value=format_interval(secs), inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    await send_mod_log(ctx.guild, embed)


@bot.command(name="кик")
@commands.has_permissions(kick_members=True)
async def кик(ctx, *, payload: str = ""):
    member, duration, reason = await resolve_target_member_from_payload(ctx, payload)
    if not member:
        await ctx.send(embed=Embed(title="❌ Формат", description="Использование: `!кик @игрок [причина]` или ответом: `!кик [причина]`", color=0xFF0000))
        return

    try:
        await member.kick(reason=f"{ctx.author}: {reason}")
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Не удалось кикнуть: {e}", color=0xFF0000))
        return

    embed = Embed(title="👢 Выдан кик", color=0xFF8800)
    embed.add_field(name="Нарушитель", value=f"{member} (`{member.id}`)", inline=False)
    embed.add_field(name="Срок", value="—", inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    await send_mod_log(ctx.guild, embed)


@bot.command(name="бан")
@commands.has_permissions(ban_members=True)
async def бан(ctx, *, payload: str = ""):
    member, duration, reason = await resolve_target_member_from_payload(ctx, payload)
    if not member:
        await ctx.send(embed=Embed(title="❌ Формат", description="Использование: `!бан @игрок [причина]` или ответом: `!бан [причина]`", color=0xFF0000))
        return

    try:
        await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=0)
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Не удалось забанить: {e}", color=0xFF0000))
        return

    embed = Embed(title="⛔ Выдан бан", color=0xFF0000)
    embed.add_field(name="Нарушитель", value=f"{member} (`{member.id}`)", inline=False)
    embed.add_field(name="Срок", value="—", inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    await send_mod_log(ctx.guild, embed)


@bot.command(name="варн")
@commands.has_permissions(moderate_members=True)
async def варн(ctx, *, payload: str = ""):
    member, duration, reason = await resolve_target_member_from_payload(ctx, payload)
    if not member:
        await ctx.send(embed=Embed(title="❌ Формат", description="Использование: `!варн @игрок [причина]` или ответом: `!варн [причина]`", color=0xFF0000))
        return

    entry = {"moderator": str(ctx.author.id), "reason": reason, "duration": duration or "—", "ts": int(time.time())}
    warns = get_warn_entries(str(member.id))
    warns.append(entry)
    save_moderation_data()

    count = len(warns)
    limit_cfg = moderation_data.get("warn_limit", {})
    limit = int(limit_cfg.get("count", 3))
    action_text = str(limit_cfg.get("action", "мут 1ч"))

    action_result = None
    if limit > 0 and count % limit == 0:
        action_result = await apply_warn_limit_action(ctx, member, action_text, f"Автонаказание по варнам: {reason}")

    embed = Embed(title="⚠️ Выдан варн", color=0xFFD966)
    embed.add_field(name="Нарушитель", value=member.mention, inline=False)
    embed.add_field(name="Варнов", value=f"{count}", inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    if action_result:
        embed.add_field(name="Автонаказание", value=action_result, inline=False)
    await ctx.send(embed=embed)
    await send_mod_log(ctx.guild, embed)


@bot.command(name="размут")
@commands.has_permissions(moderate_members=True)
async def размут(ctx, *, payload: str):
    member, reason = await resolve_member_reason_from_payload(ctx, payload)
    if not member or not reason:
        await ctx.send(embed=Embed(title="❌ Формат", description="Использование: `!размут @игрок причина` или ответом: `!размут причина`", color=0xFF0000))
        return

    try:
        await member.timeout(None, reason=f"{ctx.author}: {reason}")
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Не удалось снять мут: {e}", color=0xFF0000))
        return

    embed = Embed(title="🔊 Мут снят", color=0x00FF00)
    embed.add_field(name="Участник", value=member.mention, inline=False)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    await send_mod_log(ctx.guild, embed)


@bot.command(name="разбан")
@commands.has_permissions(ban_members=True)
async def разбан(ctx, user_id: str, *, reason: str = "Не указана"):
    if not str(user_id).isdigit():
        await ctx.send(embed=Embed(title="❌ Формат", description="Использование: `!разбан <ID> причина`", color=0xFF0000))
        return

    uid = int(user_id)
    target_user = None
    try:
        bans = [entry async for entry in ctx.guild.bans(limit=None)]
        for entry in bans:
            if entry.user.id == uid:
                target_user = entry.user
                break
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Не удалось получить список банов: {e}", color=0xFF0000))
        return

    if target_user is None:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Пользователь с таким ID не найден в бан-листе.", color=0xFF0000))
        return

    try:
        await ctx.guild.unban(target_user, reason=f"{ctx.author}: {reason}")
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Не удалось разбанить: {e}", color=0xFF0000))
        return

    embed = Embed(title="✅ Разбан", color=0x00FF00)
    embed.add_field(name="Пользователь", value=f"{target_user} (`{target_user.id}`)", inline=False)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    await send_mod_log(ctx.guild, embed)


@bot.command(name="снятьварн")
@commands.has_permissions(moderate_members=True)
async def снятьварн(ctx, member: discord.Member, count: int = 1, *, reason: str = "Снято модератором"):
    if count <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return

    warns = get_warn_entries(str(member.id))
    if not warns:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="У участника нет варнов.", color=0xFF0000))
        return

    remove_n = min(count, len(warns))
    del warns[-remove_n:]
    save_moderation_data()

    embed = Embed(title="✅ Варн снят", color=0x00FF00)
    embed.add_field(name="Участник", value=member.mention, inline=False)
    embed.add_field(name="Снято варнов", value=str(remove_n), inline=True)
    embed.add_field(name="Осталось варнов", value=str(len(warns)), inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Модератор", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)
    await send_mod_log(ctx.guild, embed)


@bot.command(name="наказания")
@commands.has_permissions(moderate_members=True)
async def наказания(ctx):
    now_dt = discord.utils.utcnow()

    muted_lines = []
    for m in ctx.guild.members:
        end_dt = getattr(m, "timed_out_until", None) or getattr(m, "communication_disabled_until", None)
        if end_dt and end_dt > now_dt:
            left = int((end_dt - now_dt).total_seconds())
            muted_lines.append(f"• {m.mention} — ещё {format_seconds_left(left)}")

    warn_limit = int(moderation_data.get("warn_limit", {}).get("count", 3))
    warn_lines = []
    for uid, entries in moderation_data.get("warns", {}).items():
        if not entries:
            continue
        member = ctx.guild.get_member(int(uid))
        label = member.mention if member else f"<@{uid}>"
        count = len(entries)
        left_to_limit = warn_limit - (count % warn_limit) if warn_limit > 0 else 0
        if left_to_limit == 0 and warn_limit > 0:
            left_to_limit = warn_limit
        warn_lines.append(f"• {label} — варнов: **{count}**, до наказания: **{left_to_limit}**")

    desc = ""
    desc += "**Активные муты:**\n" + ("\n".join(muted_lines) if muted_lines else "нет")
    desc += "\n\n**Варны:**\n" + ("\n".join(warn_lines) if warn_lines else "нет")

    await ctx.send(embed=Embed(title="📋 Активные наказания", description=desc, color=0x3498DB))




# ================== ROLE INCOME ==================
@bot.command()
async def коллект(ctx):
    user_id = str(ctx.author.id)
    user = ensure_user(user_id)

    now = int(time.time())
    total_earned = 0
    collected_roles = []  # list[tuple[str, int]]
    cooldown_wait = []
    has_manual_income_role = False

    for rid, data in role_income.get("roles", {}).items():
        if data.get("auto", True):
            continue

        role = ctx.guild.get_role(int(rid))
        if not role or role not in ctx.author.roles:
            continue

        has_manual_income_role = True
        cooldown = int(data.get("cooldown", 0))
        last = role_income.get("last_claim", {}).get(user_id, {}).get(rid, 0)
        elapsed = now - last
        if elapsed < cooldown:
            cooldown_wait.append((role.mention, cooldown - elapsed))
            continue

        try:
            amount = parse_money_value(str(data.get("amount", 0)), user["наличка"])
        except Exception:
            amount = 0

        total_earned += amount
        collected_roles.append((role.mention, amount))
        role_income.setdefault("last_claim", {}).setdefault(user_id, {})[rid] = now

    investment_profit_total = 0
    investment_lines = []
    invs = ensure_investments(user_id)
    now_ts = int(time.time())
    for inv in invs:
        if inv.get("status") != "active":
            continue
        bank_key = inv.get("bank", "")
        bank_cfg = INVESTMENT_BANKS.get(bank_key, {})
        bank_name = inv.get("bank_name", bank_cfg.get("name", "Банк"))
        next_at = int(inv.get("next_at", now_ts))
        amount_inv = int(inv.get("amount", 0))
        if now_ts < next_at:
            investment_lines.append(f"• Вывод с {bank_name}: через {format_seconds_left(next_at - now_ts)}")
            continue

        if bank_key == "neo-bank" and random.random() < float(bank_cfg.get("delay_chance", 0)):
            inv["next_at"] = now_ts + 86400
            investment_lines.append(f"• Инвестиция с {bank_name} задержана на сутки")
            continue
        if bank_key == "fantom-bank" and random.random() < float(bank_cfg.get("burn_chance", 0)):
            inv["status"] = "burned"
            investment_lines.append(f"• {bank_name} вас обманул, инвестиция сгорела")
            continue

        profit = int(round(amount_inv * float(bank_cfg.get("profit_pct", 0)) / 100.0))
        investment_profit_total += profit
        inv["next_at"] = now_ts + 86400
        investment_lines.append(f"• Вывод с {bank_name}: +{fmt_money(profit)}")

    gross_income_pool = max(0, total_earned) + max(0, investment_profit_total)
    frozen_added, freeze_lines, _ = apply_freeze_roles_for_member(ctx.guild, ctx.author, now, gross_income_pool)
    final_cash_delta = total_earned + investment_profit_total - frozen_added
    user["наличка"] += final_cash_delta

    save_json(BALANCES_FILE, balances)
    save_json(ROLE_INCOME_FILE, role_income)
    save_investments()

    if not collected_roles and not freeze_lines and not investment_lines:
        if cooldown_wait:
            wait_lines = "\n".join(f"• {role_mention}: через {format_seconds_left(left)}" for role_mention, left in cooldown_wait)
            await ctx.send(
                embed=Embed(
                    title="⏳ Коллект на кулдауне",
                    description=f"{ctx.author.mention}, доход временно недоступен.\n\nСледующий сбор:\n{wait_lines}",
                    color=0xFFAA00,
                )
            )
            return

        if has_manual_income_role:
            await ctx.send(
                embed=Embed(
                    title="⚠️ Доход не начислен",
                    description=f"{ctx.author.mention}, роли найдены, но сумма начисления сейчас равна 0. Проверьте настройку дохода роли.",
                    color=0xFFAA00,
                )
            )
            return

        await ctx.send(
            embed=Embed(
                title="❌ Доход не доступен",
                description=f"{ctx.author.mention}, нет ролей с ручным доходом (`auto: false`) или они не назначены вам.",
                color=0xFF0000,
            )
        )
        return

    role_lines = "\n\n".join(f"• **{name}** — {fmt_money(amount)}" for name, amount in collected_roles)
    desc = f"{ctx.author.mention}, итог по коллекту: **{final_cash_delta:+,} {currency}**.\n\n**Роли с доходом:**\n{role_lines}".replace(",", ".")
    if freeze_lines:
        desc += f"\n\n**Заморозка средств:**\n" + "\n".join(freeze_lines)
        desc += f"\n\nИтого заморожено: **{fmt_money(frozen_added)}**"
    if investment_lines:
        desc += "\n\n**Инвестиции:**\n" + "\n".join(investment_lines)

    await ctx.send(embed=Embed(title="💰 Коллект выполнен", description=desc, color=0x00FF00))
    await log_economy_change(ctx.guild, ctx.author.id, "Коллект", cash_delta=final_cash_delta, frozen_delta=frozen_added)


@bot.command()
async def доходсписок(ctx):
    roles_cfg = role_income.setdefault("roles", {})
    if not roles_cfg:
        await ctx.send(embed=Embed(title="ℹ️ Доходы ролей", description="Список ролей дохода пуст.", color=0x3498DB))
        return

    lines = []
    for rid, data in roles_cfg.items():
        role = ctx.guild.get_role(int(rid))
        if role:
            lines.append(
                f"{role.mention} — {data['amount']} ({currency} / %), кулдаун {data['cooldown']}с, авто: {data.get('auto', True)}"
            )


    freeze_cfg = role_income.setdefault("freeze_roles", {})
    if freeze_cfg:
        lines.append("\n**🧊 Роли заморозки:**")
        for rid, data in freeze_cfg.items():
            role = ctx.guild.get_role(int(rid))
            if role:
                lines.append(
                    f"{role.mention} — заморозка {data.get('value', 0)}, кулдаун {data.get('cooldown', 0)}с"
                )
    await ctx.send(embed=Embed(title="💰 Роли дохода", description="\n".join(lines) or "Нет ролей.", color=0x3498DB))


class TopView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.mode = "economy"
        self.page = 0

    def _dataset(self):
        if self.mode == "population":
            pop = load_json(POPULATION_FILE, {})
            return sorted(((uid, int(pop.get(uid, 0))) for uid in pop.keys()), key=lambda x: x[1], reverse=True), "👥 Топ по населению"
        if self.mode == "army":
            users = player_state.get("users", {})
            return sorted(((uid, int((users.get(uid) or {}).get("soldiers", 0))) for uid in users.keys()), key=lambda x: x[1], reverse=True), "🪖 Топ по армии"
        data = []
        for uid, user in balances.items():
            if uid == "валюта" or not isinstance(user, dict):
                continue
            available_total = int(user.get("наличка", 0)) - int(user.get("заморожено", 0)) + int(user.get("банк", 0))
            data.append((uid, available_total))
        return sorted(data, key=lambda x: x[1], reverse=True), "💰 Топ по экономике"

    def build_embed(self):
        data, title = self._dataset()
        if not data:
            return Embed(title=title, description="Список пуст.", color=0x3498DB)
        pages = [data[i:i + 10] for i in range(0, len(data), 10)]
        self.page = max(0, min(self.page, len(pages) - 1))
        chunk = pages[self.page]
        desc = ""
        start = self.page * 10 + 1
        for idx, (uid, val) in enumerate(chunk, start=start):
            suffix = currency if self.mode == "economy" else ""
            desc += f"{idx}. <@{uid}> — {fmt_num(val)} {suffix}\n".rstrip() + "\n"
        em = Embed(title=title, description=desc, color=0x3498DB)
        em.set_footer(text=f"Страница {self.page + 1}/{len(pages)}")
        return em

    async def _refresh(self, interaction: Interaction):
        self.switch_mode.label = {
            "economy": "Топ по населению",
            "population": "Топ по армии",
            "army": "Топ по экономике",
        }[self.mode]
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray)
    async def back(self, interaction: Interaction, button: Button):
        self.page -= 1
        await self._refresh(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray)
    async def forward(self, interaction: Interaction, button: Button):
        self.page += 1
        await self._refresh(interaction)

    @discord.ui.button(label="Топ по населению", style=discord.ButtonStyle.blurple)
    async def switch_mode(self, interaction: Interaction, button: Button):
        self.page = 0
        self.mode = {"economy": "population", "population": "army", "army": "economy"}[self.mode]
        await self._refresh(interaction)


@bot.command()
async def топ(ctx):
    view = TopView()
    await ctx.send(embed=view.build_embed(), view=view)


@bot.command()
@commands.has_permissions(administrator=True)
async def начислить(ctx, member: discord.Member, amount: str):
    user = ensure_user(str(member.id))
    try:
        amount_value = parse_money_value(amount, user["наличка"])
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Введите число или процент (например `500` или `10%`).", color=0xFF0000))
        return

    if amount_value <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сумма должна быть больше 0.", color=0xFF0000))
        return

    user["наличка"] += amount_value
    save_json(BALANCES_FILE, balances)

    await ctx.send(
        embed=Embed(
            title="✅ Деньги начислены",
            description=f"{ctx.author.mention} начислил **{fmt_money(amount_value)}** {member.mention}!",
            color=0x00FF00,
        )
    )
    await log_economy_change(ctx.guild, member.id, f"Начисление админом {ctx.author}", cash_delta=amount_value)


@bot.command()
@commands.has_permissions(administrator=True)
async def забрать(ctx, member: discord.Member, amount: str):
    user = ensure_user(str(member.id))
    try:
        amount_value = parse_money_value(amount, user["наличка"])
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Введите число или процент (например `500` или `10%`).", color=0xFF0000))
        return

    if amount_value <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сумма должна быть больше 0.", color=0xFF0000))
        return

    user["наличка"] -= amount_value
    save_json(BALANCES_FILE, balances)

    await ctx.send(
        embed=Embed(
            title="⚠️ Деньги забраны",
            description=f"{ctx.author.mention} забрал **{fmt_money(amount_value)}** у {member.mention}!\nНовый баланс: {fmt_money(user['наличка'])}",
            color=0xFFA500,
        )
    )
    await log_economy_change(ctx.guild, member.id, f"Списание админом {ctx.author}", cash_delta=-amount_value)


@bot.command()
@commands.has_permissions(administrator=True)
async def доходдобавить(ctx, role: discord.Role, amount: str, cooldown: int, auto: str = "да"):
    role_income.setdefault("roles", {})[str(role.id)] = {
        "amount": amount,
        "cooldown": cooldown,
        "auto": auto.lower() in ["да", "yes", "true", "1"],
    }
    save_json(ROLE_INCOME_FILE, role_income)

    await ctx.send(
        embed=Embed(
            title="✅ Доход для роли добавлен",
            description=(
                f"**Роль:** {role.mention}\n\n"
                f"**Сумма:** {amount} {currency}\n\n"
                f"**Кулдаун:** {cooldown}с\n\n"
                f"**Автосбор:** {role_income['roles'][str(role.id)]['auto']}"
            ),
            color=0x00FF00,
        )
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def доходудалить(ctx, role: discord.Role):
    rid = str(role.id)
    if rid not in role_income.get("roles", {}):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Такая роль не настроена для дохода.", color=0xFF0000))
        return

    del role_income["roles"][rid]
    save_json(ROLE_INCOME_FILE, role_income)
    await ctx.send(embed=Embed(title="✅ Роль дохода удалена", description=f"Роль **{role.name}** удалена из доходов.", color=0x00FF00))


@bot.command(name="заморозкароль")
@commands.has_permissions(administrator=True)
async def заморозкароль(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(embed=Embed(title="🧊 Заморозка роли", description="Укажите роль (mention).", color=0x3498DB))
    try:
        msg_role = await bot.wait_for("message", check=check, timeout=180)
        role = await commands.RoleConverter().convert(ctx, msg_role.content.strip())
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Не удалось определить роль.", color=0xFF0000))
        return

    await ctx.send(embed=Embed(title="🧊 Заморозка роли", description="Сколько замораживает роль? (число или % от текущей налички)", color=0x3498DB))
    msg_value = await bot.wait_for("message", check=check, timeout=180)
    value = msg_value.content.strip()

    await ctx.send(embed=Embed(title="🧊 Заморозка роли", description="Укажите кулдаун (например `24ч`, `30м`, `3600`).", color=0x3498DB))
    msg_cd = await bot.wait_for("message", check=check, timeout=180)
    try:
        cooldown = parse_interval(msg_cd.content.strip())
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Неверный кулдаун: {e}", color=0xFF0000))
        return

    role_income.setdefault("freeze_roles", {})[str(role.id)] = {"value": value, "cooldown": cooldown}
    save_json(ROLE_INCOME_FILE, role_income)
    await ctx.send(
        embed=Embed(
            title="✅ Заморозка добавлена",
            description=f"{role.mention} замораживает **{value}** раз в **{format_interval(cooldown)}**.",
            color=0x00FF00,
        )
    )


@bot.command(name="заморозкарольудалить")
@commands.has_permissions(administrator=True)
async def заморозкарольудалить(ctx, role: discord.Role):
    cfg = role_income.setdefault("freeze_roles", {})
    if str(role.id) not in cfg:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Для этой роли нет заморозки.", color=0xFF0000))
        return
    del cfg[str(role.id)]
    save_json(ROLE_INCOME_FILE, role_income)
    await ctx.send(embed=Embed(title="✅ Удалено", description=f"Заморозка для {role.mention} удалена.", color=0x00FF00))


@bot.command(name="заморозкавывести")
@commands.has_permissions(administrator=True)
async def заморозкавывести(ctx, member: discord.Member, amount: str):
    user = ensure_user(str(member.id))
    try:
        amount_value = parse_money_value(amount, user.get("заморожено", 0))
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Введите число или процент.", color=0xFF0000))
        return
    if amount_value <= 0 or user.get("заморожено", 0) < amount_value:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Недостаточно замороженных средств.", color=0xFF0000))
        return
    user["заморожено"] -= amount_value
    user["наличка"] += amount_value
    save_json(BALANCES_FILE, balances)
    await ctx.send(embed=Embed(title="✅ Заморозка выведена", description=f"{member.mention}: **{fmt_money(amount_value)}** возвращено из заморозки в наличку.", color=0x00FF00))
    await log_economy_change(ctx.guild, member.id, f"Разморозка админом {ctx.author}", cash_delta=amount_value, frozen_delta=-amount_value)


@bot.command(name="кдгод")
@commands.has_permissions(administrator=True)
async def кдгод(ctx, duration: str):
    try:
        secs = parse_interval(duration)
    except Exception as e:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Неверный формат времени: {e}", color=0xFF0000))
        return

    if secs < 60:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Минимальный интервал — 60 секунд.", color=0xFF0000))
        return

    settings["happiness_tick_seconds"] = int(secs)
    save_json(SETTINGS_FILE, settings)
    await ctx.send(
        embed=Embed(
            title="✅ КД счастья обновлён",
            description=f"Автоснятие счастья теперь происходит раз в **{format_interval(secs)}**.",
            color=0x00FF00,
        )
    )


@bot.command(name="инвайтканал")
@commands.has_permissions(administrator=True)
async def инвайтканал(ctx, channel: discord.TextChannel = None):
    target = channel or ctx.channel
    perms = target.permissions_for(ctx.guild.me)
    if not perms.send_messages:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У меня нет прав писать в {target.mention}.", color=0xFF0000))
        return

    settings["invite_channel"] = target.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(embed=Embed(title="✅ Канал приветствий установлен", description=f"Канал входа/выхода: {target.mention}", color=0x00FF00))


@bot.command()
@commands.has_permissions(administrator=True)
async def автоколлектканал(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    me = ctx.guild.me or ctx.guild.get_member(bot.user.id)

    if not channel.permissions_for(me).send_messages:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка",
                description=f"У меня нет прав отправлять сообщения в канал {channel.mention}.",
                color=0xFF0000,
            )
        )
        return

    settings["autocollect_channel"] = channel.id
    save_json(SETTINGS_FILE, settings)

    await ctx.send(
        embed=Embed(
            title="✅ Канал автоколлекта установлен",
            description=f"Канал для автоколлекта: {channel.mention}",
            color=0x00FF00,
        )
    )


@bot.command(name="грабежсейвроль")
@commands.has_permissions(administrator=True)
async def грабежсейвроль(ctx, role: discord.Role):
    settings["robbery_safe_role_id"] = role.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(embed=Embed(title="✅ Роль защиты от грабежа установлена", description=f"Теперь {role.mention} защищает от команды **!грабеж**.", color=0x00FF00))


@bot.command(name="грабеж")
@commands.cooldown(1, 1800, commands.BucketType.user)
async def грабеж(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Нельзя ограбить самого себя.", color=0xFF0000))
        return

    safe_role_id = settings.get("robbery_safe_role_id")
    if safe_role_id and any(r.id == int(safe_role_id) for r in member.roles):
        await ctx.send(embed=Embed(title="🛡 Защита", description=f"{member.mention} защищён ролью от грабежа.", color=0xFFAA00))
        return

    victim = ensure_user(str(member.id))
    robber = ensure_user(str(ctx.author.id))
    victim_cash = int(victim.get("наличка", 0))

    if victim_cash <= 0:
        await ctx.send(embed=Embed(title="❌ Грабёж не удался", description=f"У {member.mention} нет налички для грабежа.", color=0xFF0000))
        return

    percent = random.randint(1, 6)
    steal_amount = max(1, int(victim_cash * percent / 100))
    steal_amount = min(steal_amount, victim_cash)

    victim["наличка"] -= steal_amount
    robber["наличка"] += steal_amount
    save_json(BALANCES_FILE, balances)

    embed = Embed(title="🦹 Грабёж", color=0x8E44AD)
    embed.add_field(name="Грабитель", value=ctx.author.mention, inline=True)
    embed.add_field(name="Жертва", value=member.mention, inline=True)
    embed.add_field(name="Украдено", value=f"**{fmt_money(steal_amount)}** ({percent}% налички)", inline=False)
    await ctx.send(embed=embed)
    await log_economy_change(ctx.guild, member.id, f"Грабёж: {ctx.author}", cash_delta=-steal_amount)
    await log_economy_change(ctx.guild, ctx.author.id, f"Грабёж: жертва {member}", cash_delta=steal_amount)


@bot.command(name="передатьроль")
@commands.has_permissions(administrator=True)
async def передатьроль(ctx, role: discord.Role):
    settings["transfer_role_id"] = role.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(embed=Embed(title="✅ Роль перевода установлена", description=f"Команду **!передать** теперь могут использовать участники с ролью {role.mention}.", color=0x00FF00))


@bot.command(name="передать")
async def передать(ctx, member: discord.Member, amount: str):
    if member.id == ctx.author.id:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Нельзя переводить деньги самому себе.", color=0xFF0000))
        return

    transfer_role_id = settings.get("transfer_role_id")
    if transfer_role_id and not any(r.id == int(transfer_role_id) for r in ctx.author.roles):
        role = ctx.guild.get_role(int(transfer_role_id))
        role_text = role.mention if role else "специальной роли"
        await ctx.send(embed=Embed(title="⛔ Недостаточно прав", description=f"Для использования **!передать** нужна роль {role_text}.", color=0xFF0000))
        return

    sender = ensure_user(str(ctx.author.id))
    receiver = ensure_user(str(member.id))

    try:
        transfer_amount = parse_money_value(amount, int(sender.get("наличка", 0)))
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Введите корректную сумму (число или %).", color=0xFF0000))
        return

    if transfer_amount <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сумма перевода должна быть больше 0.", color=0xFF0000))
        return

    if int(sender.get("наличка", 0)) < transfer_amount:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Недостаточно налички для перевода.", color=0xFF0000))
        return

    sender["наличка"] -= transfer_amount
    receiver["наличка"] += transfer_amount
    save_json(BALANCES_FILE, balances)

    await ctx.send(embed=Embed(title="💸 Перевод выполнен", description=f"{ctx.author.mention} перевёл {member.mention} **{fmt_money(transfer_amount)}**.", color=0x00FF00))
    await log_economy_change(ctx.guild, ctx.author.id, f"Перевод -> {member}", cash_delta=-transfer_amount)
    await log_economy_change(ctx.guild, member.id, f"Перевод <- {ctx.author}", cash_delta=transfer_amount)


@bot.command(name="продатьроль")
@commands.has_permissions(administrator=True)
async def продатьроль(ctx, role: discord.Role):
    settings["sell_role_id"] = role.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(embed=Embed(title="✅ Роль торговли установлена", description=f"Команду **!продать** теперь могут использовать участники с ролью {role.mention}.", color=0x00FF00))


@bot.command(name="продать", aliases=["продатьпредмет"])
async def продать(ctx, member: discord.Member, количество: int, item_key: str, предложенная_цена: str):
    if member.id == ctx.author.id:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Нельзя продавать предметы самому себе.", color=0xFF0000))
        return
    if количество <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше 0.", color=0xFF0000))
        return

    sell_role_id = settings.get("sell_role_id")
    if sell_role_id and not any(r.id == int(sell_role_id) for r in ctx.author.roles):
        role = ctx.guild.get_role(int(sell_role_id))
        role_text = role.mention if role else "специальной роли"
        await ctx.send(embed=Embed(title="⛔ Недостаточно прав", description=f"Для использования **!продать** нужна роль {role_text}.", color=0xFF0000))
        return

    matches = resolve_item_key(item_key)
    if not matches:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Предмет не найден.", color=0xFF0000))
        return

    selected_key = matches[0]
    if len(matches) > 1:
        options = "\n".join(f"{i+1} — {name}" for i, name in enumerate(matches[:10]))
        await ctx.send(embed=Embed(title="🔎 Уточнение предмета", description=f"Найдено несколько совпадений. Выберите номер:\n\n{options}", color=0x3498DB))

        def choice_check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=choice_check, timeout=60)
            idx = int(msg.content.strip()) - 1
            if idx < 0 or idx >= min(len(matches), 10):
                raise ValueError
            selected_key = matches[idx]
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Неверный выбор предмета.", color=0xFF0000))
            return

    seller_id = str(ctx.author.id)
    buyer_id = str(member.id)
    seller_items = inventory.get(seller_id, {})
    if seller_items.get(selected_key, 0) < количество:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У вас недостаточно предметов **{selected_key}**.", color=0xFF0000))
        return

    try:
        price_value = parse_money_value(предложенная_цена, ensure_user(buyer_id).get("наличка", 0))
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Цена должна быть числом или процентом.", color=0xFF0000))
        return

    if price_value <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Цена должна быть больше 0.", color=0xFF0000))
        return

    if ensure_user(buyer_id).get("наличка", 0) < price_value:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У покупателя недостаточно налички для сделки (**{fmt_money(price_value)}**).", color=0xFF0000))
        return

    class TradeOfferView(View):
        def __init__(self):
            super().__init__(timeout=300)

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != member.id:
                await interaction.response.send_message("❌ Только покупатель может ответить на эту сделку.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="✅ Принять", style=ButtonStyle.success)
        async def accept(self, interaction: Interaction, button: Button):
            seller_balance = ensure_user(seller_id)
            buyer_balance = ensure_user(buyer_id)
            seller_inv = inventory.get(seller_id, {})
            if seller_inv.get(selected_key, 0) < количество:
                await interaction.response.edit_message(embed=Embed(title="❌ Сделка отменена", description="У продавца больше нет нужного количества предметов.", color=0xFF0000), view=None)
                self.stop()
                return
            if buyer_balance.get("наличка", 0) < price_value:
                await interaction.response.edit_message(embed=Embed(title="❌ Сделка отменена", description="У покупателя больше недостаточно налички.", color=0xFF0000), view=None)
                self.stop()
                return

            seller_inv[selected_key] -= количество
            if seller_inv[selected_key] <= 0:
                del seller_inv[selected_key]
            inventory.setdefault(buyer_id, {})
            inventory[buyer_id][selected_key] = inventory[buyer_id].get(selected_key, 0) + количество

            buyer_balance["наличка"] -= price_value
            seller_balance["наличка"] += price_value

            save_inventory()
            save_json(BALANCES_FILE, balances)

            done = Embed(title="✅ Сделка проведена", color=0x00FF00)
            done.add_field(name="Продавец", value=ctx.author.mention, inline=True)
            done.add_field(name="Покупатель", value=member.mention, inline=True)
            done.add_field(name="Предмет", value=f"{selected_key} × {количество}", inline=False)
            done.add_field(name="Цена", value=fmt_money(price_value), inline=False)
            await interaction.response.edit_message(embed=done, view=None)
            await log_economy_change(ctx.guild, member.id, f"Покупка у {ctx.author}: {selected_key} x{количество}", cash_delta=-price_value)
            await log_economy_change(ctx.guild, ctx.author.id, f"Продажа {member}: {selected_key} x{количество}", cash_delta=price_value)
            self.stop()

        @discord.ui.button(label="❌ Отклонить", style=ButtonStyle.danger)
        async def decline(self, interaction: Interaction, button: Button):
            await interaction.response.edit_message(embed=Embed(title="❌ Сделка отклонена", description=f"{member.mention} отклонил предложение.", color=0xFF0000), view=None)
            self.stop()

    await ctx.send(f"{member.mention}")
    offer = Embed(title="💼 Предложение сделки", color=0x3498DB)
    offer.description = (
        f"{ctx.author.mention} предлагает продать вам предмет.\n\n"
        f"**Предмет:** {selected_key}\n"
        f"**Количество:** {количество}\n"
        f"**Цена:** {fmt_money(price_value)}"
    )
    offer.set_footer(text="Нажмите кнопку ниже: принять или отклонить.")
    await ctx.send(embed=offer, view=TradeOfferView())



@tasks.loop(seconds=60)
async def auto_role_income_loop():
    now = int(time.time())
    for guild in bot.guilds:
        if guild.id != ALLOWED_GUILD:
            continue

        channel_id = settings.get("autocollect_channel")
        channel = guild.get_channel(channel_id) if channel_id else None
        me = guild.me or guild.get_member(bot.user.id)

        if not channel or not channel.permissions_for(me).send_messages:
            channel = next((c for c in guild.text_channels if c.permissions_for(me).send_messages), None)
        if not channel:
            continue

        for member in guild.members:
            user_id = str(member.id)
            ensure_user(user_id)
            total_earned = 0
            roles_earned = []

            for rid, data in role_income.get("roles", {}).items():
                role = guild.get_role(int(rid))
                if not role or role not in member.roles or not data.get("auto", True):
                    continue

                last_map = role_income.setdefault("last_claim", {}).setdefault(user_id, {})
                last = last_map.get(rid, now)

                if now - last >= int(data["cooldown"]):
                    try:
                        amount = parse_money_value(str(data["amount"]), ensure_user(user_id)["наличка"])
                    except Exception:
                        amount = 0
                    last_map[rid] = now
                    add_balance(user_id, amount)
                    total_earned += amount
                    roles_earned.append(role.name)

            if total_earned != 0:
                save_json(ROLE_INCOME_FILE, role_income)
                desc = f"{member.mention} итог по ролям: **{total_earned:+} {currency}**\nРоли: {', '.join(roles_earned) if roles_earned else 'нет'}"
                await channel.send(
                    embed=Embed(
                        title="💰 Автоколлект!",
                        description=desc,
                        color=0x00FF00,
                    )
                )

        # Пассивные доходы/расходы от куратора
        users_flows = passive_flows.setdefault("users", {})
        changed = False
        now_ts = int(time.time())
        for user_id, entries in users_flows.items():
            if not isinstance(entries, list):
                continue
            user = ensure_user(user_id)
            for entry in list(entries):
                expires_at = entry.get("expires_at")
                if expires_at is not None and now_ts >= int(expires_at):
                    entries.remove(entry)
                    changed = True
                    continue

                cooldown = int(entry.get("cooldown", 0))
                amount_raw = str(entry.get("amount", 0))
                if cooldown <= 0:
                    continue
                last_run = int(entry.get("last_run", now_ts))
                if now_ts - last_run < cooldown:
                    continue

                cycles = (now_ts - last_run) // cooldown
                try:
                    per_cycle = parse_money_value(amount_raw, user.get("наличка", 0))
                except Exception:
                    per_cycle = 0
                if per_cycle <= 0:
                    entry["last_run"] = last_run + cycles * cooldown
                    changed = True
                    continue

                delta = per_cycle * cycles
                if entry.get("type") == "expense":
                    user["наличка"] -= delta
                else:
                    user["наличка"] += delta

                entry["last_run"] = last_run + cycles * cooldown
                changed = True

        if changed:
            save_json(BALANCES_FILE, balances)
            save_passive_flows()

        status_until = settings.get("status_until")
        if status_until is not None and int(time.time()) >= int(status_until):
            settings["status_emoji"] = None
            settings["status_text"] = None
            settings["status_until"] = None
            save_json(SETTINGS_FILE, settings)
            try:
                await bot.change_presence(activity=None)
            except Exception:
                pass

        # Счастье / население / содержание войск (каждые 12ч)
        pop = load_json(POPULATION_FILE, {})
        state_changed = False
        now_tick = int(time.time())
        for user_id, st in player_state.setdefault("users", {}).items():
            ensure_user(user_id)
            happiness = int(st.get("happiness", 50))
            shield_until = int(st.get("shield_until", 0))
            pause_until = int(st.get("happiness_pause_until", 0))
            soldiers = int(st.get("soldiers", 0))

            happiness_tick = max(60, int(settings.get("happiness_tick_seconds", 43200)))
            last_h = int(st.get("last_happiness_tick", now_tick))
            if now_tick - last_h >= happiness_tick:
                cycles = (now_tick - last_h) // happiness_tick
                st["last_happiness_tick"] = last_h + cycles * happiness_tick
                if now_tick >= shield_until and now_tick >= pause_until:
                    pop_val = int(pop.get(user_id, 0))
                    drain = get_mobilization_happiness_penalty(pop_val, soldiers)
                    happiness = max(0, happiness - drain * cycles)
                    st["happiness"] = happiness

                    if happiness <= 0:
                        wipe_user_data(user_id, guild)
                        continue

                    growth_pct = get_population_growth_percent(happiness)
                    if growth_pct is not None and pop_val > 0:
                        pop_val = max(0, int(round(pop_val * (1 + growth_pct / 100.0))))
                        # Подрезка солдат к лимиту 30%
                        max_s = int((pop_val + soldiers) * 0.3)
                        if soldiers > max_s:
                            diff = soldiers - max_s
                            soldiers = max_s
                            st["soldiers"] = soldiers
                            pop_val += diff
                        pop[user_id] = pop_val
                    state_changed = True

            last_m = int(st.get("last_mobilization_cost_tick", now_tick))
            if now_tick - last_m >= 43200 and soldiers > 0:
                cycles = (now_tick - last_m) // 43200
                st["last_mobilization_cost_tick"] = last_m + cycles * 43200
                per_cost = 7 if st.get("war_mode", False) else 1
                ensure_user(user_id)["наличка"] -= per_cost * soldiers * cycles
                state_changed = True

        if state_changed:
            save_json(POPULATION_FILE, pop)
            save_player_state()
            save_json(BALANCES_FILE, balances)


# ================== ITEMS / SHOP ==================
@bot.command(name="категориядобавить")
@commands.has_permissions(administrator=True)
async def категориядобавить(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(embed=Embed(title="🧩 Новая категория", description="Введите название категории.", color=0x3498DB))
    try:
        name = (await bot.wait_for("message", check=check, timeout=180)).content.strip()
    except Exception:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Время ожидания истекло.", color=0xFF0000))
        return

    if not name:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Название не может быть пустым.", color=0xFF0000))
        return

    if any(str(v).casefold() == name.casefold() for v in items_data.get("categories", {}).values()):
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Категория с таким названием уже существует.", color=0xFF0000))
        return

    await ctx.send(embed=Embed(title="🧩 Новая категория", description="Введите эмодзи категории (или `скип`).", color=0x3498DB))
    try:
        emoji_raw = (await bot.wait_for("message", check=check, timeout=180)).content.strip()
    except Exception:
        emoji_raw = "скип"

    cat_ids = [int(k) for k in items_data.setdefault("categories", {}).keys() if str(k).isdigit()]
    new_id = str(max(cat_ids) + 1 if cat_ids else 1)

    items_data.setdefault("categories", {})[new_id] = name
    if emoji_raw.lower() != "скип":
        items_data.setdefault("category_emojis", {})[new_id] = emoji_raw
    else:
        items_data.setdefault("category_emojis", {}).setdefault(new_id, "")

    save_items()
    emoji_view = items_data.get("category_emojis", {}).get(new_id, "") or "—"
    await ctx.send(embed=Embed(title="✅ Категория добавлена", description=f"**Номер:** {new_id}\n**Название:** {name}\n**Эмодзи:** {emoji_view}", color=0x00FF00))


@bot.command(name="категорияудалить")
@commands.has_permissions(administrator=True)
async def категорияудалить(ctx, *, category_ref: str):
    categories = items_data.setdefault("categories", {})
    target_id = None
    ref = category_ref.strip()

    if ref in categories:
        target_id = ref
    else:
        for cid, cname in categories.items():
            if str(cname).casefold() == ref.casefold():
                target_id = cid
                break

    if target_id is None:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Категория не найдена. Укажите номер или точное название.", color=0xFF0000))
        return

    used_items = [k for k, item in items_data.get("items", {}).items() if str(item.get("category")) == str(target_id)]
    if used_items:
        preview = "\n".join(f"• {k}" for k in used_items[:10])
        more = "" if len(used_items) <= 10 else f"\n... и ещё {len(used_items)-10}"
        await ctx.send(
            embed=Embed(
                title="❌ Нельзя удалить категорию",
                description=f"В этой категории есть предметы:\n{preview}{more}\n\nСначала удалите/перенесите эти предметы.",
                color=0xFF0000,
            )
        )
        return

    removed_name = categories.pop(target_id)
    items_data.setdefault("category_emojis", {}).pop(target_id, None)
    save_items()

    await ctx.send(embed=Embed(title="✅ Категория удалена", description=f"Удалена категория **{removed_name}** (№{target_id}).", color=0x00FF00))


@bot.command()
@commands.has_permissions(administrator=True)
async def создатьпредмет(ctx):
    draft = {
        "key": "", "price": 0, "category": "1", "stock": -1, "expires_at": None,
        "description": "", "require_roles": [], "give_roles": [], "remove_roles": [], "use_text": None,
    }

    FIELD_LABELS = {
        "key": "Ключ",
        "price": "Цена",
        "category": "Категория",
        "stock": "Количество",
        "ttl": "Время жизни",
        "description": "Описание",
        "require_roles": "Обязательные роли",
        "give_roles": "Выдаёт роли",
        "remove_roles": "Забирает роли",
        "use_text": "Текст использования",
    }

    def categories_text():
        lines = []
        for cid, cname in sorted(items_data.get("categories", {}).items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 99999):
            emoji = items_data.get("category_emojis", {}).get(str(cid), "")
            marker = " ✅" if str(cid) == str(draft["category"]) else ""
            emoji_part = f"{emoji} " if emoji else ""
            lines.append(f"`{cid}` — {emoji_part}{cname}{marker}")
        return "\n".join(lines) if lines else "—"

    def format_roles(role_ids):
        if not role_ids:
            return "—"
        vals = []
        for rid in role_ids:
            role = ctx.guild.get_role(int(rid)) if ctx.guild else None
            vals.append(role.mention if role else f"<@&{rid}>")
        return ", ".join(vals) if vals else "—"

    def build_embed():
        e = Embed(title="📝 Создание предмета", color=0x3498DB)
        ttl_text = "∞" if draft["expires_at"] is None else format_seconds_left(int(draft["expires_at"]) - int(time.time()))
        stock_text = "∞" if int(draft["stock"]) == -1 else str(draft["stock"])
        cat_id = str(draft["category"])
        cat_name = items_data.get("categories", {}).get(cat_id, cat_id)
        e.add_field(name="Ключ", value=draft["key"] or "—", inline=True)
        e.add_field(name="Цена", value=(fmt_money(draft["price"]) if draft["price"] else "—"), inline=True)
        e.add_field(name="Категория", value=f"№{cat_id} — {cat_name}", inline=True)
        e.add_field(name="Количество", value=stock_text, inline=True)
        e.add_field(name="Время жизни", value=ttl_text, inline=True)
        e.add_field(name="Описание", value=draft["description"] or "—", inline=False)
        e.add_field(name="Обязательные роли", value=format_roles(draft["require_roles"]), inline=False)
        e.add_field(name="Выдаёт роли", value=format_roles(draft["give_roles"]), inline=False)
        e.add_field(name="Забирает роли", value=format_roles(draft["remove_roles"]), inline=False)
        e.add_field(name="Текст использования", value=draft["use_text"] or "✅", inline=False)
        categories_value = categories_text()
        if len(categories_value) > 1024:
            categories_value = categories_value[:1021] + "..."
        e.add_field(name="Категории (номер — название)", value=categories_value, inline=False)
        e.set_footer(text="Выберите пункт из меню ниже, чтобы открыть форму редактирования")
        return e

    class EditFieldModal(Modal):
        def __init__(self, field_name: str):
            super().__init__(title=f"Редактирование: {FIELD_LABELS[field_name]}", timeout=600)
            self.field_name = field_name

            defaults = {
                "key": draft["key"],
                "price": str(draft["price"]) if draft["price"] else "",
                "category": str(draft["category"]),
                "stock": "скип" if int(draft["stock"]) == -1 else str(draft["stock"]),
                "ttl": "скип" if draft["expires_at"] is None else str(max(0, int(draft["expires_at"]) - int(time.time()))),
                "description": draft["description"],
                "require_roles": " ".join(f"<@&{x}>" for x in draft["require_roles"]),
                "give_roles": " ".join(f"<@&{x}>" for x in draft["give_roles"]),
                "remove_roles": " ".join(f"<@&{x}>" for x in draft["remove_roles"]),
                "use_text": draft["use_text"] or "скип",
            }

            labels = {
                "key": "Ключ предмета",
                "price": "Цена",
                "category": "Категория (номер)",
                "stock": "Количество (или скип)",
                "ttl": "Время жизни в сек (или скип)",
                "description": "Описание",
                "require_roles": "Обязательные роли (или скип)",
                "give_roles": "Выдаёт роли (или скип)",
                "remove_roles": "Забирает роли (или скип)",
                "use_text": "Текст использования (или скип)",
            }

            styles = {
                "description": discord.TextStyle.paragraph,
                "use_text": discord.TextStyle.paragraph,
            }

            self.value_input = TextInput(
                label=labels[field_name],
                required=True,
                default=defaults[field_name][:1000] if isinstance(defaults[field_name], str) else str(defaults[field_name]),
                style=styles.get(field_name, discord.TextStyle.short),
                max_length=1000,
            )
            self.add_item(self.value_input)

        async def on_submit(self, interaction: Interaction):
            raw = str(self.value_input.value).strip()
            try:
                if self.field_name == "key":
                    draft["key"] = raw
                elif self.field_name == "price":
                    draft["price"] = int(raw)
                elif self.field_name == "category":
                    if raw not in items_data.get("categories", {}):
                        raise ValueError("Категория не существует")
                    draft["category"] = raw
                elif self.field_name == "stock":
                    draft["stock"] = -1 if raw.lower() == "скип" else int(raw)
                elif self.field_name == "ttl":
                    draft["expires_at"] = None if raw.lower() == "скип" else int(time.time()) + int(raw)
                elif self.field_name == "description":
                    draft["description"] = raw
                elif self.field_name == "require_roles":
                    draft["require_roles"] = parse_role_mentions(raw or "скип")
                elif self.field_name == "give_roles":
                    draft["give_roles"] = parse_role_mentions(raw or "скип")
                elif self.field_name == "remove_roles":
                    draft["remove_roles"] = parse_role_mentions(raw or "скип")
                elif self.field_name == "use_text":
                    draft["use_text"] = None if raw.lower() == "скип" else (raw or None)
            except Exception as e:
                await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)
                return
            await interaction.response.edit_message(embed=build_embed(), view=view)

    class EditSelect(Select):
        def __init__(self):
            options = [
                SelectOption(label="Ключ", value="key", emoji="🏷️"),
                SelectOption(label="Цена", value="price", emoji="💵"),
                SelectOption(label="Категория", value="category", emoji="🧩"),
                SelectOption(label="Количество", value="stock", emoji="📦"),
                SelectOption(label="Время жизни", value="ttl", emoji="⏱️"),
                SelectOption(label="Описание", value="description", emoji="📝"),
                SelectOption(label="Обязательные роли", value="require_roles", emoji="🔒"),
                SelectOption(label="Выдаёт роли", value="give_roles", emoji="✅"),
                SelectOption(label="Забирает роли", value="remove_roles", emoji="❌"),
                SelectOption(label="Текст использования", value="use_text", emoji="💬"),
                SelectOption(label="Сохранить предмет", value="save", emoji="💾"),
                SelectOption(label="Отмена", value="cancel", emoji="🛑"),
            ]
            super().__init__(placeholder="Выберите пункт для редактирования", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: Interaction):
            selected = self.values[0]
            if selected == "save":
                key = draft["key"].strip()
                if not key or int(draft["price"]) <= 0:
                    await interaction.response.send_message("❌ Заполните ключ и цену (>0).", ephemeral=True)
                    return
                if key in items_data.get("items", {}):
                    await interaction.response.send_message("❌ Предмет с таким ключом уже существует.", ephemeral=True)
                    return
                items_data.setdefault("items", {})[key] = {
                    "key": key,
                    "price": int(draft["price"]),
                    "description": draft["description"],
                    "category": str(draft["category"]),
                    "stock": int(draft["stock"]),
                    "expires_at": draft["expires_at"],
                    "require_roles": draft["require_roles"],
                    "give_roles": draft["give_roles"],
                    "remove_roles": draft["remove_roles"],
                    "use_text": draft["use_text"],
                    "created_at": int(time.time()),
                }
                save_items()
                await interaction.response.edit_message(
                    embed=Embed(title="✅ Предмет создан", description=f"Предмет **{key}** успешно сохранён.", color=0x00FF00),
                    view=None,
                )
                view.stop()
                return

            if selected == "cancel":
                await interaction.response.edit_message(embed=Embed(title="❎ Создание отменено", color=0xAAAAAA), view=None)
                view.stop()
                return

            await interaction.response.send_modal(EditFieldModal(selected))

    class CreateItemView(View):
        def __init__(self):
            super().__init__(timeout=900)
            self.add_item(EditSelect())

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Только автор команды может настраивать.", ephemeral=True)
                return False
            return True

    view = CreateItemView()
    await ctx.send(embed=build_embed(), view=view)


@bot.command()
async def магазин(ctx):
    if not items_data["items"]:
        await ctx.send(embed=Embed(title="🛒 Магазин пуст", description="В магазине нет предметов.", color=0xFFA500))
        return

    categories = items_data["categories"]
    category_emojis = items_data.get("category_emojis", {})
    options = []
    for key, name in categories.items():
        emoji = parse_select_emoji((category_emojis.get(str(key), "") or "").strip()[:64])
        if emoji is not None:
            options.append(SelectOption(label=name, value=key, emoji=emoji))
        else:
            options.append(SelectOption(label=name, value=key))
    select = Select(placeholder="Выберите категорию", options=options)

    async def select_callback(interaction: Interaction):
        selected_key = select.values[0]
        category_name = categories[selected_key]

        items_list = [
            item
            for item in items_data["items"].values()
            if item["category"] == selected_key and (item["expires_at"] is None or item["expires_at"] > int(time.time()))
        ]

        if not items_list:
            await interaction.response.send_message(
                embed=Embed(title=f"🛒 {category_name}", description="Нет доступных предметов.", color=0xFFA500),
                ephemeral=True,
            )
            return

        items_list.sort(key=lambda x: str(x.get("key", "")).casefold())
        page_size = 10
        total_pages = (len(items_list) + page_size - 1) // page_size

        def build_page(page_index: int):
            start = page_index * page_size
            page_items = items_list[start:start + page_size]
            desc = ""
            for item in page_items:
                count = "∞" if item["stock"] == -1 else str(item["stock"])
                desc += f"**{item['key']}** — {fmt_money(item['price'])}, Кол-во: {count}\n{item['description']}\n\n"
            e = Embed(title=f"🛒 {category_name}", description=desc or "Нет предметов.", color=0x3498DB)
            e.set_footer(text=f"Страница {page_index + 1}/{max(1, total_pages)}")
            return e

        if total_pages <= 1:
            await interaction.response.send_message(embed=build_page(0), ephemeral=True)
            return

        class ShopPageView(View):
            def __init__(self, owner_id: int):
                super().__init__(timeout=300)
                self.owner_id = owner_id
                self.page = 0

            async def interaction_check(self, i: Interaction) -> bool:
                if i.user.id != self.owner_id:
                    await i.response.send_message("❌ Это меню не для вас.", ephemeral=True)
                    return False
                return True

            @discord.ui.button(label="⬅️", style=ButtonStyle.gray)
            async def back(self, i: Interaction, b: Button):
                self.page = (self.page - 1) % total_pages
                await i.response.edit_message(embed=build_page(self.page), view=self)

            @discord.ui.button(label="➡️", style=ButtonStyle.gray)
            async def forward(self, i: Interaction, b: Button):
                self.page = (self.page + 1) % total_pages
                await i.response.edit_message(embed=build_page(self.page), view=self)

        view_pages = ShopPageView(interaction.user.id)
        await interaction.response.send_message(embed=build_page(0), view=view_pages, ephemeral=True)

    select.callback = select_callback
    view = View(timeout=180)
    view.add_item(select)

    await ctx.send(embed=Embed(title="🛒 Магазин", description="Выберите категорию предметов ниже:", color=0x3498DB), view=view)


@bot.command()
async def купить(ctx, количество: int, *, item_key: str):
    user_id = str(ctx.author.id)
    user = ensure_user(user_id)

    matches = resolve_item_key(item_key)
    if not matches:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Предмет **{item_key}** не найден.", color=0xFF0000))
        return

    selected_key = matches[0]
    if len(matches) > 1:
        options = "\n".join(f"{i+1} — {name}" for i, name in enumerate(matches[:10]))
        await ctx.send(embed=Embed(title="🔎 Найдены совпадения", description=f"Уточните номер товара:\n{options}", color=0x3498DB))
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            idx = int(msg.content.strip()) - 1
            selected_key = matches[idx]
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Не удалось выбрать товар по номеру.", color=0xFF0000))
            return

    item = items_data["items"].get(selected_key)

    if количество <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше нуля.", color=0xFF0000))
        return

    if item["stock"] != -1 and количество > item["stock"]:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Доступно только {item['stock']} шт.", color=0xFF0000))
        return

    total_price = item["price"] * количество
    if get_available_cash(user) < total_price:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Недостаточно {currency}. Нужно {total_price}.", color=0xFF0000))
        return

    missing_roles = []
    for rid in item.get("require_roles", []):
        role = ctx.guild.get_role(rid)
        if role and role not in ctx.author.roles:
            missing_roles.append(role.mention)

    if missing_roles:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка",
                description=f"Для использования предмета требуются роли: {', '.join(missing_roles)}",
                color=0xFF0000,
            )
        )
        return

    user["наличка"] -= total_price
    save_json(BALANCES_FILE, balances)

    if item["stock"] != -1:
        item["stock"] -= количество
        save_items()

    inventory.setdefault(user_id, {})
    inventory[user_id][selected_key] = inventory[user_id].get(selected_key, 0) + количество
    save_inventory()

    for rid in item.get("give_roles", []):
        role = ctx.guild.get_role(rid)
        if role:
            await ctx.author.add_roles(role)

    for rid in item.get("remove_roles", []):
        role = ctx.guild.get_role(rid)
        if role:
            await ctx.author.remove_roles(role)

    use_text = item.get("use_text") or "✅"
    await ctx.send(
        embed=Embed(
            title=f"💰 Покупка успешна — {selected_key}",
            description=f"{ctx.author.mention}, вы приобрели **{количество} × {selected_key}** за **{total_price} {currency}**.\n{use_text}",
            color=0x00FF00,
        )
    )



@bot.command(name="инвестировать")
async def инвестировать(ctx, сумма: int, *, bank_name: str):
    user_id = str(ctx.author.id)
    user = ensure_user(user_id)

    if сумма <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Сумма инвестиции должна быть больше нуля.", color=0xFF0000))
        return

    matches = resolve_item_key(bank_name)
    bank_matches = [m for m in matches if m.lower() in INVESTMENT_BANKS]

    if not bank_matches:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка",
                description="Банк не найден. Доступно: **Alta-Bank**, **Neo-Bank**, **Fantom-Bank**.",
                color=0xFF0000,
            )
        )
        return

    selected_key = bank_matches[0]
    if len(bank_matches) > 1:
        options = "\n".join(f"{i+1} — {name}" for i, name in enumerate(bank_matches[:10]))
        await ctx.send(embed=Embed(title="🔎 Найдены совпадения", description=f"Уточните номер банка:\n{options}", color=0x3498DB))

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            idx = int(msg.content.strip()) - 1
            selected_key = bank_matches[idx]
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Не удалось выбрать банк по номеру.", color=0xFF0000))
            return

    user_items = inventory.get(user_id, {})
    if int(user_items.get(selected_key, 0)) <= 0:
        await ctx.send(
            embed=Embed(
                title="❌ Нет банка",
                description=f"Для инвестирования в **{selected_key}** у вас должен быть хотя бы **1 × {selected_key}** в инвентаре.",
                color=0xFF0000,
            )
        )
        return

    if get_available_cash(user) < сумма:
        await ctx.send(
            embed=Embed(
                title="❌ Недостаточно средств",
                description=f"Для инвестирования нужно **{сумма} {currency}**, а доступно **{get_available_cash(user)} {currency}**.",
                color=0xFF0000,
            )
        )
        return

    user["наличка"] -= сумма
    cfg = INVESTMENT_BANKS[selected_key.lower()]
    ensure_investments(user_id).append(
        {
            "bank": selected_key.lower(),
            "bank_name": cfg["name"],
            "amount": сумма,
            "next_at": int(time.time()) + 86400,
            "status": "active",
        }
    )

    save_json(BALANCES_FILE, balances)
    save_investments()

    await ctx.send(
        embed=Embed(
            title="🏦 Инвестиция оформлена",
            description=(
                f"{ctx.author.mention}, вы инвестировали **{сумма} {currency}** в **{selected_key}**.\n"
                f"Банк не расходуется: требуется только наличие **1 × {selected_key}**.\n"
                f"Результат будет доступен через **24ч** в команде `!коллект`."
            ),
            color=0x00FF00,
        )
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def пополнитьпредмет(ctx, количество: int, *, item_key: str):
    if количество <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше нуля.", color=0xFF0000))
        return

    selected_key = await pick_item_key_by_query(ctx, item_key)
    if not selected_key:
        return

    item = items_data["items"].get(selected_key)
    if not item:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Предмет **{selected_key}** не найден.", color=0xFF0000))
        return

    if item["stock"] == -1:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="У предмета бесконечное количество.", color=0xFFA500))
        return

    item["stock"] += количество
    save_items()

    await ctx.send(
        embed=Embed(
            title="✅ Предмет пополнен",
            description=f"Предмет **{selected_key}** пополнен на **{количество}**. Теперь: **{item['stock']}**.",
            color=0x00FF00,
        )
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def удалитьпредмет(ctx, *, item_key: str):
    selected_key = await pick_item_key_by_query(ctx, item_key)
    if not selected_key:
        return

    if selected_key not in items_data["items"]:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Предмет **{selected_key}** не найден.", color=0xFF0000))
        return

    del items_data["items"][selected_key]
    save_items()

    await ctx.send(
        embed=Embed(
            title="✅ Предмет удалён",
            description=f"Предмет **{selected_key}** удалён.",
            color=0x00FF00,
        )
    )


@bot.command(name="предметинфо")
async def предметинфо(ctx, *, item_query: str):
    matches = resolve_item_key(item_query)
    if not matches:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Предмет не найден.", color=0xFF0000))
        return

    selected_key = matches[0]
    if len(matches) > 1:
        options = "\n".join(f"{i+1} — {name}" for i, name in enumerate(matches[:10]))
        await ctx.send(embed=Embed(title="🔎 Уточнение предмета", description=f"Найдено несколько совпадений. Выберите номер:\n\n{options}", color=0x3498DB))

        def choice_check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=choice_check, timeout=60)
            idx = int(msg.content.strip()) - 1
            if idx < 0 or idx >= min(len(matches), 10):
                raise ValueError
            selected_key = matches[idx]
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Неверный выбор предмета.", color=0xFF0000))
            return

    item = items_data.get("items", {}).get(selected_key)
    if not item:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Предмет не найден в базе.", color=0xFF0000))
        return

    def format_roles(role_ids):
        if not role_ids:
            return "—"
        mentions = []
        for rid in role_ids:
            role = ctx.guild.get_role(rid) if ctx.guild else None
            mentions.append(role.mention if role else f"<@&{rid}>")
        return ", ".join(mentions) if mentions else "—"

    ttl_text = "∞" if item.get("expires_at") is None else f"{max(0, int(item['expires_at']) - int(time.time()))} сек"
    stock_text = "∞" if int(item.get("stock", 0)) == -1 else str(item.get("stock", 0))
    category_name = items_data.get("categories", {}).get(str(item.get("category")), str(item.get("category")))

    embed = Embed(title=f"📦 Информация о предмете — {item.get('key', selected_key)}", color=0x3498DB)
    embed.add_field(name="Ключ", value=item.get("key", selected_key), inline=True)
    embed.add_field(name="Цена", value=f"{fmt_money(item.get('price', 0))}", inline=True)
    embed.add_field(name="Категория", value=category_name, inline=True)
    embed.add_field(name="Количество", value=stock_text, inline=True)
    embed.add_field(name="Время жизни", value=ttl_text, inline=True)
    embed.add_field(name="Описание", value=item.get("description") or "—", inline=False)
    embed.add_field(name="Обязательные роли", value=format_roles(item.get("require_roles", [])), inline=False)
    embed.add_field(name="Выдаёт роли", value=format_roles(item.get("give_roles", [])), inline=False)
    embed.add_field(name="Забирает роли", value=format_roles(item.get("remove_roles", [])), inline=False)
    embed.add_field(name="Текст использования", value=item.get("use_text") or "✅", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="редактироватьпредмет")
@commands.has_permissions(administrator=True)
async def редактироватьпредмет(ctx, *, item_query: str):
    selected_key = await pick_item_key_by_query(ctx, item_query)
    if not selected_key:
        return
    item = items_data.get("items", {}).get(selected_key)
    if not item:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Предмет не найден в базе.", color=0xFF0000))
        return

    draft = {
        "key": item.get("key", selected_key), "price": int(item.get("price", 0)), "category": str(item.get("category", "1")),
        "stock": int(item.get("stock", -1)), "expires_at": item.get("expires_at"), "description": item.get("description", ""),
        "require_roles": list(item.get("require_roles", [])), "give_roles": list(item.get("give_roles", [])),
        "remove_roles": list(item.get("remove_roles", [])), "use_text": item.get("use_text"),
    }

    def build_embed():
        e = Embed(title=f"🛠 Редактирование — {selected_key}", color=0x3498DB)
        ttl_text = "∞" if draft["expires_at"] is None else format_seconds_left(int(draft["expires_at"]) - int(time.time()))
        stock_text = "∞" if int(draft["stock"]) == -1 else str(draft["stock"])
        cat_name = items_data.get("categories", {}).get(str(draft["category"]), str(draft["category"]))
        e.add_field(name="Ключ", value=draft["key"] or "—", inline=True)
        e.add_field(name="Цена", value=fmt_money(draft["price"]), inline=True)
        e.add_field(name="Категория", value=cat_name, inline=True)
        e.add_field(name="Количество", value=stock_text, inline=True)
        e.add_field(name="Время жизни", value=ttl_text, inline=True)
        e.add_field(name="Описание", value=draft["description"] or "—", inline=False)
        return e

    class EditBaseModal(Modal):
        def __init__(self):
            super().__init__(title="Основные параметры", timeout=600)
            self.key = TextInput(label="Ключ предмета", required=True, max_length=120, default=draft["key"])
            self.price = TextInput(label="Цена", required=True, default=str(draft["price"]))
            self.category = TextInput(label="Категория (номер)", required=True, default=str(draft["category"]))
            self.stock = TextInput(label="Количество (или скип)", required=True, default=("скип" if int(draft["stock"]) == -1 else str(draft["stock"])))
            ttl_default = "скип" if draft["expires_at"] is None else str(max(0, int(draft["expires_at"]) - int(time.time())))
            self.ttl = TextInput(label="Время жизни в сек (или скип)", required=True, default=ttl_default)
            for it in (self.key, self.price, self.category, self.stock, self.ttl):
                self.add_item(it)

        async def on_submit(self, interaction: Interaction):
            try:
                draft["key"] = str(self.key.value).strip()
                draft["price"] = int(str(self.price.value).strip())
                cat = str(self.category.value).strip()
                if cat not in items_data.get("categories", {}):
                    raise ValueError("Категория не существует")
                draft["category"] = cat
                raw_stock = str(self.stock.value).strip().lower()
                draft["stock"] = -1 if raw_stock == "скип" else int(raw_stock)
                raw_ttl = str(self.ttl.value).strip().lower()
                draft["expires_at"] = None if raw_ttl == "скип" else int(time.time()) + int(raw_ttl)
            except Exception as e:
                await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)
                return
            await interaction.response.edit_message(embed=build_embed(), view=view)

    class EditExtraModal(Modal):
        def __init__(self):
            super().__init__(title="Описание и роли", timeout=600)
            self.description = TextInput(label="Описание", required=True, style=discord.TextStyle.paragraph, default=str(draft["description"])[:1000])
            self.roles = TextInput(label="Роли (req|give|remove) через ;", required=False, default=f"{' '.join(f'<@&{x}>' for x in draft['require_roles'])};{' '.join(f'<@&{x}>' for x in draft['give_roles'])};{' '.join(f'<@&{x}>' for x in draft['remove_roles'])}")
            self.use_text = TextInput(label="Текст использования (или скип)", required=False, default=(draft["use_text"] or "скип"))
            self.add_item(self.description)
            self.add_item(self.roles)
            self.add_item(self.use_text)

        async def on_submit(self, interaction: Interaction):
            draft["description"] = str(self.description.value).strip()
            raw = str(self.roles.value or "").strip()
            parts = [p.strip() for p in raw.split(";")]
            while len(parts) < 3:
                parts.append("")
            draft["require_roles"] = parse_role_mentions(parts[0] or "скип")
            draft["give_roles"] = parse_role_mentions(parts[1] or "скип")
            draft["remove_roles"] = parse_role_mentions(parts[2] or "скип")
            txt = str(self.use_text.value or "").strip()
            draft["use_text"] = None if txt.lower() == "скип" else (txt or None)
            await interaction.response.edit_message(embed=build_embed(), view=view)

    class EditView(View):
        def __init__(self):
            super().__init__(timeout=900)

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Только автор команды может настраивать.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="Основные данные", style=ButtonStyle.primary)
        async def base(self, interaction: Interaction, button: Button):
            await interaction.response.send_modal(EditBaseModal())

        @discord.ui.button(label="Описание/роли", style=ButtonStyle.primary)
        async def extra(self, interaction: Interaction, button: Button):
            await interaction.response.send_modal(EditExtraModal())

        @discord.ui.button(label="✅ Сохранить", style=ButtonStyle.success)
        async def save(self, interaction: Interaction, button: Button):
            nonlocal selected_key
            old_price = int(item.get("price", 0))
            item.update({
                "key": draft["key"], "price": int(draft["price"]), "category": str(draft["category"]), "stock": int(draft["stock"]),
                "expires_at": draft["expires_at"], "description": draft["description"], "require_roles": draft["require_roles"],
                "give_roles": draft["give_roles"], "remove_roles": draft["remove_roles"], "use_text": draft["use_text"],
            })
            if draft["key"] != selected_key:
                if draft["key"] in items_data.get("items", {}):
                    await interaction.response.send_message("❌ Такой ключ уже существует.", ephemeral=True)
                    return
                items_data["items"][draft["key"]] = item
                del items_data["items"][selected_key]
                for uid, user_items in inventory.items():
                    if selected_key in user_items:
                        user_items[draft["key"]] = user_items.get(draft["key"], 0) + user_items.pop(selected_key)
                selected_key = draft["key"]
                save_inventory()

            new_price = int(draft["price"])
            if new_price < old_price:
                diff = old_price - new_price
                refunded_total = 0
                for uid, user_items in inventory.items():
                    qty = int(user_items.get(selected_key, 0))
                    if qty > 0:
                        user_ref = ensure_user(str(uid))
                        refund = diff * qty
                        user_ref["наличка"] += refund
                        refunded_total += refund
                if refunded_total > 0:
                    save_json(BALANCES_FILE, balances)

            save_items()
            await interaction.response.edit_message(embed=Embed(title="✅ Предмет обновлён", description=f"Сохранено: **{selected_key}**", color=0x00FF00), view=None)
            self.stop()

        @discord.ui.button(label="❌ Отмена", style=ButtonStyle.secondary)
        async def cancel(self, interaction: Interaction, button: Button):
            await interaction.response.edit_message(embed=Embed(title="❎ Редактирование отменено", color=0xAAAAAA), view=None)
            self.stop()

    view = EditView()
    await ctx.send(embed=build_embed(), view=view)


@bot.command()
async def инвентарь(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    user_items = inventory.get(user_id, {})

    if not user_items:
        await ctx.send(embed=Embed(title="🎒 Инвентарь пуст", description=f"У {member.mention} пока нет предметов.", color=0xFFA500))
        return

    categories = items_data["categories"]
    category_emojis = items_data.get("category_emojis", {})
    options = []
    for key, name in categories.items():
        emoji = parse_select_emoji((category_emojis.get(str(key), "") or "").strip()[:64])
        if emoji is not None:
            options.append(SelectOption(label=name, value=key, emoji=emoji))
        else:
            options.append(SelectOption(label=name, value=key))
    select = Select(placeholder="Выберите категорию", options=options)

    async def select_callback(interaction: Interaction):
        selected_key = select.values[0]
        category_name = categories[selected_key]

        category_items = [
            (key, amount)
            for key, amount in user_items.items()
            if key in items_data["items"] and items_data["items"][key]["category"] == selected_key
        ]

        if not category_items:
            await interaction.response.send_message(
                embed=Embed(title=f"🎒 {category_name}", description="Нет предметов в этой категории.", color=0xFFA500),
                ephemeral=True,
            )
            return

        desc = ""
        for key, amount in category_items:
            info = items_data["items"].get(key)
            if info:
                desc += f"**{key}** — {amount} шт.\n{info['description']}\n\n"

        await interaction.response.send_message(embed=Embed(title=f"🎒 {category_name}", description=desc, color=0x3498DB), ephemeral=True)

    select.callback = select_callback
    view = View(timeout=180)
    view.add_item(select)

    await ctx.send(embed=Embed(title=f"🎒 Инвентарь — {member.display_name}", description="Выберите категорию ниже:", color=0x3498DB), view=view)


@bot.command()
async def использовать(ctx, количество: int, *, item_key: str):
    user_id = str(ctx.author.id)
    user_items = inventory.get(user_id, {})

    if количество <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше нуля.", color=0xFF0000))
        return

    selected_key = await pick_item_key_by_query(ctx, item_key)
    if not selected_key:
        return

    if selected_key not in user_items or user_items[selected_key] < количество:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У вас нет **{количество} × {selected_key}**.", color=0xFF0000))
        return

    item = items_data["items"].get(selected_key)
    if not item:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Предмет **{selected_key}** не найден.", color=0xFF0000))
        return

    missing_roles = []
    for rid in item.get("require_roles", []):
        role = ctx.guild.get_role(rid)
        if role and role not in ctx.author.roles:
            missing_roles.append(role.mention)

    if missing_roles:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка",
                description=f"Требуются роли: {', '.join(missing_roles)}",
                color=0xFF0000,
            )
        )
        return

    user_items[selected_key] -= количество
    if user_items[selected_key] <= 0:
        del user_items[selected_key]
    save_inventory()

    for rid in item.get("give_roles", []):
        role = ctx.guild.get_role(rid)
        if role:
            await ctx.author.add_roles(role)

    for rid in item.get("remove_roles", []):
        role = ctx.guild.get_role(rid)
        if role:
            await ctx.author.remove_roles(role)

    use_text = item.get("use_text") or "✅"
    await ctx.send(
        embed=Embed(
            title=f"🎁 Использован предмет — {selected_key}",
            description=f"{ctx.author.mention} использовал **{количество} × {selected_key}**.\n{use_text}",
            color=0x00FF00,
        )
    )


async def pick_item_key_by_query(ctx, item_query: str):
    matches = resolve_item_key(item_query)
    if not matches:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Предмет **{item_query}** не найден.", color=0xFF0000))
        return None

    selected_key = matches[0]
    if len(matches) > 1:
        options = "\n".join(f"{i+1} — {name}" for i, name in enumerate(matches[:10]))
        await ctx.send(
            embed=Embed(
                title="🔎 Уточнение предмета",
                description=f"Найдено несколько совпадений. Выберите номер:\n\n{options}",
                color=0x3498DB,
            )
        )

        def choice_check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=choice_check, timeout=60)
            idx = int(msg.content.strip()) - 1
            if idx < 0 or idx >= min(len(matches), 10):
                raise ValueError
            selected_key = matches[idx]
        except Exception:
            await ctx.send(embed=Embed(title="❌ Ошибка", description="Неверный выбор предмета.", color=0xFF0000))
            return None
    return selected_key


@bot.command()
@commands.has_permissions(administrator=True)
async def выдать(ctx, member: discord.Member, количество: int, *, item_key: str):
    if количество <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше нуля.", color=0xFF0000))
        return

    selected_key = await pick_item_key_by_query(ctx, item_key)
    if not selected_key:
        return

    user_id = str(member.id)
    inventory.setdefault(user_id, {})
    inventory[user_id][selected_key] = inventory[user_id].get(selected_key, 0) + количество
    save_inventory()

    await ctx.send(
        embed=Embed(
            title="✅ Предмет выдан",
            description=f"**Администратор:** {ctx.author.mention}\n**Получатель:** {member.mention}\n**Предмет:** {selected_key}\n**Количество:** {количество}",
            color=0x00FF00,
        )
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def изъять(ctx, member: discord.Member, количество: int, *, item_key: str):
    if количество <= 0:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Количество должно быть больше нуля.", color=0xFF0000))
        return

    user_id = str(member.id)
    user_items = inventory.get(user_id, {})

    selected_key = await pick_item_key_by_query(ctx, item_key)
    if not selected_key:
        return

    if selected_key not in user_items:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У {member.mention} нет предмета **{selected_key}**.", color=0xFF0000))
        return

    if user_items[selected_key] < количество:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Недостаточно предметов. Есть: {user_items[selected_key]}", color=0xFF0000))
        return

    user_items[selected_key] -= количество
    if user_items[selected_key] <= 0:
        del user_items[selected_key]
    save_inventory()

    await ctx.send(
        embed=Embed(
            title="⚠️ Предмет изъят",
            description=f"**Администратор:** {ctx.author.mention}\n**Игрок:** {member.mention}\n**Предмет:** {selected_key}\n**Количество:** {количество}",
            color=0xFFA500,
        )
    )


# ================== WIPE ==================
@bot.command(name="вайп")
@commands.has_permissions(administrator=True)
async def wipe_all(ctx):
    backup = {
        "time": int(time.time()),
        "balances": balances.copy(),
        "inventory": inventory.copy(),
        "population": load_json(POPULATION_FILE, {}),
        "passive_flows": passive_flows.copy(),
        "season_user_progress": seasons_data.get("user_progress", {}).copy(),
        "player_state": player_state.copy(),
        "investments": investments.copy(),
        "country_owners": country_owners.copy(),
    }
    save_json(WIPE_BACKUP_FILE, backup)

    class ConfirmView(View):
        def __init__(self):
            super().__init__(timeout=30)

        async def interaction_check(self, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Только инициатор команды может подтвердить вайп.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="✅ Подтвердить", style=ButtonStyle.danger)
        async def confirm(self, interaction: Interaction, button: Button):
            for uid, data in list(balances.items()):
                if uid == "валюта" or not isinstance(data, dict):
                    continue
                balances[uid] = {
                    "наличка": 0,
                    "банк": 0,
                    "заморожено": 0,
                    "коины": int(data.get("коины", 0)),
                }
            balances["валюта"] = currency
            inventory.clear()
            save_json(BALANCES_FILE, balances)
            save_inventory()
            save_json(POPULATION_FILE, {})
            passive_flows["users"] = {}
            save_passive_flows()
            seasons_data["user_progress"] = {}
            save_seasons_data()
            player_state["users"] = {}
            investments["users"] = {}
            country_owners["country_to_user"] = {}
            country_owners["user_to_country"] = {}
            save_player_state()
            save_investments()
            save_country_owners()

            role_ids = [int(rid) for rid in reg_settings.get("wipe_roles", []) if str(rid).isdigit()]
            for m in ctx.guild.members:
                if m.bot:
                    continue
                roles_to_remove = [r for r in m.roles if r.id in role_ids]
                try:
                    if roles_to_remove:
                        await m.remove_roles(*roles_to_remove, reason="Глобальный вайп")
                    await m.edit(nick=None, reason="Глобальный вайп")
                except Exception:
                    pass

            await interaction.response.edit_message(embed=Embed(title="💥 ГЛОБАЛЬНЫЙ ВАЙП ВЫПОЛНЕН", description="Обнулены балансы, инвентари, население, пассивные операции и прогресс сфер.", color=0x00FF00), view=None)
            self.stop()

        @discord.ui.button(label="❌ Отмена", style=ButtonStyle.secondary)
        async def cancel(self, interaction: Interaction, button: Button):
            await interaction.response.edit_message(embed=Embed(title="❎ ВАЙП ОТМЕНЁН", color=0xAAAAAA), view=None)
            self.stop()

    await ctx.send(
        embed=Embed(
            title="⚠️ ПОДТВЕРЖДЕНИЕ ГЛОБАЛЬНОГО ВАЙПА",
            description=("Нажмите ✅ чтобы подтвердить или ❌ чтобы отменить.\n\n"
                         "После вайпа можно вернуть данные командой **!отменитьвайп** в течение **1 часа**."),
            color=0xFF0000,
        ),
        view=ConfirmView(),
    )


@bot.command(name="отменитьвайп", aliases=["отменавайпа"])
@commands.has_permissions(administrator=True)
async def undo_wipe(ctx):
    backup = load_json(WIPE_BACKUP_FILE, {})
    if not backup:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Резервной копии не найдено.", color=0xFF0000))
        return

    if int(time.time()) - int(backup.get("time", 0)) > WIPE_BACKUP_TTL:
        await ctx.send(embed=Embed(title="❌ Ошибка", description="Резервная копия устарела.", color=0xFF0000))
        return

    balances.clear()
    balances.update(backup.get("balances", {"валюта": currency}))
    if "валюта" not in balances:
        balances["валюта"] = currency
    inventory.clear()
    inventory.update(backup.get("inventory", {}))

    save_json(BALANCES_FILE, balances)
    save_inventory()
    save_json(POPULATION_FILE, backup.get("population", {}))
    passive_flows.clear()
    passive_flows.update(backup.get("passive_flows", {"users": {}}))
    passive_flows.setdefault("users", {})
    save_passive_flows()
    seasons_data["user_progress"] = backup.get("season_user_progress", {})
    save_seasons_data()
    player_state.clear()
    player_state.update(backup.get("player_state", {"users": {}}))
    player_state.setdefault("users", {})
    save_player_state()
    investments.clear()
    investments.update(backup.get("investments", {"users": {}}))
    investments.setdefault("users", {})
    save_investments()
    country_owners.clear()
    country_owners.update(backup.get("country_owners", {"country_to_user": {}, "user_to_country": {}}))
    country_owners.setdefault("country_to_user", {})
    country_owners.setdefault("user_to_country", {})
    save_country_owners()

    await ctx.send(embed=Embed(title="♻️ ВАЙП ОТМЕНЁН", description="Данные восстановлены (включая прогресс сфер).", color=0x00FF00))


@bot.command(name="вайпигрок")
@commands.has_permissions(administrator=True)
async def wipe_player(ctx, member: discord.Member):
    user_id = str(member.id)
    population = load_json(POPULATION_FILE, {})
    user_passive = passive_flows.setdefault("users", {}).get(user_id, [])

    if user_id not in balances and user_id not in inventory and user_id not in population and not user_passive:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"У {member.mention} нет данных для вайпа.", color=0xFF0000))
        return

    class ConfirmPlayerWipe(View):
        def __init__(self):
            super().__init__(timeout=30)

        async def interaction_check(self, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Только инициатор команды может подтвердить вайп.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="✅ Подтвердить", style=ButtonStyle.danger)
        async def confirm(self, interaction: Interaction, button: Button):
            backup = load_json(WIPE_BACKUP_FILE, {"players": {}})
            backup.setdefault("players", {})[user_id] = {
                "time": int(time.time()),
                "balances": balances.get(user_id, {}),
                "inventory": inventory.get(user_id, {}),
                "population": population.get(user_id, 0),
                "passive_entries": get_passive_entries(user_id).copy(),
                "season_progress": seasons_data.get("user_progress", {}).get(user_id, {}).copy(),
                "player_state": player_state.setdefault("users", {}).get(user_id, {}).copy(),
                "investments": ensure_investments(user_id).copy(),
                "country": country_owners.get("user_to_country", {}).get(user_id),
            }
            save_json(WIPE_BACKUP_FILE, backup)

            prev_user = balances.get(user_id, {}) if isinstance(balances.get(user_id), dict) else {}
            balances[user_id] = {
                "наличка": 0,
                "банк": 0,
                "заморожено": 0,
                "коины": int(prev_user.get("коины", 0)),
            }
            inventory.pop(user_id, None)
            population.pop(user_id, None)
            players = load_json(PLAYER_STATS_FILE, {})
            players.pop(user_id, None)
            passive_flows.setdefault("users", {}).pop(user_id, None)
            seasons_data.setdefault("user_progress", {}).pop(user_id, None)
            player_state.setdefault("users", {}).pop(user_id, None)
            investments.setdefault("users", {}).pop(user_id, None)
            old_country = country_owners.setdefault("user_to_country", {}).pop(user_id, None)
            if old_country:
                country_owners.setdefault("country_to_user", {}).pop(old_country, None)

            save_json(BALANCES_FILE, balances)
            save_inventory()
            save_json(POPULATION_FILE, population)
            save_json(PLAYER_STATS_FILE, players)
            save_passive_flows()
            save_seasons_data()
            save_player_state()
            save_investments()
            save_country_owners()

            roles_to_remove = []
            for rid in reg_settings.get("wipe_roles", []):
                role = ctx.guild.get_role(int(rid)) if str(rid).isdigit() else None
                if role and role in member.roles:
                    roles_to_remove.append(role)
            try:
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason="Вайп игрока")
                await member.edit(nick=None, reason="Вайп игрока")
            except Exception:
                pass

            await interaction.response.edit_message(embed=Embed(title="🔥 ВАЙП ИГРОКА ВЫПОЛНЕН", description=f"Данные {member.mention}, пассивные операции и прогресс сфер обнулены.", color=0xFF0000), view=None)
            self.stop()

        @discord.ui.button(label="❌ Отмена", style=ButtonStyle.secondary)
        async def cancel(self, interaction: Interaction, button: Button):
            await interaction.response.edit_message(embed=Embed(title="❎ ВАЙП ОТМЕНЁН", color=0xAAAAAA), view=None)
            self.stop()

    await ctx.send(
        embed=Embed(
            title="⚠️ ПОДТВЕРЖДЕНИЕ ВАЙПА ИГРОКА",
            description=f"Подтвердите вайп для {member.mention}\n\nПосле вайпа можно откатить через **!отменитьвайп** (до 1 часа).",
            color=0xFF0000,
        ),
        view=ConfirmPlayerWipe(),
    )


# ================== POPULATION / STATS ==================
@bot.command(name="создатьстат")
@commands.has_permissions(administrator=True)
async def создатьстат(ctx):
    draft = {"country": "", "type": "Государство", "season": "", "population": 0}
    types = ["Государство", "Регион", "ЧВК", "Организация", "Повстанцы", "Террористы"]

    def build_embed():
        embed = Embed(title="🧾 Создание стата", color=0x3498DB)
        embed.description = (
            f"**Название:** {draft['country'] or '—'}\n"
            f"**Тип:** {draft['type']}\n"
            f"**Сезон:** {draft['season'] or '—'}\n"
            f"**Население:** {fmt_num(draft['population']) if draft['population'] else '—'}"
        )
        return embed

    class StatModal(Modal):
        def __init__(self):
            super().__init__(title="Параметры стата", timeout=600)
            self.country_in = TextInput(label="Название", required=True, max_length=120, default=draft["country"])
            self.type_in = TextInput(label="Тип", required=True, default=draft["type"], placeholder=", ".join(types))
            self.season_in = TextInput(label="Сезон", required=True, max_length=120, default=draft["season"])
            self.pop_in = TextInput(label="Население", required=True, default=(str(draft["population"]) if draft["population"] else ""))
            self.add_item(self.country_in)
            self.add_item(self.type_in)
            self.add_item(self.season_in)
            self.add_item(self.pop_in)

        async def on_submit(self, interaction: Interaction):
            country_type = next((t for t in types if t.casefold() == str(self.type_in.value).strip().casefold()), None)
            if not country_type:
                await interaction.response.send_message("❌ Неверный тип записи.", ephemeral=True)
                return
            try:
                pop_val = int(str(self.pop_in.value).strip())
            except Exception:
                await interaction.response.send_message("❌ Население должно быть числом.", ephemeral=True)
                return
            draft["country"] = str(self.country_in.value).strip()
            draft["type"] = country_type
            draft["season"] = str(self.season_in.value).strip()
            draft["population"] = max(0, pop_val)
            await interaction.response.edit_message(embed=build_embed(), view=view)

    class StatView(View):
        def __init__(self):
            super().__init__(timeout=900)

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Только автор команды может настраивать.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="Открыть форму", style=ButtonStyle.primary)
        async def open_form(self, interaction: Interaction, button: Button):
            await interaction.response.send_modal(StatModal())

        @discord.ui.button(label="✅ Сохранить", style=ButtonStyle.success)
        async def save(self, interaction: Interaction, button: Button):
            if not draft["country"] or not draft["season"] or draft["population"] <= 0:
                await interaction.response.send_message("❌ Заполните все поля и укажите население > 0.", ephemeral=True)
                return
            if draft["season"] not in seasons_data.get("seasons", {}):
                await interaction.response.send_message("❌ Такой сезон не создан. Сначала !создатьсезон.", ephemeral=True)
                return
            set_country_population_for_season(draft["country"], draft["season"], int(draft["population"]), draft["type"])
            save_json(COUNTRY_STATS_FILE, country_stats)
            await interaction.response.edit_message(embed=Embed(title="✅ Статистика добавлена", description=build_embed().description, color=0x00FF00), view=None)
            self.stop()

        @discord.ui.button(label="❌ Отмена", style=ButtonStyle.secondary)
        async def cancel(self, interaction: Interaction, button: Button):
            await interaction.response.edit_message(embed=Embed(title="❎ Создание отменено", color=0xAAAAAA), view=None)
            self.stop()

    view = StatView()
    await ctx.send(embed=build_embed(), view=view)


@bot.command(name="удалитьстат")
@commands.has_permissions(administrator=True)
async def удалитьстат(ctx, *, country: str):
    resolved_country = resolve_country_name(country)
    if not resolved_country:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка",
                description=f"Страна **{country}** не найдена в статистике.",
                color=0xFF0000,
            )
        )
        return

    country_to_user, user_to_country = get_occupied_country_map()
    owner_id = country_to_user.pop(resolved_country, None)
    if owner_id is not None:
        user_to_country.pop(str(owner_id), None)

    country_stats.pop(resolved_country, None)
    save_json(COUNTRY_STATS_FILE, country_stats)
    save_country_owners()

    players = load_json(PLAYER_STATS_FILE, {})
    changed_players = False
    for user_id, country_map in list(players.items()):
        if isinstance(country_map, dict) and resolved_country in country_map:
            country_map.pop(resolved_country, None)
            changed_players = True
            if not country_map:
                players.pop(user_id, None)

    if changed_players:
        save_json(PLAYER_STATS_FILE, players)

    await ctx.send(
        embed=Embed(
            title="🗑️ Статистика удалена",
            description=f"Страна **{resolved_country}** удалена из статистики, занятых и свободных стран.",
            color=0x00FF00,
        )
    )


@bot.command(name="статы")
async def статы(ctx):
    active_season = str(seasons_data.get("active_season") or "").strip()
    if not active_season:
        await ctx.send(
            embed=Embed(
                title="ℹ️ Статы",
                description="Сезон не установлен. Используйте `!установитьсезон \"название\"`.",
                color=0x3498DB,
            )
        )
        return

    lines = []
    for country_name in sorted(country_stats.keys(), key=lambda x: str(x).casefold()):
        season_population = get_country_population_for_season(country_name, active_season)
        if season_population is not None:
            country_type = get_country_type(country_name)
            lines.append(f"• **{country_name}** — {season_population}\n↳ *{country_type}*")

    if not lines:
        await ctx.send(
            embed=Embed(
                title=f"📊 Статы сезона: {active_season}",
                description="Для этого сезона пока нет стран с населением.",
                color=0xFFA500,
            )
        )
        return

    await ctx.send(
        embed=Embed(
            title=f"📊 Статы сезона: {active_season}",
            description="\n".join(lines),
            color=0x3498DB,
        )
    )


@bot.command(name="рег")
async def рег(ctx, member: discord.Member, country: str, year: str):
    players = load_json(PLAYER_STATS_FILE, {})
    population_data = load_json(POPULATION_FILE, {})

    user_id = str(member.id)
    year_str = str(year).strip()

    resolved_country = resolve_country_name(country)
    if not resolved_country:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Страна **{country}** не найдена.", color=0xFF0000))
        return

    population_value = get_country_population_for_season(resolved_country, year_str)
    if population_value is None:
        await ctx.send(embed=Embed(title="❌ Ошибка", description=f"Нет данных по населению для **{resolved_country}** в сезоне **{year_str}**.", color=0xFF0000))
        return

    country_to_user, user_to_country = get_occupied_country_map()
    current_country = user_to_country.get(user_id)
    occupied_by = country_to_user.get(resolved_country)

    if current_country and current_country != resolved_country:
        await ctx.send(
            embed=Embed(
                title="❌ Ошибка регистрации",
                description=f"{member.mention} уже занимает страну **{current_country}**. Один игрок может занимать только одну страну.",
                color=0xFF0000,
            )
        )
        return

    if occupied_by and occupied_by != user_id:
        await ctx.send(
            embed=Embed(
                title="❌ Страна занята",
                description=f"Страна **{resolved_country}** уже занята другим игроком.",
                color=0xFF0000,
            )
        )
        return

    async def finalize_registration():
        ensure_user(user_id)
        save_json(BALANCES_FILE, balances)

        if user_id not in population_data or population_data[user_id] == 0:
            population_data[user_id] = population_value
            save_json(POPULATION_FILE, population_data)

        players.setdefault(user_id, {}).setdefault(resolved_country, {})[year_str] = population_value
        save_json(PLAYER_STATS_FILE, players)
        user_to_country[user_id] = resolved_country
        country_to_user[resolved_country] = user_id
        save_country_owners()

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send(embed=Embed(title="🧾 Регистрация", description="Какой ник выдать игроку? (или `скип`)", color=0x3498DB))
        try:
            nick_msg = await bot.wait_for("message", check=check, timeout=180)
            new_nick = nick_msg.content.strip()
            if new_nick.lower() != "скип" and new_nick:
                await member.edit(nick=new_nick)
        except Exception:
            pass

        state = ensure_player_state(user_id)
        now_ts = int(time.time())
        state["shield_until"] = now_ts + 2 * 24 * 3600
        state["happiness"] = 50
        state["happiness_pause_until"] = max(int(state.get("happiness_pause_until", 0)), state["shield_until"])
        state["last_happiness_tick"] = now_ts
        save_player_state()

        for rid in reg_settings.get("roles_add", reg_settings.get("roles", [])):
            role = ctx.guild.get_role(int(rid))
            if role:
                try:
                    await member.add_roles(role)
                except Exception:
                    pass

        for rid in reg_settings.get("roles_remove", []):
            role = ctx.guild.get_role(int(rid))
            if role:
                try:
                    await member.remove_roles(role)
                except Exception:
                    pass

        embed = Embed(title="✅ Регистрация завершена", color=0x00FF00)
        embed.add_field(name="Игрок", value=member.mention, inline=False)
        embed.add_field(name="Страна", value=resolved_country, inline=True)
        embed.add_field(name="Сезон", value=year_str, inline=True)
        embed.add_field(name="Население", value=str(population_data[user_id]), inline=False)

        await ctx.send(embed=embed)

    account_age_seconds = (discord.utils.utcnow() - member.created_at).total_seconds()
    if account_age_seconds < 30 * 24 * 3600:
        class RegistrationConfirmView(View):
            def __init__(self):
                super().__init__(timeout=120)

            async def interaction_check(self, interaction: Interaction):
                if interaction.user.id == ctx.author.id or interaction.user.guild_permissions.administrator:
                    return True
                await interaction.response.send_message("❌ Подтвердить/отклонить может только инициатор или администратор.", ephemeral=True)
                return False

            @discord.ui.button(label="✅ Подтвердить", style=ButtonStyle.success)
            async def confirm(self, interaction: Interaction, button: Button):
                await interaction.response.edit_message(
                    embed=Embed(title="✅ Подтверждено", description="Регистрация продолжается...", color=0x00FF00),
                    view=None,
                )
                await finalize_registration()
                self.stop()

            @discord.ui.button(label="❌ Отклонить", style=ButtonStyle.secondary)
            async def cancel(self, interaction: Interaction, button: Button):
                await interaction.response.edit_message(
                    embed=Embed(title="❎ Регистрация отменена", description="Команда остановлена без изменений.", color=0x808080),
                    view=None,
                )
                self.stop()

        age_days = int(account_age_seconds // 86400)
        await ctx.send(
            embed=Embed(
                title="⚠️ Предупреждение о возрасте аккаунта",
                description=(
                    f"Аккаунт {member.mention} зарегистрирован менее 30 суток назад (примерно **{age_days}** дн.).\n\n"
                    f"Подтвердите, если хотите продолжить регистрацию."
                ),
                color=0xFFAA00,
            ),
            view=RegistrationConfirmView(),
        )
        return

    await finalize_registration()


@bot.command(name="занятстраны")
async def занятстраны(ctx):
    country_to_user, _ = get_occupied_country_map()
    if not country_to_user:
        await ctx.send(embed=Embed(title="🌍 Занятые страны", description="Пока нет занятых стран.", color=0x3498DB))
        return

    lines = []
    for country_name in sorted(country_to_user.keys(), key=lambda x: str(x).casefold()):
        uid = country_to_user[country_name]
        member = ctx.guild.get_member(int(uid)) if str(uid).isdigit() else None
        owner_label = member.mention if member else f"<@{uid}>"
        lines.append(f"• **{country_name}** — {owner_label}\n↳ *{get_country_type(country_name)}*")

    await ctx.send(embed=Embed(title="🌍 Занятые страны", description="\n".join(lines), color=0x3498DB))


@bot.command(name="свободстраны")
async def свободстраны(ctx):
    country_to_user, _ = get_occupied_country_map()
    free = [c for c in country_stats.keys() if c not in country_to_user]

    if not free:
        await ctx.send(embed=Embed(title="🟢 Свободные страны", description="Свободных стран нет.", color=0x00AA55))
        return

    desc = "\n".join(f"• {c}\n↳ *{get_country_type(c)}*" for c in sorted(free, key=lambda x: str(x).casefold()))
    await ctx.send(embed=Embed(title="🟢 Свободные страны", description=desc, color=0x00AA55))


class DescriptionEditModal(Modal):
    def __init__(self, target_member: discord.Member):
        self.target_member = target_member
        state = ensure_player_state(str(target_member.id))
        current = str(state.get("admin_description") or "")
        super().__init__(title=f"Описание: {target_member.display_name}")
        self.description_input = TextInput(
            label="Текст описания",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=False,
            default=current[:1000],
            placeholder="Введите описание игрока от администрации...",
        )
        self.add_item(self.description_input)

    async def on_submit(self, interaction: Interaction):
        state = ensure_player_state(str(self.target_member.id))
        state["admin_description"] = str(self.description_input.value or "").strip()
        save_player_state()
        await interaction.response.send_message(
            embed=Embed(
                title="✅ Описание обновлено",
                description=f"Описание игрока {self.target_member.mention} сохранено.",
                color=0x00FF00,
            ),
            ephemeral=True,
        )


class DescriptionEditView(View):
    def __init__(self, requester_id: int, target_member: discord.Member):
        super().__init__(timeout=300)
        self.requester_id = int(requester_id)
        self.target_member = target_member

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.requester_id:
            return True
        if isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message("❌ У вас нет прав на это действие.", ephemeral=True)
        return False

    @discord.ui.button(label="Открыть форму описания", style=ButtonStyle.primary)
    async def open_form(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(DescriptionEditModal(self.target_member))


@bot.command(name="описание")
@commands.has_permissions(administrator=True)
async def описание(ctx, *, member_query: str):
    member = resolve_member_query(ctx.guild, member_query)
    if not member:
        await ctx.send(
            embed=Embed(
                title="❌ Игрок не найден",
                description="Используйте упоминание, ID или ник игрока.",
                color=0xFF0000,
            )
        )
        return

    await ctx.send(
        embed=Embed(
            title="📝 Описание игрока",
            description=(
                f"Игрок: {member.mention}\n"
                "Нажмите кнопку ниже, чтобы открыть форму и задать/изменить описание."
            ),
            color=0x3498DB,
        ),
        view=DescriptionEditView(ctx.author.id, member),
    )


@bot.command(name="профиль")
async def профиль(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    user = ensure_user(user_id)
    population_data = load_json(POPULATION_FILE, {})
    population_value = population_data.get(user_id, 0)
    state = ensure_player_state(user_id)
    admin_description = str(state.get("admin_description") or "").strip()
    now_ts = int(time.time())
    shield_left = max(0, int(state.get("shield_until", 0)) - now_ts)
    happiness = int(state.get("happiness", 50))
    soldiers = int(state.get("soldiers", 0))
    news_count = int(state.get("news_published", 0))
    coins_value = int(user.get("коины", 0))

    embed = Embed(title=f"📊 Профиль {member.display_name}", color=0x3498DB)
    embed.add_field(name="💰 Общий баланс", value=fmt_money(user['наличка'] + user['банк']), inline=False)
    embed.add_field(name="🪙 Серверная валюта", value=f"{fmt_num(coins_value)} {settings.get('coin_currency', 'Alta-коин')}", inline=False)
    embed.add_field(name="📝 Описание", value=admin_description or "—", inline=False)
    embed.add_field(name="🏘 Население", value=str(population_value), inline=False)
    embed.add_field(name="📰 Опубликовано новостей", value=str(news_count), inline=False)
    embed.add_field(name="🛡️ Щит", value=(format_seconds_left(shield_left) if shield_left > 0 else "нет"), inline=True)
    embed.add_field(name="🙂 Счастье", value=f"{happiness}%", inline=True)
    embed.add_field(name="🪖 Войска", value=str(soldiers), inline=True)

    class PlayerEconomyView(View):
        def __init__(self, target_member: discord.Member):
            super().__init__(timeout=180)
            self.target_member = target_member

        @discord.ui.button(label="Экономика игрока", style=ButtonStyle.primary)
        async def player_economy(self, interaction: Interaction, button: Button):
            progress_map = seasons_data.setdefault("user_progress", {}).get(str(self.target_member.id), {})
            reached = [(sphere_name, int(level)) for sphere_name, level in progress_map.items() if int(level) > 0]

            if not reached:
                await interaction.response.send_message(
                    embed=Embed(
                        title="🧩 Экономика игрока",
                        description=f"У {self.target_member.mention} пока нет прокачанных сфер.",
                        color=0xFFA500,
                    ),
                    ephemeral=True,
                )
                return

            reached.sort(key=lambda x: x[0].lower())
            lines = [f"• **{sphere_name}** — уровень **{level}**" for sphere_name, level in reached]
            await interaction.response.send_message(
                embed=Embed(
                    title=f"🧩 Экономика {self.target_member.display_name}",
                    description="\n".join(lines),
                    color=0x3498DB,
                ),
                ephemeral=True,
            )

    await ctx.send(embed=embed, view=PlayerEconomyView(member))


@bot.command(name="статистика")
@commands.has_permissions(administrator=True)
async def statistics(ctx):
    population = load_json(POPULATION_FILE, {})
    users = [(uid, data) for uid, data in balances.items() if uid != "валюта" and isinstance(data, dict)]

    total_players = len(users)
    total_balance = sum(user.get("наличка", 0) + user.get("банк", 0) for _, user in users)
    total_population = sum(population.get(uid, 0) for uid, _ in users)

    embed = Embed(title="📊 Общая статистика сервера", color=0x3498DB)
    embed.add_field(name="👥 Количество игроков", value=str(total_players), inline=False)
    embed.add_field(name="💰 Общий баланс", value=f"{total_balance} {currency}", inline=False)
    embed.add_field(name="🏘 Общее население", value=str(total_population), inline=False)
    await ctx.send(embed=embed)


# ================== START ==================
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("TOKEN"))
