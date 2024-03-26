import sys, random, os, unidecode, re, string, threading
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from client_reception import ReceptionThread, ConnectThread
from client_utils import *
from games.tetris import Tetris, Board
from client_paint_events import *

class Login(QMainWindow):
    """Fenêtre de login pour le client"""
    login_accepted = pyqtSignal(bool)

    def __init__(self):
        """__init__() : Initialisation de la fenêtre de login"""
        super().__init__()
        self.setup()

    def setup(self):
        """setup() : Mise en place de la fenêtre de login"""
        self.setWindowTitle("Login")
        center(self)
        layout = QGridLayout()

        self.label = QLabel("Username:", self)
        layout.addWidget(self.label, 0, 0)

        self.username_edit = QLineEdit(self)
        layout.addWidget(self.username_edit, 0, 1)
        self.username_edit.setMaxLength(20)
        self.username_edit.setPlaceholderText("Entrez votre nom d'utilisateur")
        self.username_edit.setObjectName("username_edit")
        self.username_edit.textChanged.connect(self.restricted_caracters)
        self.username_edit.returnPressed.connect(self.send_username)

        self.alert_label = QLabel("", self)
        self.alert_label.setStyleSheet("color: red;")
        layout.addWidget(self.alert_label, 1, 0, 1, 2)

        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.send_username)
        layout.addWidget(self.login_button, 2, 0, 1, 2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setup_threads()

        receiver_thread.name_correct.connect(self.show_window)
    
    def restricted_caracters(self):
        """restricted_caracters() : Empêche l'utilisateur d'entrer des caractères spéciaux"""
        text = self.username_edit.text()
        text = re.sub(r'[^a-zA-ZÀ-ÿ0-9]', '', text)
        self.username_edit.setText(text)

    def setup_threads(self):
        """setup_threads() : Mise en place des threads de réception et de connexion"""
        self.connect_thread = ConnectThread()
        self.connect_thread.start()
        self.connect_thread.connection_established.connect(self.connect_to_server)

    def connect_to_server(self):
        """connect_to_server() : Se connecte au serveur"""
        receiver_thread.start()

    def send_username(self):
        """send_username() : Envoie le nom d'utilisateur au serveur"""
        global username
        username = self.username_edit.text()
        try:
            if username != "" and not username.isspace():
                client_socket.send(f"NEW_USER|{username}".encode())
                self.username_edit.clear()
        except BrokenPipeError:
            self.alert_label.setText("Connection failed")

    def show_window(self, name_correct):
        """show_wiindow() : Affiche la fenêtre principale si le nom d'utilisateur est correct
        
        Args:
            name_correct (bool): True si le nom d'utilisateur est correct, False sinon"""
        if name_correct:
            self.close()
            window.start_setup(join = False)
        else:
            self.alert_label.setText("Username already used")

class ClientWindow(QMainWindow):
    """Fenêtre principale du client"""
    correct_mdp = pyqtSignal(bool)
    in_game_signal = pyqtSignal(str, int)
    waiting_room_close_signal = pyqtSignal()
    players_number_signal = pyqtSignal(str)
    def __init__(self, join : bool = False):
        """__init__() : Initialisation de la fenêtre principale
        
        Args:
            join (bool): True si le joueur a rejoint une partie, False sinon"""
        super().__init__()
        self.join = join

        self.label_loaded = False
        self.avatarBorderBox = AvatarBorderBox()
        self.avatarBorderBox.setup_colors(self)

        receiver_thread.sylb_received.connect(self.display_sylb)
        receiver_thread.game_signal.connect(self.game_tools)
        receiver_thread.join_signal.connect(self.join_tools)
        receiver_thread.lobby_state_signal.connect(self.lobby_state_tools)

    def start_setup(self, join = False):
        """start_setup() : Mise en place de la fenêtre principale"""
        self.setup_title_screen(join)
        #self.setup(join)
        
    def setup_title_screen(self, join : bool):
        """setup_title_screen(join) : Mise en place de la fenêtre principale

        Args:
            join (bool): True si le joueur a rejoint une partie, False sinon"""
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background:transparent");
        self.showFullScreen()

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        videoWidget = QVideoWidget()
        videoWidget.setAspectRatioMode(Qt.IgnoreAspectRatio)
        videoWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
 
        widget = QWidget(self)
        self.setCentralWidget(widget)
 
        layout = QVBoxLayout()
        layout.addWidget(videoWidget)
        layout.setContentsMargins(0, 0, 0, 0)
 
        widget.setLayout(layout)
        self.mediaPlayer.setVideoOutput(videoWidget)
 
        self.openFileAutomatically()
         
    def openFileAutomatically(self):
        videoPath = os.path.join(os.path.dirname(__file__), "videos/ps2_anim.mp4")
        if os.path.exists(videoPath):
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(videoPath)))
            self.mediaPlayer.play()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent | None):
        self.setup(join = False)
        self.mouseDoubleClickEvent = self.emptyFunction
        self.keyPressEvent = self.emptyFunction

    def keyPressEvent(self, event: QKeyEvent):
        QtKeys = [Qt.Key_Tab, Qt.Key_Space, Qt.Key_Return]
        if event.key() in QtKeys:
            self.setup(join = False)
            self.keyPressEvent = self.emptyFunction
            self.mouseDoubleClickEvent = self.emptyFunction

    def emptyFunction(self, event):
        pass
                
    def setup(self, join : bool):
        """setup() : Mise en place de la fenêtre principale
        
        Args:
            join (bool): True si le joueur a rejoint une partie, False sinon"""
        rules.clear()
        rules.extend([5, 7, 3, 2, 3, 1])
        self.setWindowTitle("KABOOM")
        self.resize(500, 500)
        self.setStyleSheet(stylesheet)
        layout = QGridLayout()

        if join:
            widget = QWidget()
            widget.setLayout(layout)
            self.setCentralWidget(widget)
            return layout

        self.create_game_button = QPushButton("Créer une partie", self)
        self.create_game_button.setObjectName("create_game_pushbutton")
        layout.addWidget(self.create_game_button, 1, 0, Qt.AlignHCenter)

        self.join_game = QPushButton("Rejoindre une partie", self)
        self.join_game.setObjectName("join_game_pushbutton")
        layout.addWidget(self.join_game, 3, 0, Qt.AlignHCenter)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        self.create_game_button.clicked.connect(self.create_game_widget)
        self.creation_game = GameCreationWindow(layout)
        self.creation_game.create_game_signal.connect(lambda game_name, password, private_game: self.setup_game(layout, game_name, password, private_game))
        self.join_game.clicked.connect(lambda: self.setup_join_game(layout))

    def create_game_widget(self):
        """create_game_widget(layout) : Mise en place de la fenêtre de création de partie"""
        self.creation_game.show()
        self.creation_game.setup()

    def join_tools(self, response):
        """join_tools(response) : Gère les messages de la partie
        
        Args:
            response (str): Message de la partie"""
        reply = response.split("|")
        if reply[1] == "GAME_JOINED":
            if reply[6] == username:
                self.correct_mdp.emit(True)
                game_name = reply[2]
                game_creator = reply[3]
                password = reply[4]
                private_game = reply[5]
                layout = self.setup(join=True)
                self.join = True
                print("HAMDULLILAAAAAH", username, reply[6])
                self.setup_game(layout, game_name, password, private_game)
                self.waiting_room_close_signal.emit()
            else:
                print("Player joined")

        elif reply[1] == "WRONG_PASSWORD":
            self.correct_mdp.emit(False)
            print("Wrong password")
        
        elif reply[1] == "GET_PLAYERS":
            print("Get players")
            self.get_players(players = reply[2])
            print("Players", reply[2])

        elif reply[1] == "ALREADY_IN_GAME":
            print("Already in game")
            game_name = reply[2]
            players_number = int(reply[3])
            self.in_game_signal.emit(game_name, players_number)

        elif reply[1] == "NEW_PLAYER":
            self.players_number(game_name = reply[2], leave = False)

        elif reply[1] == "LEAVE_GAME":
            if "GAME_DELETED" in reply[3]:
                game_name = reply[4]
                print(game_name, "GAME_DELETED")
                self.delete_item(game_name)
            else:
                game_name = reply[2]
            self.players_number(game_name = game_name, leave = True)

        elif reply[1] == "GAME_FULL":
            self.message_box_dialog("La partie est pleine !")

    def game_tools(self, game_message : str):
        """game_tools(game_message) : Gère les messages de la partie

        Args:
            game_message (str): Message de la partie"""
        reply = game_message.split("|")
        print(reply, reply[1])

        if reply[1] == "GAME_ENDED":
            try:
                self.unsetup_game()
            except Exception as e:
                print(e)
            print("Game ended")

        elif reply[1] == "LIFES_RULES":
            self.ready_button.setEnabled(False)
            self.setup_hearts_rules(lifes = int(reply[2]), ready_players = reply[3])

        elif reply[1] == "TIME'S_UP":
            self.remove_heart(player = reply[2])
            if reply[2] == username:
                self.text_line_edit.setEnabled(False)
                self.text_line_edit.clear()
                self.text_label.clear()
                self.text_label.setText("⏰")

        elif reply[1] == "WRONG":
            self.text_label.clear()
            self.text_label.setText("❌")
        
        elif reply[1] == "RIGHT":
            self.text_label.clear()
            self.text_label.setText("✅")
            if reply[2] == username:
                self.text_line_edit.setEnabled(False)

    def lobby_state_tools(self, lobby_state : str):
        """lobby_state_tools(lobby_state) : Gère les messages du lobby
        
        Args:
            lobby_state (str): Message du lobby"""
        reply = lobby_state.split("|")
        if reply[1] == "NEW_CREATOR":
            self.new_creator(game_name = reply[2], creator = reply[3])
        elif reply[1] == "LEAVE_GAME":
            self.remove_a_player(game_name = reply[2], player = reply[3])
        elif reply[1] == "PLAYER_DECO":
            self.deco_a_player(player = reply[2])

    def get_players(self, players : list):
        """get_players(players) : Récupère les joueurs de la partie
        
        Args:
            players (list): Joueurs de la partie"""
        player_label_list = [self.player1_label, self.player2_label, self.player3_label, self.player4_label, self.player5_label, self.player6_label, self.player7_label, self.player8_label]
        players = players.split(",")
        for player in players:
            if player != "":
                if player in [label.text() for label in player_label_list]:
                    pass
                else:
                    for label in player_label_list:
                        if label.text() not in players:
                            label.setText(player)
                            break
                        else:
                            continue
                    # player_label_list[players.index(player)].setText(player)

    def players_number(self, game_name : str, leave : bool):
        """add_a_player(game_name) : Ajoute un joueur à la partie dans le menu pour rejoindre des parties
        
        Args:
            game_name (str): Nom de la partie
            leave (bool): True si le joueur quitte la partie, False sinon"""
        try:
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                button = self.list_widget.itemWidget(item).findChild(QPushButton)
                label = self.list_widget.itemWidget(item).findChild(QLabel, "people_label")
                #print(label.objectName())
                if button.objectName() == game_name:
                    label_number = int(label.text().split("/")[0])
                    if leave:
                        label.setText(f"{label_number - 1}/8")
                    else:
                        label.setText(f"{label_number + 1}/8")
                self.players_number_signal.emit(label.text())
        except AttributeError:
            pass
        except RuntimeError:
            pass
    
    
    def remove_a_player(self, game_name: str, player: str):
        """remove_a_player(game_name, player) : Enlève un joueur de la partie
        
        Args:
            game_name (str): Nom de la partie
            player (str): Joueur à enlever"""
        try:
            player_label_list = [self.player1_label, self.player2_label, self.player3_label, self.player4_label, self.player5_label, self.player6_label, self.player7_label, self.player8_label]
            for label in player_label_list:
                if label.text() == player or label.text() == f"<i><font color='red'>{player}</font></i>": #pourra évoluer
                    label.setText("<b><i> En attente <b> <i>")
                    break
        except IndexError:
            pass
              
    def deco_a_player(self, player : str):
        """deco_a_player(player) : Enlève un joueur de la partie
        
        Args:
            player (str): Joueur à enlever"""
        try:
            player_label_list = [self.player1_label, self.player2_label, self.player3_label, self.player4_label, self.player5_label, self.player6_label, self.player7_label, self.player8_label]
            for label in player_label_list:
                if label.text() == player:
                    label.setText(f"<i><font color='red'>{player}</font></i>")
                    break
        except IndexError:
            pass
        except RuntimeError:
            pass

    def remove_heart(self, player : str):
        """remove_heart() : Enlève un coeur au joueur"""
        if player == self.player1_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player1_label.text():
            self.heart_list_widget1.takeItem(self.heart_list_widget1.count() - 1)
        elif player == self.player2_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player2_label.text():
            self.heart_list_widget2.takeItem(self.heart_list_widget2.count() - 1)
        elif player == self.player3_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player3_label.text():
            self.heart_list_widget3.takeItem(self.heart_list_widget3.count() - 1)
        elif player == self.player4_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player4_label.text():
            self.heart_list_widget4.takeItem(self.heart_list_widget4.count() - 1)
        elif player == self.player5_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player5_label.text():
            self.heart_list_widget5.takeItem(self.heart_list_widget5.count() - 1)
        elif player == self.player6_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player6_label.text():
            self.heart_list_widget6.takeItem(self.heart_list_widget6.count() - 1)
        elif player == self.player7_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player7_label.text():
            self.heart_list_widget7.takeItem(self.heart_list_widget7.count() - 1)
        elif player == self.player8_label.text() or f"<i><font color='red'>{player}</font></i>" == self.player8_label.text():
            self.heart_list_widget8.takeItem(self.heart_list_widget8.count() - 1)

    def unsetup_game(self):
        """unsetup_game() : Reset les éléments de la partie"""
        self.start_button.setEnabled(False)
        self.ready_button.setEnabled(True)
        if not self.join:
            self.rules_button.setEnabled(True)
        self.ready_button.setText("Not Ready")
        self.text_line_edit.setEnabled(False)
        try:
            self.clear_game()
        except Exception as e:
            print(e)

    def clear_game(self):
        """clear_game() : Efface les éléments de la fenêtre de jeu"""
        self.text_label.clear()
        self.syllabe_label.clear()
        self.text_line_edit.clear()
        self.heart_list_widget1.clear()
        self.heart_list_widget2.clear()
        self.heart_list_widget3.clear()
        self.heart_list_widget4.clear()
        self.heart_list_widget5.clear()
        self.heart_list_widget6.clear()
        self.heart_list_widget7.clear()
        self.heart_list_widget8.clear()

    def new_creator(self, game_name, creator):
        """new_creator(creator) : Met à jour le créateur de la partie
        
        Args:
            creator (str): Créateur de la partie"""
        self.join = False
        self.rules_button.setEnabled(True)
        self.private_button.setEnabled(True)
        if self.private_button.text() == "🔒":
            self.password_linedit.setEnabled(True)
            self.show_password_button.setEnabled(True)
        if self.ready_button.text() == "Ready":
            self.start_button.setEnabled(True)

    def setup_game(self, layout, game_name, password, private_game):
        """setup_game(layout) : Mise en place de la fenêtre de jeu
        
        Args:
            layout (QGridLayout): Layout de la fenêtre principale
            game_name (str): Nom de la partie
            password (str): Mot de passe de la partie
            private_game (bool): True si la partie est privée, False sinon"""
        global username
        self.check_setup(layout, game_name, password, private_game)

        self.player1_label = QLabel("<b><i> En attente <b> <i>", self)
        self.player2_label = QLabel("<b><i> En attente <b> <i>", self)
        self.player3_label = QLabel("<b><i> En attente <b> <i>", self)
        self.player4_label = QLabel("<b><i> En attente <b> <i>", self)
        self.player5_label = QLabel("<b><i> En attente <b> <i>", self)
        self.player6_label = QLabel("<b><i> En attente <b> <i>", self)
        self.player7_label = QLabel("<b><i> En attente <b> <i>", self)
        self.player8_label = QLabel("<b><i> En attente <b> <i>", self)

        self.setup_heart_layout()
        self.setup_hearts_widget()
        self.setup_player_layout()
        self.setup_avatar_label()

        self.heart_layout.addWidget(self.heart_list_widget1, 0, 0, Qt.AlignHCenter)
        self.heart_layout2.addWidget(self.heart_list_widget2, 0, 0, Qt.AlignHCenter)
        self.heart_layout3.addWidget(self.heart_list_widget3, 0, 0, Qt.AlignHCenter)
        self.heart_layout4.addWidget(self.heart_list_widget4, 0, 0, Qt.AlignHCenter)
        self.heart_layout5.addWidget(self.heart_list_widget5, 0, 0, Qt.AlignHCenter)
        self.heart_layout6.addWidget(self.heart_list_widget6, 0, 0, Qt.AlignHCenter)
        self.heart_layout7.addWidget(self.heart_list_widget7, 0, 0, Qt.AlignHCenter)
        self.heart_layout8.addWidget(self.heart_list_widget8, 0, 0, Qt.AlignHCenter)

        sub_layout = QGridLayout()

        self.bomb = QPixmap(f"{image_path}mockup_bombe_1.png")
        self.bomb_label = QLabel()
        self.bomb_label.setObjectName("bomb_label")
        self.bomb_label.setPixmap(self.bomb.scaled(self.bomb_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

        self.syllabe_label = QLabel("", self)
        self.syllabe_label.setObjectName("syllabe_label")

        self.text_label = QLabel("", self)
        self.text_label.setObjectName("text_label")

        self.text_line_edit = QLineEdit(self)
        self.text_line_edit.setObjectName("text_line_edit")
        self.text_line_edit.setPlaceholderText("Entrez votre mot")
        self.text_line_edit.setEnabled(False)
        self.text_line_edit.returnPressed.connect(self.send_message)
        self.text_line_edit.textChanged.connect(self.display_text)

        sub_layout.addWidget(self.bomb_label, 0, 0, Qt.AlignHCenter)
        sub_layout.addWidget(self.syllabe_label, 1, 0, Qt.AlignHCenter)
        sub_layout.addWidget(self.text_label, 2, 0, Qt.AlignHCenter)
        sub_layout.addWidget(self.text_line_edit, 3, 0, Qt.AlignHCenter)

        self.text_widget = QWidget()
        self.text_widget.setObjectName("text_widget")
        self.text_widget.setLayout(sub_layout)

        layout.addWidget(self.player1_widget, 1, 0, Qt.AlignLeft)
        layout.addWidget(self.player2_widget, 1, 1, Qt.AlignCenter)
        layout.addWidget(self.player3_widget, 1, 2, Qt.AlignRight)
        layout.addWidget(self.player4_widget, 2, 0, Qt.AlignLeft)
        layout.addWidget(self.text_widget, 2, 1, Qt.AlignCenter)
        layout.addWidget(self.player5_widget, 2, 2, Qt.AlignRight)
        layout.addWidget(self.player6_widget, 3, 0, Qt.AlignLeft)
        layout.addWidget(self.player7_widget, 3, 1, Qt.AlignCenter)
        layout.addWidget(self.player8_widget, 3, 2, Qt.AlignRight)

        self.player1_layout.addWidget(self.player1_label, 0, Qt.AlignHCenter)
        self.player2_layout.addWidget(self.player2_label, 0, Qt.AlignHCenter)
        self.player3_layout.addWidget(self.player3_label, 0, Qt.AlignHCenter)
        self.player4_layout.addWidget(self.player4_label, 0, Qt.AlignHCenter)
        self.player5_layout.addWidget(self.player5_label, 0, Qt.AlignHCenter)
        self.player6_layout.addWidget(self.player6_label, 0, Qt.AlignHCenter)
        self.player7_layout.addWidget(self.player7_label, 0, Qt.AlignHCenter)
        self.player8_layout.addWidget(self.player8_label, 0, Qt.AlignHCenter)

        self.player1_layout.addWidget(self.player1_avatar_label, 1, Qt.AlignHCenter)
        self.player2_layout.addWidget(self.player2_avatar_label, 1, Qt.AlignHCenter)
        self.player3_layout.addWidget(self.player3_avatar_label, 1, Qt.AlignHCenter)
        self.player4_layout.addWidget(self.player4_avatar_label, 1, Qt.AlignHCenter)
        self.player5_layout.addWidget(self.player5_avatar_label, 1, Qt.AlignHCenter)
        self.player6_layout.addWidget(self.player6_avatar_label, 1, Qt.AlignHCenter)
        self.player7_layout.addWidget(self.player7_avatar_label, 1, Qt.AlignHCenter)
        self.player8_layout.addWidget(self.player8_avatar_label, 1, Qt.AlignHCenter)

        self.player1_layout.addWidget(self.heart_widget_player1)
        self.player2_layout.addWidget(self.heart_widget_player2)
        self.player3_layout.addWidget(self.heart_widget_player3)
        self.player4_layout.addWidget(self.heart_widget_player4)
        self.player5_layout.addWidget(self.heart_widget_player5)
        self.player6_layout.addWidget(self.heart_widget_player6)
        self.player7_layout.addWidget(self.heart_widget_player7)
        self.player8_layout.addWidget(self.heart_widget_player8)

        self.home_button = QPushButton("Home", self)
        self.home_button.setObjectName("home_pushbutton")
        self.home_button.clicked.connect(self.delete_game)
        
        self.private_button = QPushButton("🌐", self)
        self.private_button.setObjectName("private_pushbutton")
        self.private_button.clicked.connect(self.game_state)
        self.private_button.setFixedWidth(40)

        self.password_linedit = QLineEdit(self)
        self.password_linedit.setObjectName("password_linedit")
        self.password_linedit.setPlaceholderText("Mot de passe")
        self.password_linedit.setEchoMode(QLineEdit.Password)
        self.password_linedit.setText(password)
        self.password_linedit.setEnabled(False)
        self.password_linedit.setMaxLength(30)
        self.password_linedit.setFixedWidth(180)
        self.password_linedit.textChanged.connect(lambda: self.restricted_caracters(self.password_linedit))

        self.show_password_button = QPushButton("🔑", self)
        self.show_password_button.setObjectName("show_password_pushbutton")
        self.show_password_button.clicked.connect(self.show_password)
        self.show_password_button.setEnabled(False)

        self.rules_button = QPushButton("Règles", self)
        self.rules_button.setObjectName("rules_pushbutton")
        self.rules_button.clicked.connect(self.display_rules)

        self.ready_button = QPushButton("Not Ready", self)
        self.ready_button.setObjectName("ready_pushbutton")
        self.ready_button.setEnabled(True)
        self.ready_button.clicked.connect(self.ready)

        self.start_button = QPushButton("Start", self)
        self.start_button.setObjectName("start_pushbutton")
        self.start_button.clicked.connect(lambda: self.start_game(game_name))
        self.start_button.setEnabled(False)

        self.game_name_label = QLabel(f"<b>{game_name}<b>", self)
        self.game_name_label.setObjectName("game_name_label")
        layout.addWidget(self.game_name_label, 0, 1, Qt.AlignHCenter)
        
        layout.addWidget(self.home_button, 0, 0, Qt.AlignLeft)
        self.password_layout = QHBoxLayout()
        self.password_layout.addWidget(self.private_button)
        self.password_layout.addWidget(self.password_linedit)
        self.password_layout.addWidget(self.show_password_button)
        self.show_password_button.setFixedWidth(40)

        print(private_game, "PRIVATE GAAAAAAAAAME") # True or False (mais string)
        if private_game == "True":
            private_game = True
        elif private_game == "False":
            private_game = False

        if private_game:
            self.private_button.setText("🔒")
            self.password_linedit.setEnabled(True)
            self.show_password_button.setEnabled(True)
        else:
            self.private_button.setText("🌐")
            self.password_linedit.setEnabled(False)
            self.show_password_button.setEnabled(False)
        
        if self.join: # Si le joueur a rejoint une partie
            self.private_button.setEnabled(False)
            self.password_linedit.setEnabled(False)
            self.show_password_button.setEnabled(False)
            self.rules_button.setEnabled(False)
        else:
            self.player1_label.setText(username)

        layout.addLayout(self.password_layout, 0, 2, Qt.AlignRight)
        layout.addWidget(self.rules_button, 4, 0, Qt.AlignLeft)
        layout.addWidget(self.ready_button, 4, 1)
        layout.addWidget(self.start_button, 4, 2, Qt.AlignRight)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.set_border_properties()


    def restricted_caracters(self, line_edit):
        """restricted_caracters() : Empêche l'utilisateur d'entrer des caractères spéciaux"""
        text = line_edit.text()
        text = re.sub(r'[^a-zA-ZÀ-ÿ0-9]', '', text)
        line_edit.setText(text)

    def check_setup(self, layout, game_name, password, private_game):
        """check_setup(layout, game_name, password, private_game) : Gère des éléments en fonction du type de partie
        
        Args:
            layout (QGridLayout): Layout de la fenêtre principale
            game_name (str): Nom de la partie
            password (str): Mot de passe de la partie
            private_game (bool): True si la partie est privée, False sinon"""
        if not self.join:
            self.create_game(game_name, password, private_game)
        else:
            self.game_name = game_name
            self.join_game_as_a_player(username, game_name)
        try:
            layout.removeWidget(self.create_game_button)
            layout.removeWidget(self.join_game)
        except:
            pass

    def game_state(self):
        """game_state() : Permet de modifier l'état de la prtie"""
        if self.private_button.text() == "🌐":
            self.private_button.setText("🔒")
            self.password_linedit.setEnabled(True)
            self.show_password_button.setEnabled(True)
        else:
            self.private_button.setText("🌐")
            self.password_linedit.setEnabled(False)
            self.show_password_button.setEnabled(False)
            self.password_linedit.setEchoMode(QLineEdit.Password)

    def show_password(self):
        """show_password() : Affiche le mot de passe"""
        if self.password_linedit.echoMode() == QLineEdit.Password:
            self.password_linedit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_linedit.setEchoMode(QLineEdit.Password)

    def setup_heart_layout(self):
        """setup_heart_layout() : Mise en place des coeurs des joueurs"""
        self.coeur = QPixmap(f"{image_path}coeur-resized.png")
        self.heart_layout = QGridLayout()
        self.heart_widget_player1 = QWidget()
        self.heart_widget_player1.setObjectName("heart_widget")
        self.heart_widget_player1.setLayout(self.heart_layout)

        self.heart_layout2 = QGridLayout()
        self.heart_widget_player2 = QWidget()
        self.heart_widget_player2.setObjectName("heart_widget2")
        self.heart_widget_player2.setLayout(self.heart_layout2)

        self.heart_layout3 = QGridLayout()
        self.heart_widget_player3 = QWidget()
        self.heart_widget_player3.setObjectName("heart_widget3")
        self.heart_widget_player3.setLayout(self.heart_layout3)

        self.heart_layout4 = QGridLayout()
        self.heart_widget_player4 = QWidget()
        self.heart_widget_player4.setObjectName("heart_widget4")
        self.heart_widget_player4.setLayout(self.heart_layout4)

        self.heart_layout5 = QGridLayout()
        self.heart_widget_player5 = QWidget()
        self.heart_widget_player5.setObjectName("heart_widget5")
        self.heart_widget_player5.setLayout(self.heart_layout5)

        self.heart_layout6 = QGridLayout()
        self.heart_widget_player6 = QWidget()
        self.heart_widget_player6.setObjectName("heart_widget6")
        self.heart_widget_player6.setLayout(self.heart_layout6)

        self.heart_layout7 = QGridLayout()
        self.heart_widget_player7 = QWidget()
        self.heart_widget_player7.setObjectName("heart_widget7")
        self.heart_widget_player7.setLayout(self.heart_layout7)

        self.heart_layout8 = QGridLayout()
        self.heart_widget_player8 = QWidget()
        self.heart_widget_player8.setObjectName("heart_widget8")
        self.heart_widget_player8.setLayout(self.heart_layout8)

    def setup_player_layout(self):
        """setup_player_layout() : Mise en place des layouts des joueurs"""
        self.player1_widget = QWidget()
        self.player1_widget.setObjectName("player1_widget")
        self.player1_layout = QVBoxLayout()
        self.player1_widget.setLayout(self.player1_layout)

        self.player2_widget = QWidget()
        self.player2_widget.setObjectName("player2_widget")
        self.player2_layout = QVBoxLayout()
        self.player2_widget.setLayout(self.player2_layout)

        self.player3_widget = QWidget()
        self.player3_widget.setObjectName("player3_widget")
        self.player3_layout = QVBoxLayout()
        self.player3_widget.setLayout(self.player3_layout)

        self.player4_widget = QWidget()
        self.player4_widget.setObjectName("player4_widget")
        self.player4_layout = QVBoxLayout()
        self.player4_widget.setLayout(self.player4_layout)

        self.player5_widget = QWidget()
        self.player5_widget.setObjectName("player5_widget")
        self.player5_layout = QVBoxLayout()
        self.player5_widget.setLayout(self.player5_layout)

        self.player6_widget = QWidget()
        self.player6_widget.setObjectName("player6_widget")
        self.player6_layout = QVBoxLayout()
        self.player6_widget.setLayout(self.player6_layout)

        self.player7_widget = QWidget()
        self.player7_widget.setObjectName("player7_widget")
        self.player7_layout = QVBoxLayout()
        self.player7_widget.setLayout(self.player7_layout)

        self.player8_widget = QWidget()
        self.player8_widget.setObjectName("player8_widget")
        self.player8_layout = QVBoxLayout()
        self.player8_widget.setLayout(self.player8_layout)

    def setup_avatar_label(self):
        self.no_avatar = QPixmap(f"{image_path}no-avatar.png")
        self.tasse_avatar = QPixmap(f"{image_path}tasse-avatar.png")
        
        self.player1_avatar_label = QLabel()
        self.player1_avatar_label.setObjectName("player1_avatar_label")
        self.player1_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player1_avatar_label.setPixmap(self.tasse_avatar.scaled(self.player1_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player1_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

        self.player2_avatar_label = QLabel()
        self.player2_avatar_label.setObjectName("player2_avatar_label")
        self.player2_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player2_avatar_label.setPixmap(self.no_avatar.scaled(self.player2_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player2_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

        self.player3_avatar_label = QLabel()
        self.player3_avatar_label.setObjectName("player3_avatar_label")
        self.player3_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player3_avatar_label.setPixmap(self.no_avatar.scaled(self.player3_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player3_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

        self.player4_avatar_label = QLabel()
        self.player4_avatar_label.setObjectName("player4_avatar_label")
        self.player4_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player4_avatar_label.setPixmap(self.no_avatar.scaled(self.player4_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player4_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

        self.player5_avatar_label = QLabel()
        self.player5_avatar_label.setObjectName("player5_avatar_label")
        self.player5_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player5_avatar_label.setPixmap(self.no_avatar.scaled(self.player5_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player5_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

        self.player6_avatar_label = QLabel()
        self.player6_avatar_label.setObjectName("player6_avatar_label")
        self.player6_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player6_avatar_label.setPixmap(self.no_avatar.scaled(self.player6_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player6_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

        self.player7_avatar_label = QLabel()
        self.player7_avatar_label.setObjectName("player7_avatar_label")
        self.player7_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player7_avatar_label.setPixmap(self.no_avatar.scaled(self.player7_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player7_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

        self.player8_avatar_label = QLabel()
        self.player8_avatar_label.setObjectName("player8_avatar_label")
        self.player8_avatar_label.setFixedSize(int(screen_width / 6), int(screen_height / 6))
        self.player8_avatar_label.setPixmap(self.no_avatar.scaled(self.player8_avatar_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.player8_avatar_label.setAlignment(Qt.AlignCenter)  # Center the image

    def setup_hearts_widget(self):
        """setup_hearts_widget() : Mise en place des coeurs des joueurs"""
        self.heart_list_widget1 = QListWidget()
        self.heart_list_widget1.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget1.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget1.setSpacing(5)
        self.heart_list_widget1.setFixedSize(103, 20)
        self.heart_list_widget1.setObjectName("heart_list_widget1")
        self.heart_list_widget1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget1.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.heart_list_widget2 = QListWidget()
        self.heart_list_widget2.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget2.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget2.setSpacing(5)
        self.heart_list_widget2.setFixedSize(103, 20)
        self.heart_list_widget2.setObjectName("heart_list_widget2")
        self.heart_list_widget2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.heart_list_widget3 = QListWidget()
        self.heart_list_widget3.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget3.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget3.setSpacing(5)
        self.heart_list_widget3.setFixedSize(103, 20)
        self.heart_list_widget3.setObjectName("heart_list_widget3")
        self.heart_list_widget3.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget3.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.heart_list_widget4 = QListWidget()
        self.heart_list_widget4.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget4.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget4.setSpacing(5)
        self.heart_list_widget4.setFixedSize(103, 20)
        self.heart_list_widget4.setObjectName("heart_list_widget4")
        self.heart_list_widget4.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget4.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.heart_list_widget5 = QListWidget()
        self.heart_list_widget5.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget5.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget5.setSpacing(5)
        self.heart_list_widget5.setFixedSize(103, 20)
        self.heart_list_widget5.setObjectName("heart_list_widget5")
        self.heart_list_widget5.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget5.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.heart_list_widget6 = QListWidget()
        self.heart_list_widget6.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget6.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget6.setSpacing(5)
        self.heart_list_widget6.setFixedSize(103, 20)
        self.heart_list_widget6.setObjectName("heart_list_widget6")
        self.heart_list_widget6.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget6.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.heart_list_widget7 = QListWidget()
        self.heart_list_widget7.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget7.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget7.setSpacing(5)
        self.heart_list_widget7.setFixedSize(103, 20)
        self.heart_list_widget7.setObjectName("heart_list_widget7")
        self.heart_list_widget7.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget7.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.heart_list_widget8 = QListWidget()
        self.heart_list_widget8.setFlow(QListWidget.LeftToRight)
        self.heart_list_widget8.setWrapping(True) # Permet de faire passer les coeurs à la ligne
        self.heart_list_widget8.setSpacing(5)
        self.heart_list_widget8.setFixedSize(103, 20)
        self.heart_list_widget8.setObjectName("heart_list_widget8")
        self.heart_list_widget8.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heart_list_widget8.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def setup_hearts_rules(self, lifes : int, ready_players : str):
        """setup_hearts_rules() : Mise en place des coeurs en fonction des règles de la partie"""
        ready_players = ready_players.split(",")
        if self.player1_label.text() in ready_players:
            for i in range(0, lifes):
                self.heart_label1 = QLabel()
                self.heart_label1.setPixmap(self.coeur)
                item1 = QListWidgetItem()
                item1.setSizeHint(self.heart_label1.sizeHint())
                self.heart_list_widget1.addItem(item1)
                self.heart_list_widget1.setItemWidget(item1, self.heart_label1)
        if self.player2_label.text() in ready_players:        
            for i in range(0, lifes):
                self.heart_label2 = QLabel()
                self.heart_label2.setPixmap(self.coeur)
                item2 = QListWidgetItem()
                item2.setSizeHint(self.heart_label2.sizeHint())
                self.heart_list_widget2.addItem(item2)
                self.heart_list_widget2.setItemWidget(item2, self.heart_label2)
        if self.player3_label.text() in ready_players:
            for i in range(0, lifes):
                self.heart_label3 = QLabel()
                self.heart_label3.setPixmap(self.coeur)
                item3 = QListWidgetItem()
                item3.setSizeHint(self.heart_label3.sizeHint())
                self.heart_list_widget3.addItem(item3)
                self.heart_list_widget3.setItemWidget(item3, self.heart_label3)
        if self.player4_label.text() in ready_players:
            for i in range(0, lifes):
                self.heart_label4 = QLabel()
                self.heart_label4.setPixmap(self.coeur)
                item4 = QListWidgetItem()
                item4.setSizeHint(self.heart_label4.sizeHint())
                self.heart_list_widget4.addItem(item4)
                self.heart_list_widget4.setItemWidget(item4, self.heart_label4)
        if self.player5_label.text() in ready_players:
            for i in range(0, lifes):
                self.heart_label5 = QLabel()
                self.heart_label5.setPixmap(self.coeur)
                item5 = QListWidgetItem()
                item5.setSizeHint(self.heart_label5.sizeHint())
                self.heart_list_widget5.addItem(item5)
                self.heart_list_widget5.setItemWidget(item5, self.heart_label5)
        if self.player6_label.text() in ready_players:
            for i in range(0, lifes):
                self.heart_label6 = QLabel()
                self.heart_label6.setPixmap(self.coeur)
                item6 = QListWidgetItem()
                item6.setSizeHint(self.heart_label6.sizeHint())
                self.heart_list_widget6.addItem(item6)
                self.heart_list_widget6.setItemWidget(item6, self.heart_label6)
        if self.player7_label.text() in ready_players:
            for i in range(0, lifes):
                self.heart_label7 = QLabel()
                self.heart_label7.setPixmap(self.coeur)
                item7 = QListWidgetItem()
                item7.setSizeHint(self.heart_label7.sizeHint())
                self.heart_list_widget7.addItem(item7)
                self.heart_list_widget7.setItemWidget(item7, self.heart_label7)
        if self.player8_label.text() in ready_players:
            for i in range(0, lifes):
                self.heart_label8 = QLabel()
                self.heart_label8.setPixmap(self.coeur)
                item8 = QListWidgetItem()
                item8.setSizeHint(self.heart_label8.sizeHint())
                self.heart_list_widget8.addItem(item8)
                self.heart_list_widget8.setItemWidget(item8, self.heart_label8)

    def delete_game(self):
        """delete_game() : Supprime la partie"""
        global username
        error = QMessageBox(self)
        error.setWindowTitle("Quitter la partie")
        content = f"Êtes vous sûr de vouloir quitter la partie ?"
        error.setText(content)
        ok_button = error.addButton(QMessageBox.Ok)
        ok_button.clicked.connect(self.self_join_state)
        ok_button.clicked.connect(lambda: self.setup(join=False))
        ok_button.clicked.connect(lambda: client_socket.send(f"LEAVE_GAME|{self.game_name}|{username}".encode()))
        cancel_button = error.addButton(QMessageBox.Cancel)
        error.setIcon(QMessageBox.Warning)
        error.exec()

    def self_join_state(self):
        """self_join_state() : Indique que le joueur a rejoint la partie"""
        self.join = False
        self.avatarBorderBox.kill_timer(self)
        self.label_loaded = False

    def create_game(self, game_name, password, private_game):
        """create_game() : Crée une partie
        
        Args:
            game_name (str): Nom de la partie
            password (str): Mot de passe de la partie
            private_game (bool): True si la partie est privée, False sinon"""
        global username
        message = f"CREATE_GAME|{username}|{game_name}|{password}|{private_game}"
        self.game_name = game_name
        client_socket.send(message.encode())

    def join_game_as_a_player(self, username, game_name):
        """join_game_as_a_player(username, game_name) : Rejoint une partie en tant que joueur
        
        Args:
            username (str): Nom d'utilisateur
            game_name (str): Nom de la partie"""
        message = f"JOIN_GAME_AS_A_PLAYER|{username}|{game_name}"
        print("join game as a player")
        client_socket.send(message.encode())

    def start_game(self, game_name):
        """start_game() : Lance la partie
        
        Args:
            game_name (str): Nom de la partie"""
        global username
        self.start_button.setEnabled(False)
        self.ready_button.setEnabled(False)
        self.rules_button.setEnabled(False)
        message = f"START_GAME|{username}|{game_name}|{rules[0]}|{rules[1]}|{rules[2]}|{rules[3]}|{rules[4]}|{rules[5]}"
        client_socket.send(message.encode())

    def ready(self):
        """ready() : Indique au serveur que le joueur est prêt"""
        global username
        if not self.join:
            if self.start_button.isEnabled():
                self.start_button.setEnabled(False)
            else:
                self.start_button.setEnabled(True)

            if self.rules_button.isEnabled():
                self.rules_button.setEnabled(False)
            else:
                self.rules_button.setEnabled(True)
            message = f"READY_TO_PLAY|{username}"
        else:
            message = f"READY_TO_PLAY_JOIN|{username}"
        client_socket.send(message.encode())

        if self.ready_button.text() == "Ready":
            self.ready_button.setText("Not ready")
        else:
            self.ready_button.setText("Ready")

    def setup_join_game(self, layout : QGridLayout):
        """setup_join_game(layout) : Mise en place de la fenêtre pour rejoindre une partie
        
        Args:
            layout (QGridLayout): Layout de la fenêtre principale"""
        layout.removeWidget(self.create_game_button)
        layout.removeWidget(self.join_game)

        layout = QVBoxLayout()

        self.home_button = QPushButton("Home", self)
        self.home_button.setObjectName("home_pushbutton")
        self.home_button.clicked.connect(self.self_join_state)
        self.home_button.clicked.connect(lambda: self.setup(join=False))
        self.home_button.clicked.connect(lambda: client_socket.send("MENU|".encode()))
        layout.addWidget(self.home_button)
        # Création du QListWidget
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        receiver_thread.game_created.connect(self.add_item)
        receiver_thread.game_deleted.connect(self.delete_item)
        client_socket.send(f"GET_GAMES|{username}".encode())


    def display_sylb(self, sylb : str, player : str):
        """display_sylb(sylb) : Affiche la syllabe dans la fenêtre principale
        
        Args:
            sylb (str): Syllabe à afficher
            player (str: Pseudo du joueur)"""
        self.syllabe_label.setText(sylb)
        if player == username:
            self.text_line_edit.setEnabled(True)
            self.text_line_edit.setFocus()

    def add_item(self, game_name, private_game, players_number) -> None:
        """Ajoute un élément au QListWidget"""
        #print("add item", game_name, private_game)
        # Vérifier si l'objet existe déjà
        try:
            if not self.list_widget.findChild(QPushButton, game_name):     
                self.private_game_label = QLabel("🔒")
                if private_game == "False":
                    self.private_game_label.setText("🌐")
                self.join_game_pushbutton = QPushButton(f"{game_name}")
                self.join_game_pushbutton.setObjectName(game_name)
                self.people_label = QLabel(f"{players_number}/8")
                self.people_label.setObjectName("people_label")
                item = QListWidgetItem(self.list_widget)
                item_widget = QWidget()
                item_widget.setObjectName(game_name)
                item_layout = QHBoxLayout(item_widget)
                item_layout.addWidget(self.private_game_label)
                item_layout.addWidget(self.people_label)
                item_layout.addWidget(self.join_game_pushbutton)
                item_layout.setStretch(2, 1)
                item_widget.setLayout(item_layout)
                item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, item_widget)
                
                self.join_game_pushbutton.clicked.connect(lambda: self.show_join_window(game_name, private_game))
            else:
                return
        except RuntimeError:
            pass
        
    def show_join_window(self, game_name, private_game):
        """show_join_window(game_name) : Affiche la fenêtre de mot de passe
        
        Args:
            game_name (str): Nom de la partie"""
        private_game = self.bool_convert(private_game)
        self.join_window = JoinGameWindow(game_name, private_game)
        if private_game:
            self.join_window.show()
            self.join_window.setup()
        else:
            try:
                self.join_window.join_lobby()
            except Exception as e:
                print(e, "join lobby")

    def bool_convert(self, private_game) -> bool:
        if private_game == "False":
            return False
        else:
            return True
        
    def delete_item(self, creator):
        """delete_item(creator) : Supprime un élément du QListWidget
        
        Args:
            creator (str): Créateur de la partie"""
        try:
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                button = self.list_widget.itemWidget(item).findChild(QPushButton)
                if button.objectName() == creator:
                    row = self.list_widget.row(item)
                    self.list_widget.takeItem(row)
                    break
        except RuntimeError:
            pass

    def send_message(self):
        """send_message() : Envoie un message au serveur"""
        global username
        syllabe = syllabes[-1]
        message = f"NEW_SYLLABE|{username}|{self.text_line_edit.text()}|{syllabe}"
        client_socket.send(message.encode())
        self.text_line_edit.clear()

    def display_text(self):
        """display_text() : Affiche le texte dans le label de la fenêtre principale"""
        self.send_syllabe_mqtt()
        text = self.text_line_edit.text()
        syllabe = syllabes[-1]
        text = re.sub(r'[^a-zA-ZÀ-ÿ]', '', text)
        self.text_line_edit.setText(text)
        highlighted_text = text.lower()        
        for s in [syllabe, syllabe.upper(), syllabe.lower(), syllabe.capitalize(), syllabe.upper().capitalize()]:
            if s in text or unidecode.unidecode(s) in unidecode.unidecode(text).upper():
                text = text.lower()
                highlighted_text = text.replace(s, f"<b>{s}</b>")
        self.text_label.setText(highlighted_text)

    def send_syllabe_mqtt(self):
        """send_syllabe_mqtt() : Envoie une syllabe sur le serveur MQTT"""
        pass

    def display_rules(self):
        """display_rules() : Affiche les règles du jeu"""
        self.rules_window = RulesWindow()

    # def resizeEvent(self, event):
    #     """resizeEvent(event) : Redimensionne les éléments de la fenêtre principale"""
    #     font_size = min(self.width(), self.height()) // 30
    #     font = QFont("Arial", font_size)

    #     try:
    #         self.player1_label.setFont(font)
    #         self.player2_label.setFont(font)
    #         self.player3_label.setFont(font)
    #         self.player4_label.setFont(font)
    #         self.player5_label.setFont(font)
    #         self.player6_label.setFont(font)
    #         self.player7_label.setFont(font)
    #         self.player8_label.setFont(font)
    #         self.text_label.setFont(font)
    #         self.syllabe_label.setFont(font)
    #     except AttributeError:
    #         pass
    def message_box_dialog(self, message):
        """message_box_dialog(message) : Affiche une boîte de dialogue
        
        Args:
            message (str): Message à afficher"""
        error = QMessageBox(self)
        error.setWindowTitle("Erreur")
        error.setText(message)
        error.setIcon(QMessageBox.Warning)
        error.exec()

    def set_border_properties(self):
        self.labels = [self.player1_avatar_label, self.player2_avatar_label, self.player3_avatar_label, self.player4_avatar_label, self.player5_avatar_label, self.player6_avatar_label, self.player7_avatar_label, self.player8_avatar_label]
        self.avatarBorderBox.setup_timer(self)
        self.label_loaded = True

    def paintEvent(self, event):
        """paintEvent(event) : Dessine les bordures animées"""
        if self.label_loaded:
            self.avatarBorderBox.border(self, self.labels)

class RulesWindow(QMainWindow):
    """Fenêtre des règles du jeu"""
    def __init__(self):
        """__init__() : Initialisation de la fenêtre des règles"""
        super().__init__()
        self.setup()
        self.show()
        self.setWindowModality(Qt.ApplicationModal)

    def setup(self):
        """setup() : Mise en place de la fenêtre des règles"""
        self.setWindowTitle("Règles")
        self.resize(int(screen_width // 2.5), int(screen_height // 2.2))
        center(self)
        self.setStyleSheet(stylesheet)
        layout = QGridLayout()

        self.timerulemin_label = QLabel("Temps minimum avant explosion :", self)
        self.timerulemin_label.setObjectName("timerulemin_label")
        self.timerulemin_label.setFixedSize(400, 50) 
        layout.addWidget(self.timerulemin_label, 0, 0)

        self.timerulemin_spinbox= QSpinBox(self)
        self.timerulemin_spinbox.setObjectName("timerulemin_spinbox")
        self.timerulemin_spinbox.setMaximum(20)
        self.timerulemin_spinbox.setMinimum(2)
        self.timerulemin_spinbox.setValue(rules[0])
        self.timerulemin_spinbox.valueChanged.connect(self.check_timerulemax)
        layout.addWidget(self.timerulemin_spinbox, 1, 0)

        self.timerulemax_label = QLabel("Temps maximum après explosion :", self)
        self.timerulemax_label.setFixedSize(400, 50) 
        self.timerulemax_label.setObjectName("timerulemax_label")
        layout.addWidget(self.timerulemax_label, 2, 0)

        self.timerulemax_spinbox = QSpinBox(self)
        self.timerulemax_spinbox.setObjectName("timerulemax_spinbox")
        self.timerulemax_spinbox.setMaximum(30)
        self.timerulemax_spinbox.setMinimum(self.timerulemin_spinbox.value() + 2)
        self.timerulemax_spinbox.setValue(rules[1])
        layout.addWidget(self.timerulemax_spinbox, 3, 0)

        self.lifes_label = QLabel("Nombre de vies :", self)
        self.lifes_label.setObjectName("lifes_label")
        self.lifes_label.setFixedSize(400, 50)
        layout.addWidget(self.lifes_label, 5, 0)

        self.lifes_spinbox = QSpinBox(self)
        self.lifes_spinbox.setObjectName("lifes_spinbox")
        self.lifes_spinbox.setMaximum(12)
        self.lifes_spinbox.setMinimum(1)
        self.lifes_spinbox.setValue(rules[2])
        layout.addWidget(self.lifes_spinbox, 6, 0)

        self.syllabes_label_min = QLabel("Nombre lettres par syllabes syllabes (min):", self)
        self.syllabes_label_min.setObjectName("syllabes_label_min")
        self.syllabes_label_min.setFixedSize(400, 50)
        layout.addWidget(self.syllabes_label_min, 7, 0)

        self.syllabes_spinbox_min = QSpinBox(self)
        self.syllabes_spinbox_min.setObjectName("syllabes_spinbox_min")
        self.syllabes_spinbox_min.setMaximum(5)
        self.syllabes_spinbox_min.setMinimum(1)
        self.syllabes_spinbox_min.setValue(rules[3])
        self.syllabes_spinbox_min.valueChanged.connect(self.check_syllabesmax)
        layout.addWidget(self.syllabes_spinbox_min, 8, 0)

        self.syllabes_label_max = QLabel("Nombre lettres par syllabes syllabes (max):", self)
        self.syllabes_label_max.setObjectName("syllabes_label_max")
        self.syllabes_label_max.setFixedSize(400, 50)
        layout.addWidget(self.syllabes_label_max, 9, 0)

        self.syllabes_spinbox_max = QSpinBox(self)
        self.syllabes_spinbox_max.setObjectName("syllabes_spinbox_max")
        self.syllabes_spinbox_max.setMaximum(5)
        self.syllabes_spinbox_max.setMinimum(1)
        self.syllabes_spinbox_max.setValue(rules[4])
        layout.addWidget(self.syllabes_spinbox_max, 10, 0)

        self.repetition_label = QLabel("Répétition de syllabes :", self)
        self.repetition_label.setObjectName("repetition_label")
        self.repetition_label.setFixedSize(400, 50)
        layout.addWidget(self.repetition_label, 11, 0)

        self.repetition_spinbox = QSpinBox(self)
        self.repetition_spinbox.setObjectName("repetition_spinbox")
        self.repetition_spinbox.setMaximum(8)
        self.repetition_spinbox.setMinimum(0)
        print(rules[5], rules, "regles")
        self.repetition_spinbox.setValue(rules[5])
        layout.addWidget(self.repetition_spinbox, 12, 0)

        self.save_button = QPushButton("Enregistrer", self)
        self.save_button.setObjectName("enregistrer_pushbutton")
        self.save_button.clicked.connect(self.save_rules)

        layout.addWidget(self.save_button)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def check_syllabesmax(self):
        """check_syllabesmax() : Vérifie que le nombre maximum de syllabes est supérieur au nombre minimum"""
        self.syllabes_spinbox_max.setMinimum(self.syllabes_spinbox_min.value())
        if self.syllabes_spinbox_max.value() < self.syllabes_spinbox_min.value():
            self.syllabes_spinbox_max.setValue(self.syllabes_spinbox_min.value())

    def check_timerulemax(self):
        """check_timerulemax() : Vérifie que le temps maximum est supérieur au temps minimum"""
        self.timerulemax_spinbox.setMinimum(self.timerulemin_spinbox.value() + 2)
        if self.timerulemax_spinbox.value() < self.timerulemin_spinbox.value() + 2:
            self.timerulemax_spinbox.setValue(self.timerulemin_spinbox.value() + 2)

    def save_rules(self):
        """send_rules() : Sauvegarde les règles du jeu dans la liste rules"""
        if self.timerulemax_spinbox.value() < self.timerulemin_spinbox.value() + 2:
            self.timerulemax_spinbox.setValue(self.timerulemin_spinbox.value() + 2)
        rules.clear()
        rules.extend([self.timerulemin_spinbox.value(), self.timerulemax_spinbox.value(), self.lifes_spinbox.value(), self.syllabes_spinbox_min.value(), self.syllabes_spinbox_max.value(), self.repetition_spinbox.value()])
        print(rules)
        self.close()

class GameCreationWindow(QMainWindow):
    """Fenêtre de création de partie"""
    create_game_signal = pyqtSignal(str, str, bool)

    def __init__(self, layout):
        """__init__() : Initialisation de la fenêtre de création de partie"""
        super().__init__()
        self.layout = layout
        self.setWindowModality(Qt.ApplicationModal)

    def setup(self):
        """setup() : Mise en place de la fenêtre de création de partie"""
        global username
        self.setWindowTitle("Créer une partie")
        self.resize(int(screen_width // 2.5), int(screen_height // 2.2))
        center(self)
        self.setStyleSheet(stylesheet)
        layout = QGridLayout()

        self.game_name_label = QLabel("Nom de la partie :", self)
        self.game_name_label.setObjectName("game_name_label")
        # self.game_name_label.setFixedSize(400, 50)

        default_game_name = f"Partie de {username}"
        self.game_name_lineedit = QLineEdit(self)
        self.game_name_lineedit.setObjectName("game_name_lineedit")
        self.game_name_lineedit.setPlaceholderText(default_game_name)
        self.game_name_lineedit.setMaxLength(20)
        self.game_name_lineedit.setText(default_game_name)
        self.game_name_lineedit.returnPressed.connect(lambda: self.create_game(default_game_name, self.password_lineedit.text(), self.private_button.text()))

        self.private_button = QPushButton("🌐", self)
        self.private_button.setObjectName("private_button_icon")
        self.private_button.setFixedSize(40, 40)
        self.private_button.clicked.connect(self.private_game)

        self.password_label = QLabel("Mot de passe :", self)
        self.password_label.setObjectName("password_label")
        # self.password_label.setFixedSize(400, 50)

        characters = string.ascii_letters + string.digits
        random_password = "".join(random.choice(characters) for i in range(12))
        self.password_lineedit = QLineEdit(self)
        self.password_lineedit.setObjectName("password_lineedit")
        self.password_lineedit.setPlaceholderText("Définir un mot de passe")
        self.password_lineedit.setText(random_password)
        self.password_lineedit.setEchoMode(QLineEdit.Password)
        self.password_lineedit.setEnabled(False)
        self.password_lineedit.setMaxLength(20)
        self.password_lineedit.returnPressed.connect(lambda: self.create_game(default_game_name, random_password, self.password_lineedit.text()))
        self.password_lineedit.textChanged.connect(lambda: self.restricted_caracters(self.password_lineedit))

        self.show_password_button = QPushButton("🔑", self)
        self.show_password_button.setObjectName("show_password_pushbutton")
        self.show_password_button.setFixedSize(40, 40)
        self.show_password_button.clicked.connect(self.show_password)
        self.show_password_button.setEnabled(False)

        self.create_game_button2 = QPushButton("Créer la partie", self)
        self.create_game_button2.setObjectName("create_game_button2")
        self.create_game_button2.clicked.connect(lambda: self.create_game(default_game_name, random_password, self.password_lineedit.text()))

        layout.addWidget(self.game_name_label, 0, 0)
        layout.addWidget(self.game_name_lineedit, 1, 0)
        layout.addWidget(self.private_button, 1, 1)
        layout.addWidget(self.password_label, 2, 0)
        layout.addWidget(self.password_lineedit, 3, 0)
        layout.addWidget(self.show_password_button, 3, 1)
        layout.addWidget(self.create_game_button2, 4, 0, Qt.AlignHCenter)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def restricted_caracters(self, lineedit : QLineEdit):
        """restricted_caracters(lineedit) : Restreint les caractères spéciaux
        
        Args:
            lineedit (QLineEdit): LineEdit"""
        text = lineedit.text()
        lineedit.setText(re.sub(r'[^a-zA-ZÀ-ÿ\s0-9]', '', text))

    def show_password(self):
        """show_password() : Affiche le mot de passe"""
        if self.password_lineedit.echoMode() == QLineEdit.Password:
            self.password_lineedit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_lineedit.setEchoMode(QLineEdit.Password)

    def private_game(self):
        """private_game() : Rend la partie privée"""
        if self.private_button.text() == "🌐":
            self.private_button.setText("🔒")
            self.password_lineedit.setEnabled(True)
            self.show_password_button.setEnabled(True)
        else:
            self.private_button.setText("🌐")
            self.password_lineedit.setEnabled(False)
            self.show_password_button.setEnabled(False)
            self.password_lineedit.setEchoMode(QLineEdit.Password)

    def create_game(self, dafault_game_name, random_password, manual_password):
        """create_game() : Crée une partie
        
        Args:
            dafault_game_name (str): Nom de la partie par défaut
            random_password (str): Mot de passe par défaut
            manual_password (str): Mot de passe manuel"""
        if self.password_lineedit.text() == random_password or self.password_lineedit.text() == "" or self.password_lineedit.text().isspace():
            password = random_password
        else:
            password = manual_password

        if self.game_name_lineedit.text() == dafault_game_name or self.game_name_lineedit.text() == "" or self.game_name_lineedit.text().isspace():
            game_name = dafault_game_name
        else:
            game_name = self.game_name_lineedit.text()

        if self.private_button.text() == "🌐":
            private_game = False
        else:
            private_game = True

        self.create_game_signal.emit(game_name, password, private_game)
        self.close()

class JoinGameWindow(QMainWindow):
    """Fenêtre de création de partie"""
    def __init__(self, game_name, private_game):
        """__init__() : Initialisation de la fenêtre de création de partie"""
        super().__init__()
        self.game_name = game_name
        self.private_game = private_game

        self.setWindowModality(Qt.ApplicationModal)

        window.in_game_signal.connect(self.in_game)
        
    def setup(self):
        """setup() : Mise en place de la fenêtre de création de partie"""
        self.setWindowTitle("Rejoindre une partie")
        self.resize(200, 200)
        center(self)
        self.setStyleSheet(stylesheet)
        layout = QGridLayout()

        self.game_name_label = QLabel(f"<b>{self.game_name}<b>", self)
        self.game_name_label.setObjectName("game_name_label")
        self.game_name_label.setFixedSize(400, 50)

        self.password_label = QLabel("Mot de passe :", self)
        self.password_label.setObjectName("password_label")
        self.password_label.setFixedSize(400, 50)

        self.password_widget = QWidget()
        self.password_widget.setFixedHeight(100)
        self.password_layout = QHBoxLayout()

        self.password_lineedit = QLineEdit(self)
        self.password_lineedit.setObjectName("password_lineedit")
        self.password_lineedit.setPlaceholderText("Mot de passe")
        self.password_lineedit.setEchoMode(QLineEdit.Password)
        self.password_lineedit.setMaxLength(30)
        self.password_lineedit.returnPressed.connect(self.join_game)
        self.password_lineedit.textChanged.connect(lambda: self.restricted_caracters(self.password_lineedit))

        self.show_password_button = QPushButton("🔑", self)
        self.show_password_button.setObjectName("show_password_pushbutton")
        self.show_password_button.setFixedWidth(40)
        self.show_password_button.clicked.connect(self.show_password)

        self.join_game_button = QPushButton("Rejoindre la partie", self)
        self.join_game_button.setObjectName("join_game_button")
        self.join_game_button.clicked.connect(self.join_game)

        self.alert_label = QLabel("", self)
        self.alert_label.setFixedSize(400, 50)
        self.alert_label.setStyleSheet("color: red;")

        self.game_name_label.setAlignment(Qt.AlignHCenter)  # Center the text horizontally
        self.alert_label.setAlignment(Qt.AlignHCenter)

        layout.addWidget(self.game_name_label, 0, 0, Qt.AlignHCenter)
        layout.addWidget(self.password_label, 1, 0) 
        layout.addWidget(self.password_widget, 2, 0)
        layout.addWidget(self.alert_label, 3, 0, Qt.AlignHCenter)
        layout.addWidget(self.join_game_button, 4, 0, Qt.AlignHCenter)

        self.password_widget.setLayout(self.password_layout)
        self.password_layout.addWidget(self.password_lineedit)
        self.password_layout.addWidget(self.show_password_button)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        window.correct_mdp.connect(self.incorrect_mdp)

    def join_lobby(self):
        """join_lobby() : Rejoint le lobby (public)"""
        global username
        client_socket.send(f"JOIN_GAME|{self.game_name}|password|{username}".encode())

    def join_game(self):
        """join_game(game_name) : Rejoint une partie privée"""
        global username
        if self.password_lineedit.text() != "" and not self.password_lineedit.text().isspace():
            client_socket.send(f"JOIN_GAME|{self.game_name}|{self.password_lineedit.text()}|{username}".encode())

    def show_password(self):
        """show_password() : Affiche le mot de passe"""
        if self.password_lineedit.echoMode() == QLineEdit.Password:
            self.password_lineedit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_lineedit.setEchoMode(QLineEdit.Password)

    def incorrect_mdp(self, mdp : bool):
        """incorrect_mdp() : Affiche un message d'erreur
        
        Args:
            mdp (bool): Mot de passe incorrect ou non"""
        if mdp:
            self.alert_label.setText("")
            self.close()
        else:
            self.alert_label.setText("Mot de passe incorrect")

    def in_game(self, game_name, players_number):
        """in_game() : Affiche un message d'erreur"""
        self.waiting_room = WaitingRoom(game_name, players_number)
        self.waiting_room.show()
        self.waiting_room.setup()
        self.close()

    def restricted_caracters(self, lineedit : QLineEdit):
        """restricted_caracters(lineedit) : Restreint les caractères spéciaux
        
        Args:
            lineedit (QLineEdit): LineEdit"""
        text = lineedit.text()
        lineedit.setText(re.sub(r'[^a-zA-ZÀ-ÿ\s0-9]', '', text))

class WaitingRoom(QMainWindow):
    """Fenêtre d'attente"""
    def __init__(self, game_name, players_number):
        """__init__() : Initialisation de la fenêtre d'attente"""
        super().__init__()
        self.game_name = game_name
        self.players_number = players_number

        # self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(f"Waiting Room")
        self.resize(300, 300)
        center(self)
        self.setStyleSheet(stylesheet)

        window.waiting_room_close_signal.connect(lambda: self.close())
        window.players_number_signal.connect(self.manage_players_number)

    def setup(self):
        """setup() : Mise en place de la fenêtre d'attente"""
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignHCenter)
        self.game_name_label = QLabel(f"<b>{self.game_name}<b>", self)
        self.game_name_label.setObjectName("game_name_label")
        self.game_name_label.setAlignment(Qt.AlignHCenter)

        self.waiting_label = QLabel("👥", self)
        self.waiting_label.setObjectName("waiting_label")
        self.waiting_label.setAlignment(Qt.AlignHCenter)
        self.waiting_label.setStyleSheet("font-size: 80px;")

        self.number_of_players_label = QLabel(f"{self.players_number}/8", self)
        self.number_of_players_label.setObjectName("number_of_players_label")
        self.number_of_players_label.setAlignment(Qt.AlignHCenter)

        # eventthread = threading.Thread(target=self.__event)
        # eventthread.start()
        self.tetris = Tetris()
        self.tetris.setFixedSize(180, 380)
        
        layout.addWidget(self.game_name_label, 0, 1)
        layout.addWidget(self.waiting_label, 1, 1)
        layout.addWidget(self.number_of_players_label, 2, 1)
        layout.addWidget(self.tetris, 3, 1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def manage_players_number(self, players_number : str):
        """manage_players_number() : Gère le nombre de joueurs dans la partie"""
        self.players_number = players_number
        self.number_of_players_label.setText(players_number)

    def closeEvent(self, event):
        """closeEvent(event) : Fonction appelée lors de la fermeture de la fenêtre
        
        Args:
            event (QCloseEvent): Événement de fermeture"""
        client_socket.send(f"LEAVE_WAITING_ROOM|{self.game_name}|{username}".encode())
        event.accept()
    
    def __event(self):
        while True:
            if Board.Game_is_over:
                self.tetris.close()

if __name__ == "__main__":
    """__main__() : Lance l'application"""
    receiver_thread = ReceptionThread()
    window = ClientWindow()
    login = Login()
    login.show()
    sys.exit(app.exec_())
