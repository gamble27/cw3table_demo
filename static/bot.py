from static.telegram_client import TelegramAPIClient
from static.database import SQLiteDatabase
from static.gspread_client import Spreadsheet
from time import time
import static.config as cfg
import re
from gspread.client import APIError
from static.config import log


class User:
    username = ""

    guild = ""
    hero = ""
    prof = ""  # class
    lvl = ""
    attack = ""
    defense = ""
    clothes = {}
    pet = ""


class AppManager:
    def __init__(self, telegram_api=cfg.TelegramClient.API, host=cfg.TelegramClient.HOST):
        # telegram api stuff
        self.telegram_client = TelegramAPIClient(telegram_api)
        self.telegram_client.set_webhook(host)

        # gspread api stuff
        self.spreadsheet = Spreadsheet(
            cfg.GSpreadClient.CREDENTIALS,
            cfg.GSpreadClient.TABLE_NAME
        )
        self.success_login_flag = True

        # shmot & users db stuff
        self.users_db = SQLiteDatabase(cfg.Databese.FILE_NAME)
        self.clothes_table = cfg.Databese.SHMOT_TABLE_NAME
        self.caravans_table = cfg.Databese.CARAVANS_TABLE_NAME
        self.admins_table = cfg.Databese.ADMINS_TABLE_NAME

        self.regex = {
            'guild': r'\[\w{1,3}\]',
            'hero': r'\][\w ]+',  # [1:]  // name of the character
            'class': r'(🛡|🏹|⚔️|⚒|⚗️|📦)Класс:',  # [0] todo:BOW RUNS
            'lvl': r'Уровень: \d{1,2}',  # [-2:]
            'atk': r'Атака: \d+',
            'def': r'🛡Защита: \d+',
            'clothes': '',
            'pet': r'.+/pet'
        }

        # available bot commands

        # just commands
        self.commands = {
            "/start":       self.handle_start,
            "/help":        self.handle_help,
            "/table":       self.handle_table,
            "/promo":       self.handle_promo,
            "/ping":        self.handle_ping,
            "/for":         self.handle_forays,
            "/forays":      self.handle_forays,
            "/add_admin":   self.handle_admin_addition,

            "/start@"+cfg.TelegramClient.BOT_USER: self.handle_start,
            "/help@"+cfg.TelegramClient.BOT_USER: self.handle_help,
            "/table@"+cfg.TelegramClient.BOT_USER: self.handle_table,
            "/promo@"+cfg.TelegramClient.BOT_USER: self.handle_promo,
            "/ping@"+cfg.TelegramClient.BOT_USER: self.handle_ping,
            "/for@"+cfg.TelegramClient.BOT_USER: self.handle_forays,
            "/forays@"+cfg.TelegramClient.BOT_USER: self.handle_forays,
            "/add_admin@"+cfg.TelegramClient.BOT_USER: self.handle_admin_addition
        }

        # those which use message text
        self.commands_with_text = {
            "/feedback": self.handle_feedback,
            "/for": self.handle_forays,
            "/forays": self.handle_forays,
            "/add_admin": self.handle_admin_addition,

            "/feedback@" + cfg.TelegramClient.BOT_USER: self.handle_feedback,
            "/for@"+cfg.TelegramClient.BOT_USER: self.handle_forays,
            "/forays@"+cfg.TelegramClient.BOT_USER: self.handle_forays,
            "/add_admin@" + cfg.TelegramClient.BOT_USER: self.handle_admin_addition
        }

        # response stuff
        self.chat_id = None  # id for current message
        self.update = None  # current API response

        # catch the bug stuff
        self.no_guild = False

    def handle_msg(self, update):
        self.update = update
        try:
            if 'message' not in self.update:
                return
            self.chat_id = self.update['message']['chat']['id']
            if "new_chat_participant" in self.update:
                # if update["new_chat_participant"]["username"] == cfg.TelegramClient.BOT_USER:
                #     self.handle_help()
                return

            if "text" not in self.update["message"]:
                return
            txt = self.update['message']['text']

            #  handle hero from @ChatWarsBot
            if 'forward_from' in self.update['message']:
                if self.update['message']['forward_from']['username'] == 'ChatWarsBot':
                    self.handle_cw3_msg()

            # handle other commands
            elif txt in self.commands:
                handler = self.commands[txt]
                handler()

            # handle those commands which need message text
            for command in self.commands_with_text:
                if command in txt:
                    handler = self.commands_with_text[command]
                    handler(txt)
                    break
        except Exception as e:
            log(e, 111)

    def handle_cw3_msg(self):
        if 'text' not in self.update['message']:
            return

        txt = self.update['message']['text']

        if   '/ach' in txt:  # hero
            self.handle_cw3_hero()
        elif 'Ты задержал' in txt or\
              'Ты пытался остановить' in txt or \
              'Ты упустил' in txt:  # caravan stop
            self.handle_cw3_caravan_stop()

    def handle_cw3_caravan_stop(self):
        # todo: refactor govnokoda, osobenno dostupa k tablice, glaza krovotochat zhe!
        username = self.update['message']['from']['username']
        stop_time_unix = self.update['message']['forward_date']
        try:
            # fetch users data
            total, last, avg_time = self.users_db.find(
                self.caravans_table,
                "username",
                "'{}'".format(username),
                "total_stops, last_stop, avg_timeout"
            )

            # update the data
            time_delta = stop_time_unix - last
            if time_delta <= 0:
                self.telegram_client.send_message(
                    self.chat_id,
                    "Не дури, это не новый корован :)"
                )
                return
            avg_time = (avg_time*(total-1) + time_delta)/(total)
            total += 1
            last = max(stop_time_unix, last)

            # write it to db
            values = {
                "total_stops":  total,
                "avg_timeout":  avg_time,
                "last_stop":    last
            }
            self.users_db.set(
                self.caravans_table,
                "username",
                "'{}'".format(username),
                values
            )

            # send statistics to user
            av_h = int(avg_time // 3600)
            av_m = int((avg_time % 3600) // 60)

            delta_h = time_delta // 3600
            delta_m = (time_delta % 3600) // 60

            # user_id = update['message']['from']['id']
            msg = """
🎮 @{name}
            
Всего стопов: 
🛑 {stops}
            
Последний интервал между корованами:
⌛️ {last_hh}h {last_mm}m
            
Средний интервал между корованами:
🛎 {av_hh}h {av_mm}m
            """.format(
                name=username,
                stops=total,
                last_hh=delta_h, last_mm=delta_m,
                av_hh=av_h, av_mm=av_m
            )
            self.telegram_client.send_message(
                self.chat_id,
                msg
            )
        except TypeError:  # user not found -> find gave NoneType
            # write user data to DB
            values = {
                "username":     username,
                "total_stops":  1,
                "last_stop":    stop_time_unix,
                "avg_timeout":  0
            }
            self.users_db.join(
                self.caravans_table,
                values
            )

            # send greeting to user :]
            self.telegram_client.send_message(
                self.chat_id,
                "Респект! Теперь я буду вести статистику твоих стопов"
            )
        except Exception as e:
            log(e)
            self.telegram_client.send_message(
                self.chat_id,
                "я обісравсь"
            )

    def handle_cw3_hero(self):
        try:
            user = self.update['message']['from']['username']
            txt = self.update['message']['text']

            # check if the hero is too old
            if self.update['message']['date'] > self.update['message']['forward_date'] + 30:
                self.telegram_client.send_message(self.chat_id,
                                                  "Этот /hero старше 30 секунд. Пришлите, пожалуйста, свежий /hero")
                return
            # update if it is ok
            self.get_user_info(user, txt)
            if self.no_guild:
                self.telegram_client.send_message(self.chat_id,
                                                  "Повторюсь. Тебе нужна гильдия для пользования ботом.")
            else:
                self.write_user_info()
                self.clean()
                self.telegram_client.send_message(self.chat_id, "Profile updated successfully")

        except Exception as e:
            log(e, 74)

    def get_user_info(self, username, text):
        User.username = username

        text_splitted = text.split("\n")
        try:
            guild = re.search(self.regex["guild"], text_splitted[0])
            if guild is None:
                self.no_guild = True
                return
            else:
                self.no_guild = False
                User.guild = guild.group(0)

            hero = re.search(self.regex["hero"], text_splitted[0])
            User.hero = hero.group(0)[1:] if hero is not None else "hero"

            prof = re.search(self.regex["class"], text)
            User.prof = prof.group(0)[0] if prof is not None else "class"

            lvl = re.search(self.regex["lvl"], text)
            User.lvl = lvl.group(0)[-2:] if lvl is not None else "level"

            attack = re.search(self.regex["atk"], text)
            User.attack = (re.search(r'\d+', attack.group(0)).group(0)
                           if attack is not None else "atk")

            defense = re.search(self.regex["def"], text)
            User.defense = (re.search(r'\d+', defense.group(0)).group(0)
                            if defense is not None else "def")

            # clothes
            for cloth, cloth_type in self.users_db.show_table(
                self.clothes_table, fields=["name", "type"]
            ):
                res = re.search(
                    r'(⚡\+(\d+))?\s?([A-Za-z\s_]*' + str(cloth) + r'[A-Za-z\s_]*)\s(\+(\d+)⚔)?\s?(\+(\d+)🛡)?',
                    ' '.join(text_splitted)
                )
                if res:
                    User.clothes[cloth_type] = res.group()

            pet = re.search(self.regex["pet"], text)
            User.pet = pet.group(0)[:-6] if pet is not None else ""

        except Exception as e:
            log(e, 104)

    def write_user_info(self):
        try:
            worksheet_list = list(map(
                lambda ws: ws.title,
                self.spreadsheet.sheet.worksheets()
            ))
            if User.guild not in worksheet_list:
                worksheet = self.spreadsheet.sheet.add_worksheet(
                    title=User.guild,
                    rows=35,
                    cols=15,
                )
                worksheet.append_row([
                    "username",

                    "character name",
                    "class",

                    "lvl",
                    "atk",
                    "def",

                    "RHand",
                    "LHand",
                    "Head",
                    "Body",
                    "Legs",
                    "Hands",
                    "Cloak",

                    "pet"
                ])
            else:
                worksheet = self.spreadsheet.sheet.worksheet(User.guild)
            try:
                user_cell = worksheet.find(User.username)
            except Exception as e:
                log(e, 172)
                user_cell = False

            if user_cell:
                worksheet.delete_row(user_cell.row)
            worksheet.append_row(self._table_row)
        except APIError as e:
            log(e, 187)
            self.spreadsheet.refresh(cfg.GSpreadClient.CREDENTIALS)
            if self.success_login_flag:
                self.success_login_flag = False
                self.write_user_info()
            else:   # second try fail handling
                self.telegram_client.send_message(
                    cfg.TelegramClient.DEV_ID,
                    "ERROR: Google Sheets API login failed"
                )
                self.success_login_flag = True
        except Exception as e:
            log(e, 186)
        # finally:
        #     self.success_login_flag = True

        # todo: sort by lvl

    @property
    def _table_row(self):
        paste = [
            User.username,

            User.hero,
            User.prof,

            User.lvl,
            User.attack,
            User.defense,
        ]

        keys = [
            "RHand",
            "LHand",
            "Head",
            "Body",
            "Legs",
            "Hands",
            "Cloak"
        ]

        for key in keys:
            if key in User.clothes:
                paste.append(User.clothes[key])
            else:
                paste.append("")

        paste.append(User.pet)

        return paste

    def handle_start(self):
        self.handle_help()

    def handle_help(self):
        msg_text = """
Привет!

Этот бот создан для учёта шмота гильдий ChatWars3. Если ты понятия не имеешь, о чём я, жми /promo
Для того, чтоб использовать бота, тебе нужно состоять в гильдии.

Информация о шмотках гильдий содержится в общем доступе Гугл таблиц, получить ссылку можешь по команде /table

Для того, чтоб обновить информацию, тебе нужно прислать /hero из @ChatWarsBot

Сообщить о баге или просто поиздеваться над говнокодом можно через /feedback

Так же бот может вести статистику приходящих корованов, для этого достаточно просто скинуть ему сообщение из @ChatWarsBot с результатом пришедшего корована.
Для того, чтобы посмотреть свою статистику, нажми /for или /forays
        """

        self.telegram_client.send_message(self.chat_id, msg_text)

    def handle_table(self):
        self.telegram_client.send_message(self.chat_id, cfg.GSpreadClient.LINK)

    def handle_promo(self):
        self.telegram_client.send_message(self.chat_id,
                                          "https://telegram.me/ChatWarsBot?start=b37f816d6c8e455ba28f4676bd12448f")

    def handle_ping(self):
        self.telegram_client.send_message(self.chat_id, "pong")

    def handle_feedback(self, text):
        feedback_words = text.split()
        if len(feedback_words) > 1:
            feedback_message = "FEEDBACK: " + ' '.join([wrd for wrd in feedback_words
                                         if '/feedback' not in wrd])
            self.telegram_client.send_message(cfg.TelegramClient.DEV_ID, feedback_message)

    def handle_forays(self, text=None):
        try:
            # precise user for foray message
            if text is None:  # this means command was given in solo or by reply
                if 'reply_to_message' in self.update['message']:  # this was a reply by admin or staff
                    username = self.update['message']['reply_to_message']['from']['username']
                    access_given = self.is_admin(
                        self.update['message']['from']['username']
                    )
                else:  # this is curious user
                    username = self.update['message']['from']['username']
                    access_given = True
            else:  # this is curious admin or staff, username given
                if len(text.split()) > 1:
                    if text.split()[1][0] == '@' and\
                       len(text.split()[1]) > 1:
                        username = text.split()[1][1:]
                    else:
                        return
                else:
                    return

                access_given = self.is_admin(
                    self.update['message']['from']['username']
                )

            # now just give it to them, if permitted
            if access_given:
                msg = self.form_foray(username)
                if msg is None:
                    self.telegram_client.send_message(
                        self.chat_id,
                        "Я такого не знаю \n┐( ˘_˘)┌"
                    )
                else:
                    self.telegram_client.send_message(
                        self.chat_id,
                        msg
                    )
            else:
                self.telegram_client.send_message(
                    self.chat_id,
                    "У вас недостаточно прав."
                )
        except KeyError as e:
            log(e)
            self.telegram_client.send_message(
                self.chat_id,
                "Кажется, у кого-то нет юзернейма."
            )

    def handle_admin_addition(self, text=None):
        try:
            # precise whom we are giving admin access
            if text is None:
                if 'reply_to_message' in self.update['message']:  # command given by reply
                    username = self.update['message']['reply_to_message']['from']['username']
                    access_given = self.is_admin(
                        self.update['message']['from']['username']
                    )
                else:
                    return
            else:  # username given
                if len(text.split()) > 1:
                    if text.split()[1][0] == '@' and \
                            len(text.split()[1]) > 1:
                        username = text.split()[1][1:]
                    else:
                        return
                else:
                    return

                access_given = self.is_admin(
                    self.update['message']['from']['username']
                )

            # now just give it to them, if permitted
            if access_given:
                # give admin access
                values = {
                    'username':     username,
                    'access_lvl':   1,
                }
                self.users_db.join(
                    self.admins_table,
                    values
                )

                # send greetings to new admin
                self.telegram_client.send_message(
                    self.chat_id,
                    "Администратор добавлен."
                )
            else:
                self.telegram_client.send_message(
                    self.chat_id,
                    "У вас недостаточно прав."
                )

        except KeyError as e:
            log(e)
            self.telegram_client.send_message(
                self.chat_id,
                "Кажется, у кого-то нет юзернейма."
            )

    def is_admin(self, username):
        access_level = self.users_db.find(
            self.admins_table,
            "username",
            "'{}'".format(username),
            "access_lvl"
        )
        if access_level is None:
            return False
        else:
            return access_level[0] > 0

    def form_foray(self, username):
        try:
            # fetch users data
            total, last, avg_time = self.users_db.find(
                self.caravans_table,
                "username",
                "'{}'".format(username),
                "total_stops, last_stop, avg_timeout"
            )

            # get it in a normal look
            time_delta = int(time()) - last

            av_h = int(avg_time // 3600)
            av_m = int((avg_time % 3600) // 60)

            delta_h = time_delta // 3600
            delta_m = (time_delta % 3600) // 60

            # user_id = update['message']['from']['id']
            msg = """
🎮 @{name}

Всего стопов: 
🛑 {stops}

Последний интервал между корованами:
⌛️ {last_hh}h {last_mm}m

Средний интервал между корованами:
🛎 {av_hh}h {av_mm}m
                        """.format(
                name=username,
                stops=total,
                last_hh=delta_h, last_mm=delta_m,
                av_hh=av_h, av_mm=av_m
            )
            return msg
        except TypeError:
            return None
        except Exception as e:
            log(e, 404)
            return None

    def clean(self):
        User.username = ""

        User.guild = ""
        User.hero = ""
        User.prof = ""  # class
        User.lvl = ""
        User.attack = ""
        User.defense = ""
        User.clothes = {}
        User.pet = ""
