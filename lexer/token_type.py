from enum import Enum, auto


class TokenType(Enum):
    # Identifier
    IDENTIFIER = auto()
    # Datatype
    DATA_TYPE = auto()
    VOID_TYPE = auto() 

    # Literals
    INTEGER_LITERAL = auto()
    FLOAT_LITERAL = auto() 
    STRING_LITERAL = auto()
    CHAR_LITERAL = auto()
    BOOL_LITERAL = auto()

    # Keywords
    FOR = auto()
    WHILE = auto()
    BR_CONT = auto()
    IF = auto()
    ELSE = auto()
    RETURN = auto()
    OBJ_CREATOR = auto()
    DECLARE = auto()
    CALL = auto()


    # OOP Keywords
    CLASS = auto()
    STRUCT = auto()
    INTERFACE = auto()
    INHERITS = auto()
    IMPLEMENTS = auto()
    MAIN = auto()
    STATIC = auto()
    ACCESS_MODIFIER = auto()
    SUPER = auto()
    THIS = auto()
    CONSTRUCTOR = auto()
    FUNCTION = auto()


    
    # Operators and Precedence
    PLUS_MINUS = auto()
    DIVIDE_MODULUS = auto()
    POINTER_MULTIPLY = auto()
    RELATIONAL_OPERATOR = auto()
    ASSIGNMENT_OPERATOR = auto() 
    COMP_ASSIGNMENT_OPERATOR = auto()
    LOGICAL_AND = auto() 
    LOGICAL_OR = auto()
    NOT_OPERATOR = auto() 
    INC_DEC = auto()
    DOT = auto()
    ARROW = auto()
    SCOPE_RESOLUTION = auto()
    REF_OPERATOR = auto()

    # Punctuators
    SEMICOLON = auto()
    COMMA = auto()
    COLON = auto()
    ROUND_BRACKET_OPEN = auto()
    ROUND_BRACKET_CLOSE = auto()
    CURLY_BRACKET_OPEN = auto()
    CURLY_BRACKET_CLOSE = auto()
    SQUARE_BRACKET_OPEN = auto()
    SQUARE_BRACKET_CLOSE = auto()


    # Invalid
    INVALID_LEXEME = auto()

    # End Of File 
    EOF_MARKER = auto()
    


