# ===== Module Description:

"""
# trivia_server

This module implements the TCP server (with multiple players) of the trivia game.

Examples
-------
You can run this server using the following command::

    $ python TriviaServer.py


Another section...

"""
# ====================

# ===== Imports:

# For Python versions between 3.7 to 3.9, we need the following line:
from __future__ import annotations
import json
import socket
import select
import random
from typing import Union
import chatlib
from chatlib import ProtocolUser, User, Question,\
    PROTOCOL_CLIENT, PROTOCOL_SERVER_OK, PROTOCOL_SERVER_ERROR


# ====================

# ===== Constants:


LISTEN_ALL_IP = "0.0.0.0"
SERVER_IP = LISTEN_ALL_IP

USERS_PATH = "users.json"
QUESTIONS_PATH = "questions.json"

HIGHSCORE_TABLE_SIZE = 3
CORRECT_ANSWER_SCORE = 5

UNKNOWN_ERROR_OCCURRED = "ERROR: An unknown error occured."
ERROR_USERNAME_DOES_NOT_EXIST = "Error: Username does not exist!"
ERROR_PASSWORD_DOES_NOT_MATCH = "Error: Password does not match!"
ERROR_INVALID_ANSWER = "Error: Invalid answer! Must be a number between 1-4."
ERROR_CLIENT_WAS_ADDED_WRONG = "Error: This client was not added by `accept_new_client`!"

# ====================
# ===== Classes:


