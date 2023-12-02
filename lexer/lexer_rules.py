from lexer.token_type import TokenType as tt
import re

KEYWORDS = {
    "for": tt.FOR,
    "while": tt.WHILE,
    "break": tt.BR_CONT,
    "continue": tt.BR_CONT,
    "if": tt.IF,
    "else": tt.ELSE,
    "return": tt.RETURN,
    "makeObj": tt.OBJ_CREATOR,
    "declare": tt.DECLARE,
}

DATATYPES = {
    "int": tt.DATA_TYPE,
    "float": tt.DATA_TYPE,
    "char": tt.DATA_TYPE,
    "string": tt.DATA_TYPE,
    "bool": tt.DATA_TYPE,
    "void": tt.VOID_TYPE,
}

OOP_KEYWORDS = {
    "class": tt.CLASS,
    "struct": tt.STRUCT,
    "interface": tt.INTERFACE,
    "inherits": tt.INHERITS,
    "implements": tt.IMPLEMENTS,
    "mainEntry": tt.MAIN,
    "static": tt.STATIC,
    "public": tt.ACCESS_MODIFIER,
    "private": tt.ACCESS_MODIFIER,
    "protected": tt.ACCESS_MODIFIER,
    "super": tt.SUPER,
    "this": tt.THIS,
    "constructor": tt.CONSTRUCTOR,
    "function": tt.FUNCTION
}

OPERATORS = {
    "+": tt.PLUS_MINUS,
    "-": tt.PLUS_MINUS,
    "*": tt.POINTER_MULTIPLY,
    "/": tt.DIVIDE_MODULUS,
    "%": tt.DIVIDE_MODULUS,
    "<": tt.RELATIONAL_OPERATOR,
    ">": tt.RELATIONAL_OPERATOR,
    "<=": tt.RELATIONAL_OPERATOR,
    ">=": tt.RELATIONAL_OPERATOR,
    "!=": tt.RELATIONAL_OPERATOR,
    "==": tt.RELATIONAL_OPERATOR,
    "=": tt.ASSIGNMENT_OPERATOR,
    "+=": tt.COMP_ASSIGNMENT_OPERATOR,
    "-=": tt.COMP_ASSIGNMENT_OPERATOR,
    "*=": tt.COMP_ASSIGNMENT_OPERATOR,
    "/=": tt.COMP_ASSIGNMENT_OPERATOR,
    "%=": tt.COMP_ASSIGNMENT_OPERATOR,
    "!": tt.NOT_OPERATOR,
    "&&": tt.LOGICAL_AND,
    "||": tt.LOGICAL_OR,
    "++": tt.INC_DEC,
    "--": tt.INC_DEC,
    ".": tt.DOT,
    "->": tt.ARROW,
    "::": tt.SCOPE_RESOLUTION,
    "&": tt.REF_OPERATOR,
}

PUNCTUATORS = {
    ";": tt.SEMICOLON,
    ",": tt.COMMA,
    # ":": tt.COLON,
    "(": tt.ROUND_BRACKET_OPEN,
    ")": tt.ROUND_BRACKET_CLOSE,
    "{": tt.CURLY_BRACKET_OPEN,
    "}": tt.CURLY_BRACKET_CLOSE,
    "[": tt.SQUARE_BRACKET_OPEN,
    "]": tt.SQUARE_BRACKET_CLOSE,
}


ALL_RULES = KEYWORDS | DATATYPES | OOP_KEYWORDS | OPERATORS | PUNCTUATORS


def match_token_type(token_str: str):
    if re.match(r"^(true|false)$", token_str):
        return tt.BOOL_LITERAL
    elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", token_str):
        return tt.IDENTIFIER
    elif re.match(r"^[-+]?[0-9]+$", token_str):
        return tt.INTEGER_LITERAL
    elif re.match(r"^[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?$", token_str):
        return tt.FLOAT_LITERAL
    elif re.match(r'^".*"$', token_str):
        if not token_str.endswith(r"\""):
            return tt.STRING_LITERAL
        elif token_str.endswith(r'\\"'):
            return tt.STRING_LITERAL

    elif re.match(r"^'.{0,2}'", token_str):
        return tt.CHAR_LITERAL
    return tt.INVALID_LEXEME


special_characters = [
    "n",  # Newline
    "r",  # Carriage Return
    "t",  # Tab
    "\\",  # Backslash
    "'",  # Single Quote
]
