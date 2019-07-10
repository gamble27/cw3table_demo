class Databese:
    FILE_NAME = "/path/to/users_shmot.db"
    SHMOT_TABLE_NAME = "shmot"
    USERS_TABLE_NAME = "users_shmot"
    CARAVANS_TABLE_NAME = "caravans"
    ADMINS_TABLE_NAME = "admins"

class TelegramClient:
    API = "telegram-api-key"
    HOST = "https://site.address.com/"
    BOT_USER = "cw3_table_bot"

    DEV_ID = 123456789


class GSpreadClient:
    CREDENTIALS = "path/to/credentials.json"
    TABLE_NAME = "CW3Table"
    LINK = "https://docs.google.com/spreadsheets/your/spreadsheet/with/table"


# write a bug into log file
def log(exception, no=0):
    with open("/path/to/log.txt", 'a') as f:
        f.write(str(no))
        f.write(str(exception))
        f.write("\n")
        f.close()