class Server(ProtocolUser):
    """
    A class represents the server for trivia-player, derived from `chatlib.ProtocolUser` class.

    -------

    Attributes
    -------
    socket : socket.socket
        The socket of the client/user.

    users

    questions

    logged_users

    -------

    Protected Methods
    -------
    _split_data(data, expected_fields)

    _join_data(words)

    _build_message(cmd, msg)

    _parse_message(msg)

    Public Methods
    -------
    recv_message_and_parse()

    _build_and_append_message(cmd, data='')

    terminate()
        Closes the server socket (for use when the socket is no longer needed).

    """

    def __init__(self, server_ip: str = SERVER_IP, server_port: int = chatlib.SERVER_PORT) -> None:
        """
        Creates a `Server` by creating a socket, binding it and putting on a listening mode.

        ----------

        Parameters
        ----------
        server_ip : str, (default SERVER_IP)
            The server IP. The default is for a 'listen to all' server.
        server_port : int, (default SERVER_PORT)
            The server port.
        ----------

        Raises
        ------
        - TypeError
            - In case one of the parameters is of inappropriate type.
        """
        super().__init__()
        self.users = self._load_users()
        self.questions = self._load_questions()
        self.logged_users = {}
        self.messages_to_send = []
        self.clients = []

        # Bind the socket to the IP and port of the socket:
        self.socket.bind((server_ip, server_port))
        # Allow the socket to listen to clients:
        self.socket.listen()

    @property
    def users(self) -> dict[str, User]:
        """`dict`[`str`,`User`]: A dictionary of all the users - whether connected or not.

        #### Pay attention: The getter for this property returns a shallow copy of this dict.
        """
        return self._users.copy()

    @users.setter
    def users(self, users: list[User]) -> None:
        if not isinstance(users, list) or not all(isinstance(u, User) for u in users):
            raise TypeError
        self._users = {user.name: user for user in users}

    @property
    def questions(self) -> dict[int, Question]:
        """`dict`[`int`,`Question`]: A dictionary of all the questions.

        #### Pay attention: The getter for this property returns a shallow copy of this dict.
        """
        return self._questions.copy()

    @questions.setter
    def questions(self, questions: dict[int, Question]) -> None:
        if not isinstance(questions, dict):
            raise TypeError
        if not all(isinstance(i, int) and isinstance(q, Question) for (i, q) in questions.items()):
            raise TypeError
        self._questions = questions

    @property
    def logged_users(self) -> dict[tuple[str, int], str]:
        """`dict`[`tuple`[`str`,`int`],`str`]: A dictionary of all the logged users.

        #### Pay attention: The getter for this property returns a shallow copy of this dict.
        """
        return self._logged_users.copy()

    @logged_users.setter
    def logged_users(self, logged_users: dict[tuple[str, int], str]) -> None:
        if not isinstance(logged_users, dict):
            raise TypeError
        if not all(isinstance(t, tuple) for t in logged_users):
            raise TypeError
        if not all(isinstance(s, str) and isinstance(i, int) for (s, i) in logged_users.keys()):
            raise TypeError
        if not all(isinstance(s, str) for s in logged_users.values()):
            raise TypeError
        self._logged_users = logged_users

    @property
    def messages_to_send(self) -> list[tuple[socket.socket, str]]:
        """`list`[`tuple`[`socket.socket`,`str`]]: A list of all (client, msg) tuples to be sent.

        We make it a list to keep our server a fair server (in terms of FCFS).

        #### Pay attention: The getter for this property returns a shallow copy of this list.
        """
        return self._messages_to_send.copy()

    @messages_to_send.setter
    def messages_to_send(self, messages_to_send: list[tuple[socket.socket, str]]) -> None:
        if not isinstance(messages_to_send, list):
            raise TypeError
        if not all(isinstance(t, tuple) for t in messages_to_send):
            raise TypeError
        if not all(isinstance(soc, socket.socket) and isinstance(s, str)
                   for (soc, s) in messages_to_send):
            raise TypeError
        self._messages_to_send = messages_to_send

    @property
    def clients(self) -> list[socket.socket]:
        """`list`[`socket.socket`]: A list of all clients which have been accepted by `accept`.

            #### Pay attention: The getter for this property returns a shallow copy of this list.
        """
        return self._clients

    @clients.setter
    def clients(self, clients: list[socket.socket]) -> None:
        if not isinstance(clients, list):
            raise TypeError
        if not all(isinstance(soc, socket.socket) for soc in clients):
            raise TypeError
        self._clients = clients

    @staticmethod
    def _load_users() -> list[User]:
        with open(USERS_PATH, "r") as read_users:
            return [User.dict_to_user(user_dict) for user_dict in json.load(read_users)]

    def store_users(self) -> None:
        with open(USERS_PATH, "w") as write_users:
            users_list = [user.user_to_dict() for user in self._users.values()]
            json.dump(users_list, write_users, indent=2)

    @staticmethod
    def _load_questions() -> dict[int, Question]:
        with open(QUESTIONS_PATH, "r") as read_questions:
            return {int(k):Question.dict_to_question(q) for (k,q) in json.load(read_questions).items()}

    def store_questions(self) -> None:
        with open(QUESTIONS_PATH, "w") as write_questions:
            questions_dict = {num:q.question_to_dict() for (num,q) in self._questions.items()}
            json.dump(questions_dict, write_questions, indent=2)

    @staticmethod
    def recv_message_and_parse(client: socket.socket) -> Union[tuple[str, str], tuple[None, None]]:
        """
        Recieves a new message from the socket and then parses the message using `chatlib`.

        This function alse prints a message with the data recived.

        ------

        Parameters
        ------
        client: socket.socket
            - The socket for reciving the message from. see also `returns` to see what happens
            in case of an illegal socket.

        ------

        Returns
        ------
        - tuple[str, str]
            - If succeded - returns a tuple (cmd, msg). (cmd is the command and msg is the massege).
        - tuple[None, None]
            - If an error occured with the message recived from the client, or if the client socket
            is an illegal socket(e.g. closed forcibly and thus an `OSError` or
            `ConnectionResetError` was raised).
        ------

        Raises
        ------
        - TypeError
            - If the argument is of inappropriate type
        - InterruptedError
            - If `recv` failed (i.e the syscall is interrupted).
        """

        if not isinstance(client, socket.socket):
            raise TypeError
        data = ''
        try:
            data = client.recv(chatlib.BUFFER_SIZE).decode()
        except InterruptedError as error:
            raise error
        except (ConnectionResetError, OSError):
            return (None, None)
        cmd, msg = ProtocolUser._parse_message(data)
        if cmd:
            print("[CLIENT]\t{}\nmsg:\t{}".format(client.getpeername(), data))
        return (cmd, msg)

    def _build_and_append_message(self, client: socket.socket, cmd: str, data: str = '') -> None:
        """
        Builds a new message using `chatlib`, by code and message.
        Then, appends it to the `_messages_to_send` list.

        ------

        Parameters
        ------
        client: socket.socket
            - The socket for sending the message.

        cmd : str
            - A command string, to send to the server.

        data : str, (default '')
            - A data srting, to send to the server.
        ------

        Raises
        ------
        - AssertionError
            - If `cmd` or `data` does not match the protocol.
        """

        assert isinstance(client, socket.socket) and all(
            isinstance(s, str) for s in [cmd, data])
        if cmd == PROTOCOL_SERVER_ERROR:
            cmd_protocol = cmd
        elif cmd in PROTOCOL_SERVER_OK.keys():
            cmd_protocol = PROTOCOL_SERVER_OK[cmd]
        else:
            raise AssertionError
        msg = ProtocolUser._build_message(cmd_protocol, data)
        if not msg:
            raise AssertionError
        self._messages_to_send.append((client, msg))  # was added

    def send_messages_to_ready_sockets(self, ready_to_write: list[socket.socket]) -> None:
        if not isinstance(ready_to_write, list):
            raise TypeError
        if not all(isinstance(soc, socket.socket) for soc in ready_to_write):
            raise TypeError
        # TODO: Make here intersection for achiving O(n) complexity...
        for msg in self._messages_to_send:
            curr_socket, data = msg
            if curr_socket in ready_to_write:
                self._messages_to_send.remove(msg)
                try:
                    curr_socket.send(data.encode())
                    print("[SERVER]\t{}\nmsg:\t{}".format(
                        curr_socket.getpeername(), data))
                except (ConnectionResetError, OSError) as error:
                    self.terminate_client(curr_socket)

    @staticmethod
    def _send_error(client: socket.socket, error_mgs: str = UNKNOWN_ERROR_OCCURRED) -> None:
        """
        Send error message with given message to the client.

        (Uses the method `_build_and_append_message`).

        ------

        Parameters
        ------
        client: socket.socket
            - The socket for sending the error.
            Must be a real and exist socket, otherwise an `OSError` will be raised.

        error_mgs : str, (default `UNKNOWN_ERROR_OCCURRED`)
            - The error messgae to send.
        """

        # TODO: check if `error_mgs` is in the protocol.
        assert isinstance(client, socket.socket) and isinstance(error_mgs, str)
        Server._build_and_append_message(
            client, PROTOCOL_SERVER_ERROR, error_mgs)

    def _handle_login_message(self, client: socket.socket, data: str) -> None:
        """
        Gets socket and message data of login message and checks the username and password if match.

        If not - sends error and finished. If all ok, sends OK message and adds user and address
        to logged_users.

        (Uses the method `_build_and_append_message`).

        ------

        Parameters
        ------
        client: socket.socket
            - The client socket. Must be a real and exist socket, otherwise an `OSError`
            will be raised.

        data : str
            - A string of format "<username>#<password>".
        """
        assert isinstance(client, socket.socket) and isinstance(data, str)
        data_list = self._split_data(data, 2)
        if not data_list:
            self._send_error(client)
            return
        username, password = data_list
        if not username in self.users:
            self._send_error(client, ERROR_USERNAME_DOES_NOT_EXIST)
        elif password != self.users[username].get_password():
            self._send_error(client, ERROR_PASSWORD_DOES_NOT_MATCH)
        else:
            self._build_and_append_message(client, "login")
            assert client.getpeername() not in self._logged_users  # TODO: remove it
            self._logged_users[client.getpeername()] = username
            assert client.getpeername() in self._logged_users  # TODO: remove it

    def _handle_logout_message(self, client: socket.socket) -> None:
        """
        Closes the logging-out socket and removes user from logged_users dictioary.

        This function alse prints a message to the screen.

        ------

        Parameters
        ------
        client: socket.socket
            - The socket to close.
            Must be a real and exist socket, otherwise an `OSError` will be raised.
        """
        assert isinstance(client, socket.socket)
        del self._logged_users[client.getpeername()]
        client.close()
        self._clients.remove(client)
        print("Connection closed!")
        self._print_client_sockets()

    def _handle_get_score_message(self, client: socket.socket) -> None:
        """
        Gets an address of a logged-in client and send the client its own score.

        (Uses the method `_build_and_append_message`).

        ------

        Parameters
        ------
        client: socket.socket
            - A client socket which is already logged-in.
            Must be a real and exist socket, otherwise an `OSError` will be raised.
        """
        assert isinstance(client, socket.socket)
        client_address = client.getpeername()
        assert client_address in self._logged_users
        username = self._logged_users[client_address]
        assert username in self._users
        score = str(self._users[username].get_score())
        self._build_and_append_message(client, "get_score", score)

    def _handle_get_highscore_message(self, client: socket.socket) -> None:
        """
        Gets an address of a logged-in client and send the client the highscore messgae,
        according to the protocol.

        (Uses the method `_build_and_append_message`).

        ------

        Parameters
        ------
        client: socket.socket
            - A client socket which is already logged-in.
        Must be a real and exist socket, otherwise an `OSError` will be raised.
        """
        assert isinstance(client, socket.socket)
        greatest = sorted(self.users.values(), key=lambda user: user._score,
                          reverse=True)[0:HIGHSCORE_TABLE_SIZE]
        highscore = '\n'.join(": ".join((user.name, str(user.score)))
                              for user in greatest)
        self._build_and_append_message(client, "get_highscore", highscore)

    def _handle_get_logged_users_message(self, client: socket.socket) -> None:
        """
        Gets an address of a logged-in client and send the client all the logged-in users,
        according to the protocol.

        (Uses the method `_build_and_append_message`).

        ------

        Parameters
        ------
        client: socket.socket
            - A client socket which is already logged-in.
        Must be a real and exist socket, otherwise an `OSError` will be raised.
        """
        assert isinstance(client, socket.socket)
        logged_msg = ','.join(self._logged_users.values())
        self._build_and_append_message(client, "get_logged_users", logged_msg)

    def _get_random_question(self) -> str:
        """
        An helper method for `get_questio` cmd. Gets a random question from the repository.

        ------

        Returns
        ------
        - str
            - A string of the format:

            "<question_num>#<question>#<answer1>#<answer2>#<answer3>#<answer4>".
        """
        q_num = random.choice(list(self._questions.keys()))
        question = self._questions[q_num]
        q_elements = (str(q_num), question._question) + \
            tuple(question.optional_answers)
        return self._join_data(q_elements)

    def _handle_get_question_message(self, client: socket.socket) -> None:
        """
        Gets an address of a logged-in client, rand a question from the repository and then
        sends it to the client.

        (Uses the method `_build_and_append_message`).

        ------

        Parameters
        ------
        client: socket.socket
            - A client socket which is already logged-in.
        Must be a real and exist socket, otherwise an `OSError` will be raised.
        """
        assert isinstance(client, socket.socket)
        self._build_and_append_message(
            client, "get_question", self._get_random_question())

    def _handle_send_answer_message(self, client: socket.socket, answer_data: str) -> None:
        """
        Gets an address of a logged-in client and its answer messgae. Then, checks the answer
        and sends an appropriate message.

        In the case of a message that does not comply with the protocol, sends an error messgae.

        (Uses the method `_build_and_append_message`).

        ------

        Parameters
        ------
        client: socket.socket
            - A client socket which is already logged-in.
        Must be a real and exist socket, otherwise an `OSError` will be raised.
        """
        assert isinstance(client, socket.socket) and isinstance(
            answer_data, str)
        answer_parts = self._split_data(answer_data, 2)
        if not answer_parts or len(answer_parts) != 2:
            self._send_error(client, ERROR_INVALID_ANSWER)
            return
        try:
            # checks if integers.
            q_num, answer = int(answer_parts[0]), int(answer_parts[1])
            # checks if question number exists.
            question = self._questions[q_num]
            # checks if answer is between 1-4.
            if answer not in [i for i in range(1, chatlib.NUMBER_OF_ANSWERS + 1)]:
                raise ValueError
        except (ValueError, KeyError):
            self._send_error(client, ERROR_INVALID_ANSWER)
            return
        if answer == question._answer:
            self._build_and_append_message(client, "send_answer_correct")
            self._users[self._logged_users[client.getpeername()]].add_score(
                CORRECT_ANSWER_SCORE)
        else:
            self._build_and_append_message(
                client, "send_answer_wrong", str(question._answer))

    def handle_client_message(self, client: socket.socket, cmd: str, data: str) -> None:
        """
        Gets message cmd and data and calls the right function to handle command.
        Then, the message will be appended to the `_messages_to_send` list.

        ------

        Parameters
        ------
        client: socket.socket
            - The socket to terminate (close).

        cmd : str
            - The command code, as described in `chatlib` constants.

        data : str
            - The data as a string, according to the protocol.

        ------

        Raises
        ------
        - TypeError
            - If the argument is of inappropriate type
        """
        if not isinstance(client, socket.socket) or \
                not all(isinstance(s, str) for s in [cmd, data]):
            raise TypeError
        if cmd == PROTOCOL_CLIENT["login"]:
            self._handle_login_message(client, data)
        elif cmd == PROTOCOL_CLIENT["logout"]:
            self._handle_logout_message(client)
        elif cmd == PROTOCOL_CLIENT["get_score"]:
            self._handle_get_score_message(client)
        elif cmd == PROTOCOL_CLIENT["get_highscore"]:
            self._handle_get_highscore_message(client)
        elif cmd == PROTOCOL_CLIENT["get_logged_users"]:
            self._handle_get_logged_users_message(client)
        elif cmd == PROTOCOL_CLIENT["get_question"]:
            self._handle_get_question_message(client)
        elif cmd == PROTOCOL_CLIENT["send_answer"]:
            self._handle_send_answer_message(client, data)
        else:
            self._send_error(client, UNKNOWN_ERROR_OCCURRED)

    def _print_client_sockets(self) -> None:
        """
        A function to print all the connected clients.
        """
        if not self._clients:
            print("Currently no one is connected.")
        else:
            print("Currently connected - {} clients:".format(len(self._clients)))
            print("\t".join([""] + [str(client.getpeername())
                  for client in self._clients]))

    def accept_new_client(self) -> socket.socket:
        """
        Using `accept`, accepting a new client and adds it to clients list.

        This method also prints a "new client joined" messgae.

        ------

        Notes
        ------
        Since `accept` uses a blocking syscall, if there is no new socket at the moment,
        this method will block the process.
        """
        (client_socket, client_address) = self.socket.accept()
        self._clients.append(client_socket)
        print("New client joined!\t{}".format(client_address))
        self._print_client_sockets()
        return client_socket

    def select_clients(self) -> tuple[list[socket.socket], list[socket.socket],
                                      list[socket.socket]]:
        """
        Performes the function `select.select`.

        ------

        Returns
        ------
        - tuple[list, list, list]
            - (ready_to_read, ready_to_write, in_error).

        ------

        Notes
        ------
        Since `select` uses a blocking syscall, this method will block the process until
        one or more file descriptors are ready for some kind of I/O.
        """
        return select.select([self.socket] + self._clients, self._clients, [])

    def terminate_client(self, client: socket.socket) -> None:
        """
        Closes the client socket, removes user from `logged_users` and removes client
        from `clients`.

        This method alse prints a message to the screen.

        ------

        Parameters
        ------
        client: socket.socket
            - The socket to terminate (close).

        ------

        Raises
        ------
        - TypeError
            - If the argument is of inappropriate type
        """
        if not isinstance(client, socket.socket):
            raise TypeError
        if client not in self._clients:
            return
        self._clients.remove(client)
        try:
            if client.getpeername() in self._logged_users:
                del self._logged_users[client.getpeername()]
            assert client.getpeername() not in self._logged_users
            client.close()
        except OSError:
            pass
        print("Connection closed!")
        self._print_client_sockets()


# ====================
# ===== Main Function:

def main():
    """
    Main fuction, which runs a multy-clients server and serving all the requests.
    """
    print("Welcome to Trivia Server!\nstarting up on port 5678.")
    server = Server()
    print("Server is up and ready.")
    # - Main loop:
    while True:
        # - Use `select` for getting all the ready_to_read and ready_to_write clients:
        ready_to_read, ready_to_write = server.select_clients()[0:2]
        # - Handle ready_to_read:
        for curr in ready_to_read:
            # - In case of a new client:
            if curr is server.socket:
                server.accept_new_client()
            # - In case of an existing client:
            else:
                cmd, data = server.recv_message_and_parse(curr)
                if not cmd:
                    server.terminate_client(curr)
                else:
                    server.handle_client_message(curr, cmd, data)

        # handle ready to write
        server.send_messages_to_ready_sockets(ready_to_write)

if __name__ == '__main__':
    main()
