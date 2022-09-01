# ===== Imports:

# For Python versions between 3.7 to 3.9, we need the following line:
from __future__ import annotations
import chatlib
from typing import Union
from chatlib import ProtocolUser, PROTOCOL_CLIENT, PROTOCOL_SERVER_OK


# ====================

# ===== Constants:

LOCAL_HOST = "127.0.0.1"  # Our server will run on same computer as client
SERVER_IP = LOCAL_HOST
DEFAULT_TIMEOUT = 10


# ====================
# Errors Messages:


INPUT_TOO_LONG_MSG = "ERROR: Input exceeds the maximum length of data"

NO_SUCH_INPUT_MSG = "ERROR: No such an option."

UNKNOWN_ERROR_OCCURRED_MSG = "ERROR: An unknown error occured."

TRY_AGAIN_MSG = "Please try again."


# ====================
# ===== Utility Functions:

def _print_error_try_again(error: str):
    print(error, TRY_AGAIN_MSG)


def _print_unknown_error():
    print(UNKNOWN_ERROR_OCCURRED_MSG)


def _print_unknown_error_try_again():
    print(UNKNOWN_ERROR_OCCURRED_MSG, TRY_AGAIN_MSG)


def _print_send_success(cmd_name):
    chatlib.print_server_msg(chatlib.SUCCESS_PRINT_CLIENT[cmd_name])


# ====================
# ===== Classes:


