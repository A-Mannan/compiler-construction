from lexer.token_type import TokenType
from dataclasses import dataclass


@dataclass
class Token:
    token_type: TokenType
    value: str
    line_number: int


