from server_utils import *
from server_game import Game
import random, time, threading, unidecode
from socket import socket as socket


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
        self.list_lock = threading.Lock()


    def run(self):
        """run() : Fonction qui permet de lancer la Thread reception"""
        self.reception(self.conn)

    def reception(self, conn):
        """reception() : Fonction qui permet de recevoir les messages du client
        
        Args:
            conn (socket): Socket de connexion du client"""
        global arret
        flag = False

        while not flag and not arret:
            try:
                msg = conn.recv(1024).decode()
                print(msg)
                print(self.players, "FOR THE PLAYER")
            except ConnectionResetError:
                self.deco(conn)
                flag = True
                break
            except ConnectionAbortedError:
                self.deco(conn)
                flag = True
                break
            except OSError:
                self.deco(conn)
                flag = True
                break

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

            elif message[0] == "NEW_WORD":
                self.new_word(conn, message)

            elif message[0] == "READY_TO_PLAY":
                self.ready_to_play(conn, message)
            
            elif message[0] == "READY_TO_PLAY_JOIN":
                self.ready_to_play_join(conn, message)

            elif message[0] == "START_GAME":
                self.start_game(conn, message)

            elif message[0] == "NEW_USER": #Nouvel utilisateur se connecte
                self.new_user(conn, message)

            elif message[0] == "NEW_SYLLABE":
                self.new_syllabe(conn, message, msg)

            elif message[0] == "GET_GAMES":
                self.get_games(username = message[1])

            elif message[0] == "LEAVE_GAME":
                self.leave_game(game_name=message[1], player=message[2])
            
            elif message[0] == "JOIN_GAME":
                self.join_game(conn, message)

            elif message[0] == "JOIN_GAME_AS_A_PLAYER":
                self.join_game_as_a_player(conn, username = message[1], game_name = message[2])

        print("Arret de la Thread reception")

    def join_game(self, conn, message):
        """join_game() : Fonction qui permet de vérifier si le joueur peut accéder à la partie via le mdp, et si oui, le connecte à alle en envoyant un message
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Rejoindre une partie")

        password = message[2]
        username = message[3]
        game_index = game_list["Name"].index(message[1])
        game_name = game_list["Name"][game_index]
        game_creator = game_list["Creator"][game_index]
        game_password = game_list["Password"][game_index]
        game_private = game_list["Private"][game_index]
        #print(game_name, game_creator, game_password, game_private, password, username)
        print("MOT DE PASSE", game_password, password)
        if game_private == "True":
            if password == game_password:
                for connexion in game_tour["Conn"]:
                    conn_index = game_tour["Conn"].index(connexion)
                    #print(game_tour["Game"][conn_index], game_creator, game_name, username)
                    if game_tour["Game"][conn_index] == game_name:
                        connexion.send(f"JOIN|GAME_JOINED|{game_name}|{game_creator}|{game_password}|{game_private}|{username}".encode())
                conn.send(f"JOIN|GAME_JOINED|{game_name}|{game_creator}|{game_password}|{game_private}|{username}".encode())
            else:
                conn.send("JOIN|WRONG_PASSWORD".encode())
        else:
            for connexion in game_tour["Conn"]:
                conn_index = game_tour["Conn"].index(connexion)
                #print(game_tour["Game"][conn_index], game_creator, game_name, username)
                if game_tour["Game"][conn_index] == game_name:
                    connexion.send(f"JOIN|GAME_JOINED|{game_name}|{game_creator}|{game_password}|{game_private}|{username}".encode())
            conn.send(f"JOIN|GAME_JOINED|{game_name}|{game_creator}|{game_password}|{game_private}|{username}".encode())

    def get_game_players(self, game_name : str) -> list:
        """get_game_players() : Fonction qui permet de récupérer les joueurs d'une partie
        
        Args:
            game_name (str): Nom de la partie"""
        game_players = []
        for player in game_tour["Player"]:
            player_index = game_tour["Player"].index(player)
            if game_tour["Game"][player_index] == game_name:
                game_players.append(player)
        print(game_players, "GAME PLAYERS")
        return game_players

    def join_game_as_a_player(self, conn, username, game_name):
        """join_game_as_a_player() : Fonction qui permet d'associer le joueur à la bonne partie dans la liste globale game_tour
        
        Args:
            username (str): Pseudo du joueur
            game_name (str): Nom de la partie"""
        player_index = game_tour["Player"].index(username)
        game_tour["Game"][player_index] = game_name
        game_players_list = self.get_game_players(game_name)
        game_players = ','.join(game_players_list)
        for connexion in game_tour["Conn"]:
            conn_index = game_tour["Conn"].index(connexion)
            if game_tour["Game"][conn_index] == game_name:
                connexion.send(f"JOIN|GET_PLAYERS|{game_players}".encode())

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
    
    def convert_word(self, word) -> str:
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
            game_tour["Ready"].append(False)
            game_tour["InGame"].append(False)
            game_tour["Game"].append(None)
            self.username = message[1]
            conn.send("NAME_CORRECT".encode())
        else:
            conn.send("NAME_ALREADY_USED".encode())
    
    def get_games(self, username):
        """get_games() : Fonction qui permet de récupérer la liste des parties
        
        Args:
            username (str): Pseudo du joueur"""
        player_index = game_tour["Player"].index(username)
        conn = game_tour["Conn"][player_index]
        for i in range(len(game_list["Name"])):
            game_name = game_list["Name"][i]
            private = game_list["Private"][i]
            conn.send(f"GAME_CREATED|{game_name}|{private}".encode())
            time.sleep(0.1)
    
    def leave_game(self, game_name, player) -> None:
        """leave_game() : Fonction qui permet de quitter une partie

        Args:
            conn (socket): Socket de connexion du client
            game_name (str): Nom de la partie
            player (str): Pseudo du joueur"""
        players_list = []
        number_of_players = 0

        game_index = game_tour["Player"].index(player)
        game_tour["Game"][game_index] = None
        game_tour["InGame"][game_index] = False
        game_tour["Ready"][game_index] = False

        print("Quitter une partie", game_tour)
        self.send_player_leaving(game_name, player)
    
        for game in game_tour["Game"]:
            if game == game_name:
                number_of_players += 1
                players_list.append(game_tour["Player"][game_tour["Game"].index(game)])
        print(players_list, number_of_players, "PLAYERS LIST")
        self.players = {"Player": [], "Ready": [], "Lifes": [], "Game": []}

        if number_of_players == 0:
            self.delete_game(game_name)
        else:
            creator = game_list["Creator"][game_list["Name"].index(game_name)]
            if player == creator:
                for player in players_list:
                    if player != creator:
                        self.new_creator(game_name, player)
                        return

    def send_player_leaving(self, game_name : str, player : str):
        """send_player_leaving() : Fonction qui permet d'envoyer un message à tous les joueurs pour les informer qu'un joueur a quitté la partie
        
        Args:
            game_name (str): Nom de la partie"""
        for connexion in game_tour["Conn"]:
            if game_tour["Game"][game_tour["Conn"].index(connexion)] == game_name:
                connexion.send(f"LOBBY_STATE|LEAVE_GAME|{game_name}|{player}".encode())
                
    def new_creator(self, game_name, player):
        """new_creator() : Fonction qui permet de changer le créateur de la partie
        
        Args:
            game_name (str): Nom de la partie
            player (str): Pseudo du joueur"""
        game_index = game_list["Name"].index(game_name)
        game_list["Creator"][game_index] = player
        print("Nouveau créateur", game_list["Creator"][game_index], game_list["Name"][game_index], player)
        conn = self.get_conn(player)
        conn_index = reception_list["Conn"].index(conn)
        reception = reception_list["Reception"][conn_index]
        reception.reset_players(join = False, creator = player, game_name = game_name)
        conn.send(f"LOBBY_STATE|NEW_CREATOR|{game_name}|{player}".encode())

    
    def get_conn(self, player : str) -> socket:
        """get_conn() : Fonction qui permet de récupérer le socket de connexion du joueur
        
        Args:
            player (str): Pseudo du joueur
        
        Returns:
            socket: Socket de connexion du joueur"""
        index_player = game_tour["Player"].index(player)
        return game_tour["Conn"][index_player]


    def delete_game(self, game_name : str):
        """delete_game() : Fonction qui permet de supprimer une partie
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        game_index = game_list["Name"].index(game_name)
        game_list["Name"].pop(game_index)
        game_list["Creator"].pop(game_index)
        game_list["Password"].pop(game_index)
        game_list["Private"].pop(game_index)
        game_list["Game_Object"].pop(game_index)

        for connexion in conn_list:
            connexion.send(f"GAME_DELETED|{game_name}".encode())
        print("Suppression d'une partie", game_list)


    def start_game(self, conn, message):
        """start_game() : Fonction qui permet de lancer une partie
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Lancement de la partie")
        self.new_players(game_name=message[2], creator=message[1])
        rules = [int(message[3]), int(message[4]), int(message[5]), int(message[6]), int(message[7]), int(message[8])]
        #print("Règles", rules)
        self.game = Game(conn, self.players, creator=message[1], game = True, rules = rules, game_name=message[2])
        game_list_index = game_list["Name"].index(message[2])
        with self.list_lock:
            game_list["Game_Object"][game_list_index] = self.game #on ajoute l'insatance de la classe pour pouvoir l'utiliser depuis d'autres threads de réception
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
        #print(self.players["Ready"][index_player])
        index_player = game_tour["Player"].index(message[1])
        game_tour["Ready"][index_player] = None
        
    def ready_to_play_join(self, conn, message):
        """ready_to_play_join() : Fonction qui permet de savoir si le joueur est prêt
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        index_player = game_tour["Player"].index(message[1])
        if game_tour["Ready"][index_player]:
            game_tour["Ready"][index_player] = False
        else:
            game_tour["Ready"][index_player] = True
        #print(game_tour["Ready"][index_player])

    def new_word(self, conn, message):
        """new_word() : Fonction qui permet d'ajouter un nouveau mot
        
        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        print("Nouveau mot")
        self.words_list.append(message[1])

    def new_players(self, game_name, creator):
        """new_player() : Fonction qui permet d'ajouter un nouveau joueur
        
        Args:
            game_name (str): Nom de la partie
            creator (str): Créateur de la partie"""
        for player in game_tour["Player"]:
            player_index = game_tour["Player"].index(player)
            if game_tour["Game"][player_index] == game_name and player != creator:
                self.players["Player"].append(player)
                self.players["Game"].append(game_name)
                self.players["Lifes"].append(0)
                if game_tour["Ready"][player_index]:
                    self.players["Ready"].append(True)
                else:
                    self.players["Ready"].append(False)

        #print(self.players, "PLAYERS", game_tour, game_name)

    def reset_players(self, join, creator, game_name):
        """reset_players() : Fonction qui permet de réinitialiser les joueurs
        
        Args:
            join (bool): Si le joueur rejoint une partie
            creator (str): Créateur de la partie
            game_name (str): Nom de la partie"""
        print("RESET PLAYERS", join, creator, game_name)
        print(self.username)
        self.players = {"Player": [], "Ready": [], "Lifes": [], "Game": []}
        if not join:
            print("RESET PLAYERS")
            self.players["Player"].append(creator)
            self.players["Ready"].append(False)
            self.players["Game"].append(f"{game_name}")
            self.players["Lifes"].append(0)
        print(self.players, "RESET PLAYERS")


    def create_game(self, conn, message):
        """create_game() : Fonction qui permet de créer une partie

        Args:
            conn (socket): Socket de connexion du client
            message (list): Message du client"""
        #message = f"CREATE_GAME|{username}|{game_name}|{password}|{private_game}"
        print(message, "MESSAGE")
        print("Création d'une partie")
        game_list["Creator"].append(message[1])
        game_list["Name"].append(message[2])
        game_list["Password"].append(message[3])
        game_list["Private"].append(message[4])
        game_list["Game_Object"].append(None)
        print(game_list, "GAME LIST")
        self.players["Player"].append(message[1])
        self.players["Ready"].append(False)
        self.players["Game"].append(f"{message[2]}")
        self.players["Lifes"].append(0)
        
        player_index = game_tour["Player"].index(message[1])
        game_tour["Game"][player_index] = message[2] #ici on ajoute le nom de la partie au createur de la partie

        for connexion in conn_list:
            connexion.send(f"GAME_CREATED|{message[2]}|{message[4]}".encode())
        
    def deco(self, conn):
        """deco() : Fonction qui permet de déconnecter un client
        
        Args:
            conn (socket): Socket de connexion du client"""
        print("Un client vient de se déconnecter...")
        index_player = game_tour["Conn"].index(conn)

        game_tour["Conn"].remove(conn)
        game_tour["Player"].pop(index_player)

        try:
            game_tour["InGame"].pop(index_player)
            game_tour["Game"].pop(index_player)
        except ValueError and IndexError:
            pass

        conn_list.remove(conn)
        conn.close()

    def check_user_unique(self, user) -> bool:
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
        conn.send(f"GAME|RIGHT|{player}".encode())
        try:
            player_index = self.players["Player"].index(player)
            game = self.players["Game"][player_index]
        except ValueError:
            print("Player not in the list")
            player_index = game_tour["Player"].index(player)
            game_name = game_tour["Game"][player_index]
            self.new_players(game_name=game_name, creator=None)
            self.game = game_list["Game_Object"][game_list["Name"].index(game_name)]
            game = game_name
        self.game.stop_compteur(game)

    def check_syllabe(self, mot, sylb) -> bool:
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

        
            