class Client(ProtocolUser):
    """
    A class represents a client for trivia-player, derived from `chatlib.ProtocolUser` class.

    -------

    Attributes
    -------
    socket : socket.socket
        The socket of the client/user.

    -------

    Protected Methods
    -------
    _split_data(data, expected_fields)

    _join_data(words)

    _build_message(cmd, msg)

    _parse_message(msg)

    _recv_message_and_parse()

    _build_and_send_message(cmd, data='')

    _build_send_recv_parse(cmd, data='', print_success=False)

    Public Methods
    -------
    terminate()
        Closes the socket (for use when the socket is no longer needed).

    """

    def __init__(self, server_ip: str = SERVER_IP, server_port: int = chatlib.SERVER_PORT) -> None:
        """
        Creates a `Client` by creating a client-socket and connects it to the server, using `connect` method.

        ----------

        Parameters
        ----------
        server_ip : str, (default SERVER_IP)
            The server IP. The default is for a 'local host' server.
        server_port : int, (default SERVER_PORT)
            The server port.
        ----------

        Raises
        ------
        - TypeError
            - In case one of the parameters is of inappropriate type.
        - ConnectionRefusedError
            - In case of connection failure.
        """
        super().__init__()
        self.socket.settimeout(DEFAULT_TIMEOUT)
        # Connect the socket to the server's socket, whith its IP and port:
        try:
            self.socket.connect((server_ip, server_port))
        except ConnectionRefusedError as e:
            raise e

    def _recv_message_and_parse(self) -> Union[tuple[str, str], tuple[None, None]]:
        """
        Recieves a new message from the socket and then parses the message using `chatlib`.

        ------

        Returns
        ------
        - tuple[str, str]
            - If succeded - returns a tuple (cmd, msg). (cmd is the command and msg is the massege)
        - tuple[None, None]
            - If error occured with the message recived form the server,
            returns a tuple (None, None) (the return value of `_parse_message`).
        ------

        Raises
        ------
        - InterruptedError
            - If `recv` failed (i.e the syscall is interrupted).
        """

        data = ''
        try:
            data = self.socket.recv(chatlib.BUFFER_SIZE).decode()
        except InterruptedError as error:
            raise error
        return ProtocolUser._parse_message(data)

    def _build_and_send_message(self, cmd: str, data: str = '') -> str:
        """
        Builds a new message using `chatlib`, wanted code and message. Then, sends it to the socket.

        ------

        Parameters
        ------
        cmd : str
            - A command string, to send to the server.

        data : str, (default '')
            - A data srting, to send to the server.
        ------

        Returns
        ------
        - str
            - The messgae sent to the socket.

        Raises
        ------
        - TypeError
            - If the argument is of inappropriate type
        - ValueError
            - If `cmd` or `data` does not match the protocol.
        - InterruptedError
            - If `send` failed (i.e the syscall is interrupted).
        """

        if not isinstance(cmd, str) or not isinstance(data, str):
            raise TypeError
        cmd_protocol = PROTOCOL_CLIENT[cmd]
        msg = ProtocolUser._build_message(cmd_protocol, data)
        if not msg:
            raise ValueError
        try:
            self.socket.send(msg.encode())
        except InterruptedError as error:
            raise error
        return msg

    def _build_send_recv_parse(self, cmd: str, data: str = '',
                               print_success: bool = False) -> tuple[str, str]:
        """
        Gets the command and the message, sends them to the socket,
        (Optional: prints a success messgae) and recives the response from the socket.

        Returns the response as a tuple of (cmd,msg).

        (Uses the functions `_build_and_send_message` and `_recv_message_and_parse`).

        ------

        Parameters
        ------
        cmd : str
            - A command string, to send to the socket.

        data : str, (default '')
            - A data srting, to send to the socket.

        print_success : bool, (default False)
            - A boolean value, telling the function whether to print a success line
            after sending or not.
        ------

        Returns
        ------
        - tuple[str, str]
            - If succeded - returns a tuple (cmd, msg). (cmd is the command and msg is the massege)
        - tuple[None, None]
            - If error occured with the message recived form the socket,
            returns a tuple (None, None) (the return value of `_parse_message`).
        ------

        Raises
        ------
        - TypeError
            - If the argument is of inappropriate type
        - ValueError
            - If `cmd` or `data` does not match the protocol.
        - InterruptedError
            - If `send` or `recv` failed (i.e the syscall is interrupted).
        """

        if not isinstance(print_success, bool):
            raise TypeError

        try:
            self._build_and_send_message(cmd, data)
        except Exception as error:
            raise error

        if print_success:
            _print_send_success(cmd)

        recv_cmd, recv_msg = '', ''
        try:
            (recv_cmd, recv_msg) = self._recv_message_and_parse()
        except Exception as error:
            raise error

        return (recv_cmd, recv_msg)

    def login(self) -> None:
        """
        Sends a login request to the server, via the socket, using a username and password provided by the user.

        If login fails, will try again untill success.
        """
        cmd_name = 'login'
        recv_cmd, recv_msg = '', ''
        while True:
            username = input("Please enter username: \n")
            password = input("Please enter password: \n")
            data = Client._join_data([username, password])
            if (len(data) > chatlib.DATA_FIELD_MAX_LENGTH):
                _print_error_try_again(INPUT_TOO_LONG_MSG)
            try:
                self._build_and_send_message(cmd_name, data)
            except Exception as e:
                assert (not isinstance(e, (TypeError, ValueError)))
                _print_unknown_error_try_again()
                continue
            (recv_cmd, recv_msg) = self._recv_message_and_parse()
            if recv_cmd == PROTOCOL_SERVER_OK['login'] and recv_msg == '':
                _print_send_success(cmd_name)
                break
            elif recv_cmd == chatlib.PROTOCOL_SERVER_ERROR:
                _print_error_try_again(recv_msg)
            else:
                _print_unknown_error_try_again()

    def logout(self) -> None:
        """
        Send a logout request to the server, via the socket.

        NOTE: If done using this client, you should call `terminate()`, that will close the socket. 

        ------

        Raises
        ------
        - InterruptedError
            - If `send` failed (i.e the syscall is interrupted).
        ------
        """
        cmd_name = 'logout'
        try:
            self._build_and_send_message(cmd_name)
        except Exception as e:
            raise e
        _print_send_success(cmd_name)

    def get_score(self) -> None:
        """
        Prints the current score of the user. In case of error message, prints the message.

        (Uses the function `_build_send_recv_parse`).

        ------

        Raises
        ------
        - InterruptedError
            - If `send` or `recv` failed (i.e the syscall is interrupted).
        ------
        """
        cmd_name = "get_score"
        recv_cmd, recv_msg = '', ''
        try:
            (recv_cmd, recv_msg) = self._build_send_recv_parse(cmd_name)
        except Exception as e:
            raise e
        if recv_cmd == PROTOCOL_SERVER_OK[cmd_name]:
            chatlib.print_server_msg("Your score is: " + recv_msg)
        elif recv_cmd == chatlib.PROTOCOL_SERVER_ERROR:
            _print_unknown_error()

    def get_highscore(self) -> None:
        """
        Prints the table score, as recived from the server. In case of error message, prints the message.

        (Uses the function `_build_send_recv_parse`).

        ------

        Parameters
        ------
        client_socket : socket object
            - The client-socket, which was returned from the `connect`.
        ------

        Raises
        ------
        - TypeError
            - If the argument is of inappropriate type
        - ValueError
            - If `cmd` or `data` does not match the protocol.
        - InterruptedError
            - If `send` or `recv` failed (i.e the syscall is interrupted).
        ------
        """
        cmd_name = "get_highscore"
        recv_cmd, recv_msg = '', ''
        try:
            (recv_cmd, recv_msg) = self._build_send_recv_parse(cmd_name)
        except Exception as e:
            raise e
        if recv_cmd == PROTOCOL_SERVER_OK[cmd_name]:
            chatlib.print_server_msg("High-Score table is:\n" + recv_msg)
        elif recv_cmd == chatlib.PROTOCOL_SERVER_ERROR:
            _print_unknown_error()

    @staticmethod
    def _printQuestion(recv_cmd: str, recv_msg: str) -> None:
        """
        Private method. Gets the `cmd` and the `msg` and check them.

        If everything is legal - parses it and prints it.

        If there is an error with the `cmd` or with the `msg`, raises ValueError.

        (Uses the function `Client._split_data`).

        ------

        Parameters
        ------
        recv_cmd : str
            - The recived command. Should be `YOUR_QUESTION`. 
            `Must be str!`

        recv_msg : str
            - The question. A string of the format `id#question#answer1#answer2#answer3#answer4`. 
            `Must be str!`
        ------

        Raises
        ------
        - ValueError
            - If one of the parameters does not match the protocol (i.e bad response).
        ------
        """
        if recv_cmd != PROTOCOL_SERVER_OK['get_question']:
            raise ValueError
        q_parts = Client._split_data(recv_msg, chatlib.QUESTION_PRATS_NUM)
        if not q_parts:
            raise ValueError
        msg = "Q#{} : {}:\n\
            1. {}\n\
            2. {}\n\
            3. {}\n\
            4. {}".format(*q_parts)
        chatlib.print_server_msg(msg)

    @staticmethod
    def _printFeedback(recv_cmd: str, recv_msg: str) -> None:
        """
        Private method. Gets the `cmd` and the `msg` and check them.

        If everything is legal - prints the feedback, whether the answer is correct or not.

        If there is an error with the `cmd` or with the `msg`, raises ValueError.

        (Uses the function `Client._split_data`).

        ------

        Parameters
        ------
        recv_cmd : str
            - The recived command. Should be `CORRECT_ANSWER` or `WRONG_ANSWER`. 
            `Must be str!`

        recv_msg : str
            - The question. A string of the format `correct_answer` if wrong, or an empty string if correct. 
            `Must be str!`
        ------

        Raises
        ------
        - ValueError
            - If one of the parameters does not match the protocol (i.e bad response).
        ------
        """
        if recv_cmd == PROTOCOL_SERVER_OK["send_answer_correct"]:
            chatlib.print_server_msg("YES!!!!!")
        elif recv_cmd == PROTOCOL_SERVER_OK["send_answer_wrong"]:
            chatlib.print_server_msg("Nope! Coorect answer is #" + recv_msg)
        else:
            raise ValueError

    def play_question(self) -> None:
        """
        A method for playing a trivia question.

        Gets a question from the server, displays it on screen, gets an answer and finally displays a feedback.

        (Uses the function `_build_send_recv_parse`).

        ------

        Raises
        ------
        - InterruptedError
            - If `send` or `recv` failed (i.e the syscall is interrupted).
        ------
        """

        # Ask a question from the server:
        cmd_name = 'get_question'
        recv_cmd, recv_msg = '', ''
        try:
            (recv_cmd, recv_msg) = self._build_send_recv_parse(cmd_name)
        except Exception as e:
            raise e
        # Print the question:
        try:
            Client._printQuestion(recv_cmd, recv_msg)
        except:
            _print_unknown_error()
            return
        # Get an answer from the user:
        answer = ''
        while True:
            answer = input("Please choose an answer [1-4]: ")
            if answer in [str(i) for i in range(1, 5)]:
                break
            _print_error_try_again(NO_SUCH_INPUT_MSG)

        # Send the answer to the server:
        cmd_name = 'send_answer'

        q_num = Client._split_data(recv_msg, chatlib.QUESTION_PRATS_NUM)[0]
        data = Client._join_data([q_num, answer])

        try:
            (recv_cmd, recv_msg) = self._build_send_recv_parse(cmd_name, data)
        except Exception as e:
            raise e

        # Get a feedback about the answer:
        try:
            Client._printFeedback(recv_cmd, recv_msg)
        except:
            _print_unknown_error()
            return

    @staticmethod
    def _printLoggedUsers(recv_cmd: str, recv_msg: str) -> None:
        """
        Private method. Gets the `cmd` and the `msg` and check them.

        If everything is legal - prints all the looged users.

        If there is an error with the `cmd` or with the `msg`, raises ValueError.

        (Uses the function `Client._split_data`).

        ------

        Parameters
        ------
        recv_cmd : str
            - The recived command. Should be `LOGGED_ANSWER`. 
            `Must be str!`

        recv_msg : str
            - The question. A string of all the users, with a comma (',') as a delimeter between them. 
            `Must be str!`
        ------

        Raises
        ------
        - ValueError
            - If one of the parameters does not match the protocol (i.e bad response).
        ------
        """
        if recv_cmd != PROTOCOL_SERVER_OK['get_logged_users']:
            raise ValueError
        users = recv_msg.split(chatlib.LOGGED_USERS_DELIMETER)
        msg = "Logged users: \n" + ', '.join(users)
        chatlib.print_server_msg(msg)

    def get_logged_users(self) -> None:
        """
        Prints all the users connected to that server.

        (Uses the function `_build_send_recv_parse`).

        ------

        Raises
        ------
        - InterruptedError
            - If `send` or `recv` failed (i.e the syscall is interrupted).
        ------
        """
        cmd_name = "get_logged_users"
        recv_cmd, recv_msg = '', ''
        try:
            (recv_cmd, recv_msg) = self._build_send_recv_parse(cmd_name)
        except Exception as e:
            raise e
        try:
            Client._printLoggedUsers(recv_cmd, recv_msg)
        except Exception as e:
            _print_unknown_error()
            return


# ====================

# ===== Main Function:


def main():
    # Create the client, connect it to the server and login:
    my_player = Client()  # TODO: check if `connect` raises an exception.
    my_player.login()

    # Main loop for sending and reciving:

    prompt_dict = {
        'p': "Play a trivia question",
        's': 'Get my score',
        'h': 'Get high score',
        'l': "Get logged users",
        'q': 'Quit'
    }
    prompt = '\n'.join([(k + '\t' + v) for k, v in prompt_dict.items()])
    prompt += '\nPlease enter your choise: '
    cmd_input = ''
    while True:
        cmd_input = input(prompt)
        if(cmd_input == 'q'):
            break
        if(cmd_input == 'p'):
            my_player.play_question()
        elif(cmd_input == 's'):
            my_player.get_score()
        elif(cmd_input == 'h'):
            my_player.get_highscore()
        elif(cmd_input == 'l'):
            my_player.get_logged_users()
        else:
            _print_error_try_again(NO_SUCH_INPUT_MSG)

    # Terminate - logout and close:
    my_player.logout()
    my_player.terminate()


# ====================

if __name__ == '__main__':
    main()
