# ===== Module Description:

"""
# Chatlib

A module for all the the trivia-protocol constants and some basic functions and classes.

Provides:

1. Some constants that match the game protocol.

2. A base class called `ProtocolUser`, for both Client and Server.

3. Some helper functions for colored printing, using `colorama` module.

4. `User` & `Question` classes.

Examples
--------
>>> TODO:
... # sc
"""


# ====================
# ===== Imports:

# For Python versions between 3.7 to 3.9, we need the following line:
from __future__ import annotations
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
NUMBER_OF_ANSWERS = 4
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
    def _split_data(data: str, expected_fields: int) -> Union[list[str], None]:
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
    def _join_data(words: Union[list[str], tuple[str]]) -> str:
        """Gets a list or a tuple, joins all of it's fields to one string divided by the data delimiter.

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
        if not isinstance(words, list) and not isinstance(words, tuple):
            raise TypeError
        if not all(isinstance(word, str) for word in words):
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
    def _parse_message(msg: str) -> Union[tuple[str, str], tuple[None, None]]:
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


class Question:
    """
    A class represents a user in the trivia game.

    -------

    Attributes
    -------
    question

    optional_answers

    answer

    -------

    Methods
    -------
    get_question()
        - Returns the question.

    get_optional_answers()
        Returns a shallow copy of the optional_answers tuple.

    get_answer()
        Returns the correct answer.

    is_correct(answer_num)
        Gets an integer between 1-4. Returns whether this is the answer or not.
    """

    def __init__(self, question: str, optional_answers: tuple[str], answer: int) -> None:
        """
        Creates a new question.

        ----------

        Parameters
        ----------
        question : str
            The question itself.
        optional_answers : tuple[str]
            A tuple of four strings. Each one is a possible answer(str).
        answer : int
            The correct answer number.
        ----------

        Raises
        ------
        - TypeError
            - In case one of the parameters is of inappropriate type.
        - ValueError
            - In case the value of one of the parameters is inappropriate.
        """
        self.question = question
        self.optional_answers = optional_answers
        self.answer = answer

    @property
    def question(self) -> str:
        """:obj:`str`: The question itself.
        """
        return self._question

    @question.setter
    def question(self, question: str) -> None:
        if not isinstance(question, str):
            raise TypeError
        self._question = question

    @property
    def optional_answers(self) -> tuple[str]:
        """:obj:`tuple`[:obj:`str`]: A dict with four pairs.

        Each value in the tuple is a possible answer(str).
        """
        return self._optional_answers

    @optional_answers.setter
    def optional_answers(self, optional_answers: tuple[str]) -> None:
        if not isinstance(optional_answers, tuple):
            raise TypeError
        if not all(isinstance(s, str) for s in optional_answers):
            raise TypeError
        if not len(optional_answers) == NUMBER_OF_ANSWERS:
            raise ValueError
        self._optional_answers = optional_answers

    @property
    def answer(self) -> int:
        """:obj:`int`: The correct answer number. An integer between 1-4.
        """
        return self._answer

    @answer.setter
    def answer(self, answer: int) -> None:
        if not isinstance(answer, int):
            raise TypeError
        if not answer in range(1, NUMBER_OF_ANSWERS + 1):
            raise ValueError
        self._answer = answer

    @classmethod
    def dict_to_question(cls, question: dict[str, ]) -> Question:
        """
        A class-method which gets a dict an returns an appropriate `Question` instance.
        #### Avoid using this on an object that was not returned from `user_to_question`.

        ------
        Parameters
        ------
        question : dict
            - A dict of the correct format (see examples).

        ------
        Returns
        ------
        - Question
            - The `Question` instance.

        ------
        Raises
        ------
        - TypeError
            - If one of the arguments is of a wrong type.
        - KeyError
            - Wrong Mapping key in the dictionary.

        ------
        Examples:
        ------
        >>> User.dict_to_user({"question":"2+3 = ?", "optional_answers":("1", "5", "10", "0"),"answer":2})
        """
        if not isinstance(question, dict) or len(question) != 3:
            raise TypeError
        if list(question.keys()) != ["question", "optional_answers", "answer"]:
            raise KeyError
        return Question(question["question"], tuple(question["optional_answers"]),
                        question["answer"])

    def question_to_dict(self) -> dict:
        """
        Returns an appropriate dict for the calling `Question` instance.

        ------
        Returns
        ------
        - dict
            - An appropriate dict.
        """
        return {"question": self._question, "optional_answers": self._optional_answers,
                "answer": self._answer}

    def get_question(self) -> str:
        """
        Returns the question.

        ------

        Returns
        ------
        - str
            - The question.
        """
        return self._question

    def get_optional_answers(self) -> tuple[str]:
        """
        Returns the tuple of the optional answers.

        ------

        Returns
        ------
        - tuple[str]
            - All the four answers as a tuple.

        Example
        ------
        >>> q1.get_answers()
        ('<a1>', '<a2>', '<a3>', '<a4>').
        """
        return self._optional_answers

    def get_answer(self) -> int:
        """
        Returns the correct answer.

        ------

        Returns
        ------
        - int
            - The answer.
        """
        return self._answer

    def is_correct(self, answer_num: int) -> bool:
        """
        Gets an integer between 1-4. Returns whether this is the answer or not.

        ------

        Parameters
        ----------
        answer_num : int
            The answer num to be checked.

        Returns
        ------
        - bool
            - True - if correct.
            - False - if it is not correct.
        """
        if not isinstance(answer_num, int):
            raise TypeError
        return answer_num == self._answer


class User:
    """
    A class represents a user in the trivia game. For all the users the server contact with.

    -------

    Attributes
    -------
    name

    password

    score

    questions_asked

    -------

    Methods
    -------
    dict_to_user(users: dict[str, ])
        A class-method. Returns an appropriate `User` instance for a `dict`.

    user_to_dict()
        Returns an appropriate dict for the calling `User` instance.

    add_score(score_tp_add)
        Add the given score to the user score.

    get_score()
        Returns the current score of the user.

    mark_question_as_asked(question)
        Gets a question and add it to the list of questions_asked.

    was_question_asked(question)
        Gets a question number and checks whether the user has already been asked
        this question or not.
    """

    def __init__(self, name: str, password: str, score: int = 0,
                 questions_asked: Union[list[int], None] = None) -> None:
        """
        Creates a new user.

        ----------

        Parameters
        ----------
        name : str
            The user name.
        password : str
            The user password.
        score : int, (default 0)
            The user score.
        questions_asked : list[int], (default [])
            All the questions the user have already been asked.
        ----------

        Raises
        ------
        - TypeError
            - In case one of the parameters is of inappropriate type.
        """
        self.name = name
        self.password = password
        self.score = score
        self.questions_asked = questions_asked

    @property
    def name(self) -> str:
        """:obj:`str`: The user name.
        """
        return self._name

    @name.setter
    def name(self, user_name: str) -> None:
        if not isinstance(user_name, str):
            raise TypeError
        self._name = user_name

    @property
    def password(self) -> str:
        """:obj:`str`: The user password.
        """
        return self._password

    @password.setter
    def password(self, user_password: str) -> None:
        if not isinstance(user_password, str):
            raise TypeError
        self._password = user_password

    @property
    def score(self) -> str:
        """:obj:`str`: The user score (initialized to zero).
        """
        return self._score

    @score.setter
    def score(self, user_score: int) -> None:
        if not isinstance(user_score, int):
            raise TypeError
        # TODO: consider checking the question number...
        self._score = user_score

    @property
    def questions_asked(self) -> list[int]:
        """:obj:`list`[:obj:`int`]: All the questions the user have already been asked.

        #### Pay attention: The getter for this property returns a shallow copy of this list.
        """
        return self._questions_asked.copy()

    @questions_asked.setter
    def questions_asked(self, user_questions_asked: list[int]) -> None:
        if user_questions_asked is None:
            self._questions_asked = []
        else:
            if not isinstance(user_questions_asked, list):
                raise TypeError
            if not all(isinstance(v, int) for v in user_questions_asked):
                raise TypeError
            self._questions_asked = user_questions_asked

    @classmethod
    def dict_to_user(cls, user: dict[str, ]) -> User:
        """
        A class-method which gets a dict an returns an appropriate `User` instance.
        #### Avoid using this on an object that was not returned from `user_to_dict`. 

        ------
        Parameters
        ------
        user : dict
            - A dict of the correct format (see examples).

        ------
        Returns
        ------
        - User
            - The `User` object.

        ------
        Raises
        ------
        - TypeError
            - If one of the arguments is of a wrong type.
        - KeyError
            - Wrong Mapping key in the dictionary.

        ------
        Examples:
        ------
        >>> User.dict_to_user({"name": "Dan", "password": "123", "score": 3, "questions_asked": [1,3,5]})
        """
        if not isinstance(user, dict) or len(user) != 4:
            raise TypeError
        if list(user.keys()) != ["name", "password", "score", "questions_asked"]:
            raise KeyError
        return User(user["name"], user["password"], user["score"], user["questions_asked"])

    def user_to_dict(self) -> dict:
        """
        Returns an appropriate dict for the calling `User` instance.

        ------
        Returns
        ------
        - dict
            - An appropriate dict.
        """
        return {"name": self._name, "password": self._password,
                "score": self._score, "questions_asked": self._questions_asked}

    def get_name(self) -> str:
        """
        Returns the name of the user.

        ------

        Returns
        ------
        - str
            - The username.
        """
        return self._name

    def get_password(self) -> str:
        """
        Returns the password of the user.

        ------

        Returns
        ------
        - str
            - The password.
        """
        return self._password

    def add_score(self, score_to_add: int) -> int:
        """
        Add the given score to the user score.

        ------

        Parameters
        ------
        score_to_add : int
            - The score should be added to the user.
        ------

        Returns
        ------
        - int
            - The user's new score.
        ------

        Raises
        ------
        - TypeError
            - In case one of the parameters is of inappropriate type.
        """

        if not isinstance(score_to_add, int):
            raise TypeError
        self._score += score_to_add
        return self._score

    def get_score(self) -> int:
        """
        Returns the current score of the user.

        ------

        Returns
        ------
        - int
            - The user's current score.
        """
        return self._score

    def mark_question_as_asked(self, question: int) -> None:
        """
        Gets a question and add it to the list of questions_asked.

        ------

        Parameters
        ------
        question : int
            - The question number.
        ------

        Raises
        ------
        - TypeError
            - In case one of the parameters is of inappropriate type.
        """
        if not isinstance(question, int):
            raise TypeError
        # TODO: consider checking the question number...

        if question in self._questions_asked:
            return
        self._questions_asked.append(question)

    def was_question_asked(self, question: int) -> bool:
        """
        Gets a question number and checks whether the user has already been asked
        this question or not.

        ------

        Parameters
        ------
        question : int
            - The question number.
        ------

        Returns
        ------
        - bool
            - True - If the user has already been asked this question.
            - False - Otherwise.
        ------

        Raises
        ------
        - TypeError
            - In case one of the parameters is of inappropriate type.
        """
        if not isinstance(question, int):
            raise TypeError
        return question in self._questions_asked


# ====================
# ===== Main Function:

def main():
    """
    Main function.
    """


if __name__ == '__main__':
    main()
