from lexer.lexer_rules import (
    PUNCTUATORS,
    OPERATORS,
    ALL_RULES,
    match_token_type,
    special_characters,
)
from lexer.token import Token
from lexer.token_type import TokenType as tt
from typing import List


class Lexer:
    def __init__(self, source_code: str) -> None:
        self.source_code: str = source_code
        self.position: int = 0
        self.current_line: int = 1
        self.temp_word: str = ""
        self.token_list: List[Token] = []

    @property
    def current_char(self) -> str:
        return self.source_code[self.position]

    @property
    def in_string_literal(self) -> bool:
        if self.temp_word.startswith('"'):
            if self.current_char == "\n":
                return False
            if len(self.temp_word) > 1 and self.temp_word.endswith('"'):
                if self.temp_word.endswith(r'\\"'):
                    return False
                elif self.temp_word.endswith(r"\""):
                    return True
                else:
                    return False
            return True
        return False

    @property
    def in_char_literal(self) -> bool:
        if self.temp_word.startswith("'"):
            if self.current_char == "\n":
                return False
            if len(self.temp_word) >= 3:
                if (
                    self.temp_word[1] == "\\"
                    and self.temp_word[2] not in special_characters
                ):
                    return False
                if self.temp_word[1] != "\\":
                    return False
            if len(self.temp_word) >= 4 and self.temp_word[1] == "\\":
                return False

            if self.temp_word.count("'") % 2 == 0:
                return False

            return True
        return False

    @property
    def in_multi_line_comment(self):
        if self.temp_word.startswith("/*"):
            if self.temp_word.endswith("*") and self.current_char == "/":
                return False
            return True
        return False

    @property
    def in_single_line_comment(self):
        if self.temp_word.startswith("//"):
            if self.current_char == "\n":
                return False
            return True
        return False

    @property
    def should_ignore(self):
        return self.in_single_line_comment or self.in_multi_line_comment

    @property
    def is_finished(self) -> bool:
        return self.position >= len(self.source_code)

    def advance(self):
        self.position += 1

    def should_break(self) -> bool:
        if not self.temp_word:
            return False

        if self.in_char_literal or self.in_string_literal:
            return False

        if self.current_char == "." and "." not in self.temp_word:
            if match_token_type(self.temp_word) == tt.IDENTIFIER:
                return True
            is_next_char_digit = (
                self.source_code[self.position + 1].isdigit()
                if self.position + 1 < len(self.source_code)
                else None
            )
            if self.temp_word.lstrip("+-").isdigit() or is_next_char_digit:
                return False

        if self.temp_word == "." and self.current_char.isdigit():
            return False

        if self.current_char in [" ", "\n", "\t"]:
            return True

        if (
            self.current_char in ["'", '"']
            and '"' not in self.temp_word
            and "'" not in self.temp_word
        ):
            return True

        if self.temp_word + self.current_char in ["//", "/*"]:
            return False

        if self.current_char in PUNCTUATORS | OPERATORS:
            # if self.current_char == '.' and '.' in self.temp_word:
            #     return False
            if (
                self.temp_word + self.source_code[self.position : self.position + 1]
                in PUNCTUATORS | OPERATORS
            ):
                return False

            return True

        if self.temp_word in ["+", "-"] and self.current_char.isdigit():
            if self.token_list[-1].token_type in [
                tt.ASSIGNMENT_OPERATOR,
                tt.COMP_ASSIGNMENT_OPERATOR,
                *OPERATORS.values()
                # tt.IDENTIFIER,
                # tt.INTEGER_LITERAL,
                # tt.FLOAT_LITERAL,
            ]:
                return False

        if self.temp_word in PUNCTUATORS | OPERATORS:
            return True

        if not self.in_char_literal and self.temp_word.startswith("'"):
            return True

        if not self.in_string_literal and self.temp_word.startswith('"'):
            return True

        return False

    def generate_token(self) -> Token:
        token_type = ALL_RULES.get(self.temp_word)
        if token_type is None:
            token_type = match_token_type(self.temp_word)
        return Token(token_type, self.temp_word, self.current_line)

    def tokenize(self) -> List[Token]:
        while not self.is_finished:
            if not self.should_ignore and self.should_break():
                self.token_list.append(self.generate_token())
                self.temp_word = ""

            if self.current_char == "\n":
                self.current_line += 1

            if not self.should_ignore and self.current_char not in [
                " ",
                "\n",
                "\t",
            ]:
                self.temp_word += self.current_char

            self.advance()
            if not self.should_ignore:
                if self.temp_word.startswith("/*"):
                    self.advance()
                    self.temp_word = ""
                elif self.temp_word.startswith("//"):
                    self.temp_word = ""

        if self.temp_word:
            self.token_list.append(self.generate_token())

        self.token_list.append(Token(tt.EOF_MARKER, "", self.current_line))

        return self.token_list
