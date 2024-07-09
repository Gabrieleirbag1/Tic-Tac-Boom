from requirements import *
from client_audio import ButtonSoundEffect, AmbianceSoundEffect, MusicPlayer
from client_settings import Settings, Configurations, LangueSettings

# MQTT & Socket
confs = Configurations()

confs.broker = 'localhost'
confs.port = 1883
confs.topic = "test"
confs.client_id = f'publish-{random.randint(0, 1000)}'
confs.user = 'frigiel'
confs.password = 'toto'

# Vars
app = QApplication(sys.argv)
screen_size = QDesktopWidget().screenGeometry()
screen_width, screen_height = screen_size.width(), screen_size.height()
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
username = None
syllabes = []
rules = [5, 7, 3, 2, 3, 1, 0]

# Paths
image_path = os.path.join(os.path.dirname(__file__), "images/")

main_style_file_path = os.path.join(os.path.dirname(__file__), "styles/main.qss")
main_style_file = QFile(main_style_file_path)
main_style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
main_stylesheet = QTextStream(main_style_file).readAll()

windows_style_file_path = os.path.join(os.path.dirname(__file__), "styles/windows.qss")
windows_style_file = QFile(windows_style_file_path)
windows_style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
windows_stylesheet = QTextStream(windows_style_file).readAll()

# Fonts
QFontDatabase.addApplicationFont(os.path.join(os.path.dirname(__file__), "fonts/Bubble Love Demo.otf"))
QFontDatabase.addApplicationFont(os.path.join(os.path.dirname(__file__), "fonts/Game On_PersonalUseOnly.ttf"))
QFontDatabase.addApplicationFont(os.path.join(os.path.dirname(__file__), "fonts/Chilanka-Regular.ttf"))

# Settings
settings = Settings()
langue = LangueSettings(settings.accessibility_data[2][1])

# Audio
button_sound = ButtonSoundEffect(settings)
ambiance_sound = AmbianceSoundEffect(settings)
music = MusicPlayer(settings)

def center_window(object):
    """center_window(object) : Fonction qui permet de centrer une fenêtre sur l'écran"""
    qr = object.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    object.move(qr.topLeft())