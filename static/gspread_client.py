import gspread
from oauth2client.service_account import ServiceAccountCredentials
import static.config as cfg


class Spreadsheet:
    def __init__(
        self,
        credentials_json,
        spreadsheet_name=None,
        open_by_key=False,
        open_by_url=False,
        scope=('https://spreadsheets.google.com/feeds',
               'https://www.googleapis.com/auth/drive')
    ):
        # connect gspread
        self._credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_json,
            list(scope)
        )
        self.login()
        # self._account = gspread.authorize(self._credentials)
        # self._account.login()

        # open the spreadsheet
        if spreadsheet_name is not None:
            if open_by_key:
                self.sheet = self._account.open_by_key(spreadsheet_name)
            elif open_by_url:
                self.sheet = self._account.open_by_url(spreadsheet_name)
            else:
                self.sheet = self._account.open(spreadsheet_name)

            self.ID = self.sheet.id
        else:
            self.sheet = None

    def login(self):
        self._account = gspread.authorize(self._credentials)
        self._account.login()

    def refresh(self,
                new_credentials_json,
                scope=('https://spreadsheets.google.com/feeds',
                       'https://www.googleapis.com/auth/drive')
                ):
        self._credentials = self._credentials = ServiceAccountCredentials.from_json_keyfile_name(
            new_credentials_json,
            list(scope)
        )
        self.login()

    def _create_spreadsheet(self, name):
        self.sheet = self._account.create(name)
        self.ID = self.sheet.id

    def _share_spreadsheet(self, email=None, permission_type='user', role='reader'):
        if email is None:
            self._account.insert_permission(
                self.ID,
                None,
                perm_type='anyone',
                role='reader'
            )
        else:
            self.sheet.share(
                email,
                perm_type=permission_type,
                role=role
            )


if __name__ == "__main__":
    # create spreadsheet
    table = Spreadsheet(cfg.GSpreadClient.CREDENTIALS)
    # table._create_spreadsheet("CW3Table")

    # share spreadsheet
    # table = Spreadsheet(cfg.GSpreadClient.CREDENTIALS, "CW3Table")

    # table._share_spreadsheet(
    #     'admin@gmail.com',
    #     permission_type='user',
    #     role='writer'
    # )

    # table._share_spreadsheet()

    # save link
    # with open('link.txt', 'w') as f:
    #     f.write(str(table.ID))
    #     f.close()
