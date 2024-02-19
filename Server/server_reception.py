from server_utils import *
from server_game import Game
import random, time, threading, unidecode


class Reception(threading.Thread):
    """Reception() : Classe qui permet de gérer la réception des messages du client
    
    Args:
        threading (Thread): Classe qui permet de créer des Threads"""

    def __init__(self, conn):
        """__init__() : Fonction qui permet d'initialiser la classe Reception
        
        Args:
            conn (socket): Socket de connexion du client"""
        threading.Thread.__init__(self)
        self.conn = conn
        self.words_list = []
        self.players = {"Player": [], "Ready": [], "Lifes": [], "Game": []}


    def run(self):
        """run() : Fonction qui permet de lancer la Thread reception"""
        self.reception(self.conn)

    def reception(self, conn):
        """reception() : Fonction qui permet de recevoir les messages du client
        
        Args:
            conn (socket): Socket de connexion du client
            conn_list (list): Liste des sockets de connexion des clients"""
        global arret
        flag = False

        while not flag and not arret:
            msg = conn.recv(1024).decode()
            print(msg)

            try:
                message = msg.split("|")
            except:
                message = msg

            if msg == "arret" or message == "bye":
                print("Arret du serveur")
                flag = True
                if message == "arret":
                    arret = True

            elif not msg:
                self.deco(conn)
                flag = True

            elif message[0] == "CREATE_GAME":
                self.create_game(conn, message)

            elif message[0] == "NEW_PLAYER":
                self.new_player(conn, message)

            elif message[0] == "NEW_WORD":
                self.new_word(conn, message)

            elif message[0] == "READY_TO_PLAY":
                self.ready_to_play(conn, message)

            elif message[0] == "START_GAME":
                self.start_game(conn, message)

            elif message[0] == "NEW_USER":
                self.new_user(conn, message)

            elif message[0] == "NEW_SYLLABE":
                self.new_syllabe(conn, message, msg)

            elif message[0] == "GET_GAMES":
                self.get_games(username = message[1])

            elif message[0] == "DELETE_GAME":
                self.delete_game(conn, message)

        print("Arret de la Thread reception")

    def new_syllabe(self, conn, message, msg):
        """new_syllabe() : Fonction qui permet de créer une nouvelle syllabe
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client
            msg (str): Message du client"""
        print(f'User : {msg} {message}\n')
        word = self.convert_word(message[2])
        sylb = self.convert_word(message[3])
        print("CONVERTED", sylb)
        print(game_tour)
        index_player = game_tour["Player"].index(message[1])
        connexion = game_tour["Conn"][index_player]

        if self.check_syllabe(word, sylb):
            print("if")
            if any(self.convert_word(word.lower()) == self.convert_word(mot.lower()) for mot in dictionnaire):
                self.right(connexion, player=message[1])
                self.words_list.append(word.lower())
            else:
                self.wrong(connexion, player=message[1])
        else:
            self.wrong(connexion, player=message[1])
    
    def convert_word(self, word):
        """convert_word() : Permet d'ignorer les caractères spéciaux, les accents et les majuscules du dictionnaire
        
        Args:
            word (str): Mot à convertir
        
        Returns:
            str: Mot converti"""
        word = unidecode.unidecode(word)  # Convertir les caractères spéciaux en caractères ASCII
        word = word.lower()  # Convertir les majuscules en minuscules
        
        return word

    def new_user(self, conn, message):
        """new_user() : Fonction qui permet d'ajouter un nouveau joueur
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        if self.check_user_unique(message[1]):
            game_tour["Player"].append(message[1])
            game_tour["Conn"].append(conn)
            game_tour["Syllabe"].append("")
            game_tour["Game"].append("")
            conn.send("NAME_CORRECT".encode())
        else:
            conn.send("NAME_ALREADY_USED".encode())
    
    def get_games(self, username):
        """get_games() : Fonction qui permet de récupérer la liste des parties"""
        player_index = game_tour["Player"].index(username)
        conn = game_tour["Conn"][player_index]
        for game in game_list:
            conn.send(f"GAME_CREATED|{game}".encode())
            time.sleep(0.1)

    def delete_game(self, conn, message):
        """delete_game() : Fonction qui permet de supprimer une partie
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Suppression d'une partie")
        game_list.remove(message[1])
        for connexion in conn_list:
            connexion.send(f"GAME_DELETED|{message[1]}".encode())

    def start_game(self, conn, message):
        """start_game() : Fonction qui permet de lancer une partie
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Lancement de la partie")
        rules = [int(message[2]), int(message[3]), int(message[4]), int(message[5]), int(message[6]), int(message[7])]
        print("Règles", rules)
        self.game = Game(conn, self.players, creator=message[1], game = True, rules = rules)
        self.game.start()

    def ready_to_play(self, conn, message):
        """ready_to_play() : Fonction qui permet de savoir si le joueur est prêt
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Le joueur est prêt")
        index_player = self.players["Player"].index(message[1])

        if self.players["Ready"][index_player]:
            self.players["Ready"][index_player] = False
        else:
            self.players["Ready"][index_player] = True
        print(self.players["Ready"][index_player])

    def new_word(self, conn, message):
        """new_word() : Fonction qui permet d'ajouter un nouveau mot
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Nouveau mot")
        self.words_list.append(message[1])

    def new_player(self, conn, message):
        """new_player() : Fonction qui permet d'ajouter un nouveau joueur
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Ajout d'un nouveau joueur")
        self.players["Player"].append(message[1])
        self.players["Game"].append(message[2])
        self.players["Ready"].append(False)
        self.players["Lifes"].append(0)

    def create_game(self, conn, message):
        """create_game() : Fonction qui permet de créer une partie

        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Création d'une partie")
        game_list.append(f"{message[1]}")
        self.players["Player"].append(message[1])
        self.players["Ready"].append(False)
        self.players["Game"].append(f"{message[1]}")
        self.players["Lifes"].append(0)

        for connexion in conn_list:
            connexion.send(f"GAME_CREATED|{message[1]}".encode())
        
    def deco(self, conn):
        """deco() : Fonction qui permet de déconnecter un client
        
        Args:
            conn (socket): Socket de connexion du client"""
        print("Un client vient de se déconnecter...")
        index_player = game_tour["Conn"].index(conn)

        game_tour["Conn"].remove(conn)
        game_tour["Player"].pop(index_player)

        try:
            game_tour["Syllabe"].pop(index_player)
            game_tour["Game"].pop(index_player)
        except ValueError and IndexError:
            pass

        conn_list.remove(conn)
        conn.close()

    def check_user_unique(self, user):
        """check_user_unique() : Fonction qui vérifie si le pseudo du joueur est unique
        
        Args:
            user (str): Pseudo du joueur"""
        for player in game_tour["Player"]:
            if player == user:
                print("Pseudo déjà utilisé")
                return False
        return True


    def wrong(self, conn, player):
        """wrong() : Fonction qui génère un mot aléatoire
        
        Args:
            conn (socket): Socket de connexion du client
            player (str): Pseudo du joueur"""
        conn.send("GAME|WRONG|".encode())
        print()


    def right(self, conn, player):
        """right() : Fonction qui génère un mot aléatoire
        
        Args:
            conn (socket): Socket de connexion du client
            player (str): Pseudo du joueur"""
        conn.send("GAME|RIGHT|".encode())
        player_index = self.players["Player"].index(player)
        game = self.players["Game"][player_index]
        self.game.stop_compteur(game)

    def check_syllabe(self, mot, sylb):
        """check_syllabe() : Fonction qui vérifie si le mot passé en paramètre contient une syllabe
        
        Args:
            mot (str): Mot à vérifier
            sylb (str): Syllabe à vérifier

        Returns:
            bool: True si le mot contient la syllabe, False sinon"""
        if sylb in mot:
            return True
        else:
            return False

        
            
