from lexer.lexer import Lexer
from lexer.token_type import TokenType as tt
from parser.parser import Parser
from tabulate import tabulate
import json


with open("./tests/test7.txt") as file:
    lexer = Lexer(file.read())
    tokens = lexer.tokenize()

    token_tuples = []
    for token_obj in tokens:
        token_tuples.append(
            (
                token_obj.token_type.name,
                token_obj.value.strip(r"'").strip('"')
                if token_obj.token_type != tt.INVALID_LEXEME
                else token_obj.value,
                token_obj.line_number,
            )
        )

    print(
        tabulate(
            token_tuples,
            headers=["Token Type", "Value", "Line Number"],
            tablefmt="orgtbl",
        )
    )

    print()

    parser = Parser(tokens)
    parse_tree = parser.parse()

    if parse_tree is not None:
        with open("./output/parse_tree.json", "w") as file:
            file.write(json.dumps(parse_tree.jsonify(), indent=3))
