# ===== Module Description:


"""
# Chatlib
A modul for all the the trivia-protocol constants and some basic functions and classes.

Examples
--------
>>> TODO:
... # sc
"""

# ====================
# ===== Imports:


import socket
from abc import ABC, abstractmethod
from colorama import Fore, Style, init as colorma_init
from typing import Union


# ====================
# ===== Constants:


DATA_DELIMETER = '#'

FIELDS_DELIMETER = '|'

CMD_SUFFIX_CHAR = ' '

CMD_FIELD_LENGTH = 16

LEN_FIELD_LENGTH = 4

CMD_FIELD_MAX_LENGTH = 16

DATA_FIELD_MAX_LENGTH = 10 ** LEN_FIELD_LENGTH - 1

MESSAGE_PARTS = 3

BUFFER_SIZE = 2 ** 10
"""Max size of the socket buffer"""

SERVER_PORT = 5678

QUESTION_PRATS_NUM = 6

LOGGED_USERS_DELIMETER = ','

CHATLIB_ERROR_RETURN = None


# ====================

# ===== Protocol Constants:


SUCCESS_PRINT_CLIENT = {
    "login": "Logged in!",
    "logout": "Goodbye",
    "get_score": " Getting score",
    "get_highscore": "Getting high score",
    "get_question": " Getting question",
    "send_answer": "Sending answer",
    "get_logged_users": "Getting logged users"
}


PROTOCOL_CLIENT = {
    "login": "LOGIN",
    "logout": "LOGOUT",
    "get_score": "MY_SCORE",
    "get_highscore": "HIGHSCORE",
    "get_question": "GET_QUESTION",
    "send_answer": "SEND_ANSWER",
    "get_logged_users": "LOGGED"
}

PROTOCOL_SERVER_OK = {
    "login": "LOGIN_OK",
    "get_score": "YOUR_SCORE",
    "get_highscore": "ALL_SCORE",
    "get_question": "YOUR_QUESTION",
    "send_answer_correct": "CORRECT_ANSWER",
    "send_answer_wrong": "WRONG_ANSWER",
    "get_logged_users": "LOGGED_ANSWER"
}

PROTOCOL_SERVER_ERROR = "ERROR"


# ====================
# ===== Utility Functions:

# ====================
# ===== Library Functions:


def init_colored_print() -> None:
    """
    An initialization for the color printing.
    """
    colorma_init(convert=True)


def print_server_msg(s: str) -> None:
    """
    A convenient way to print the server messgaes, in a blue color.
    """
    print(Fore.LIGHTBLUE_EX + s + Style.RESET_ALL)


def printDebug(s: str) -> None:
    """
    A convenient way to print errors, for debugging.
    """
    print(Fore.LIGHTRED_EX + s + Style.RESET_ALL)


# For colored print:
init_colored_print()


# ====================
# ===== Library Classes:


class ProtocolUser(ABC):
    """
    An abstract class represents a TCP client, with the functionality of send and receive data,
    according to `chatlib` protocol.

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

    Public Methods
    -------

    terminate()
        Closes the socket (for use when the socket is no longer needed).

    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Creates a generic socket, uses the TCP protocol.

        ----------
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    def _split_data(data: str, expected_fields: int) -> Union[list[str],None]:
        """Gets a string and number of expected fields in it. Splits the string
        using protocol's data field delimiter (#) and validates that there are
        correct number of fields.

        ------

        Parameters
        ------
        data : str
            - A string contains the row data.

        expected_fields : int
            - Number of fields in data.
        ------

        Returns
        ------
        - List[str]
            - list of fields if all ok.
        - None
            - If the number of fields is not as given.
        ------

        Raises
        ------
        - TypeError
            - If one of the arguments is of a wrong type.
        """

        if (not isinstance(data, str)) or (not isinstance(expected_fields, int)):
            raise TypeError

        data_list = data.split(DATA_DELIMETER)

        if len(data_list) != expected_fields:
            return CHATLIB_ERROR_RETURN
        return data_list

    @staticmethod
    def _join_data(words: list[str]) -> str:
        """Gets a list, joins all of it's fields to one string divided by the data delimiter.

        ------

        Parameters
        ------
        words : list[str]
            - A list of words to join together into a one srting.
        ------

        Returns
        ------
        - str
            - string that looks like cell1#cell2#cell3
        ------

        Raises
        ------
        - TypeError
            - If one of the arguments is of a wrong type.
        """

        if (not isinstance(words, list)) or (not all(isinstance(word, str) for word in words)):
            raise TypeError
        return DATA_DELIMETER.join(words)

    @staticmethod
    def _build_message(cmd: str, msg: str) -> str:
        """Gets command name (str) and data field (str) and creates a valid protocol message

        ------

        Parameters
        ------
        cmd : str
            - The command name.

        msg : str
            - The data field.
        ------

        Returns
        ------
        - str
            - A valid protocol message, of format: `CCCCCCCCCCCCCCCC|LLLL|MMM`
        - None
            - If `cmd` or `msg` does not match the protocol.
        ------

        Raises
        ------
        - TypeError
            - If one of the arguments is of a wrong type.
        """

        if (not isinstance(cmd, str)) or (not isinstance(msg, str)):
            raise TypeError

        if (len(cmd) > CMD_FIELD_MAX_LENGTH) or (len(msg) > DATA_FIELD_MAX_LENGTH):
            return CHATLIB_ERROR_RETURN

        cmd_field = cmd.ljust(CMD_FIELD_LENGTH, CMD_SUFFIX_CHAR)
        data_len_field = str(len(msg)).zfill(LEN_FIELD_LENGTH)
        data_field = msg
        return FIELDS_DELIMETER.join([cmd_field, data_len_field, data_field])

    @staticmethod
    def _parse_message(msg: str) -> Union[tuple[str, str],tuple[None, None]]:
        """Parses protocol message and returns command name and data field

        ------

        Parameters
        ------
        msg : str
            - [description]
        ------

        Returns
        ------
        - tuple[str, str]
            - A tuple of strings - [cmd, msg].
        - tuple[None, None]
            - If some error occured - [None, None]
        ------

        Raises
        ------
        - TypeError
            - If one of the arguments is of a wrong type.
        - ConnectionResetError
            - May raise it if the other side is closed forcibly.
        """

        # Check type of msg:
        if not isinstance(msg, str):
            raise TypeError
        failure = (CHATLIB_ERROR_RETURN, CHATLIB_ERROR_RETURN)
        msg_parts = msg.split(FIELDS_DELIMETER)

        # Check there are 3 strings seperated by the delimeter:
        if len(msg_parts) != MESSAGE_PARTS:
            return failure
        cmd, data_len_str, data = tuple(msg_parts)

        # Check cmd:
        if len(cmd) != CMD_FIELD_LENGTH:
            return failure

        # Check data_len:
        try:
            data_len = int(data_len_str)
        except:
            return failure
        if not 0 <= data_len < DATA_FIELD_MAX_LENGTH:
            return failure

        # Check data:
        if data_len != len(data):
            return failure

        return (cmd.strip(), data)

    def terminate(self) -> None:
        """
        Closes the socket, using `close` method (for use when the socket is no longer needed).
        """
        try:
            self.socket.close()
        except:
            pass


# ====================

# ===== Main Function:

def main():
    """
    Main function.
    """


# ====================

if __name__ == '__main__':
    main()
