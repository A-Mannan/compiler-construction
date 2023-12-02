from parser.tree import TreeNode
from lexer.token import Token
from lexer.token_type import TokenType as tt
from semantics.symbol_table_manager import SymbolTableManager
from semantics.utils import (
    DefinitionTableEntry,
    ScopeTableEntry,
    MemberTableEntry,
    TypeInfo,
    TypeCheckingInfo,
)
from typing import List, Union


class Parser:
    def __init__(self, tokens) -> None:
        self.tokens: List[Token] = tokens
        self.curr_index = 0
        self.parse_tree: Union[TreeNode, None] = None
        self.st_manager = SymbolTableManager()

    @property
    def curr_token(self) -> Token:
        return self.tokens[self.curr_index]

    def advance(self):
        self.curr_index += 1

    def display_error(self, msg):
        print(
            f"Syntax error at line# {self.curr_token.line_number} :\n  error parsing '{self.curr_token.value}', {msg}"
        )
        print("-" * 70)

    def display_semantic_error(self, msg, show_line_num=True):
        print(
            f"Semantic error {f'at line# {self.curr_token.line_number}' if show_line_num else ''} :\n  {msg}"
        )
        print("-" * 70)

    def parse(self):
        # try:
        node = self.parse_program()
        # if node is not None:
        self.parse_tree = node

        if self.curr_token.token_type != tt.EOF_MARKER:
            print("All tokens were not parsed !!!")

        self.st_manager.print_def_table()
        print()
        self.st_manager.print_all_member_tables()
        print()
        self.st_manager.print_scope_table()
        return self.parse_tree
        # except:
        #     ...

    def parse_program(self):
        node = TreeNode("program")
        if self.curr_token.token_type in {
            tt.ACCESS_MODIFIER,
            tt.CLASS,
            tt.STRUCT,
            tt.INTERFACE,
            tt.EOF_MARKER,
        }:
            child = self.parse_class_int_struct_def_list()
            if child is None:
                return
            node.add_child(child)

            if not self.st_manager.is_main_found:
                self.display_semantic_error("No main method found", show_line_num=False)

            return node

        self.display_error("expected a class, struct or interface declaration")
        # self.advance()
        # return TreeNode("error")

    def parse_class_int_struct_def_list(self):
        node = TreeNode("class_int_struct_def_list")

        if self.curr_token.token_type in {
            tt.ACCESS_MODIFIER,
            tt.CLASS,
            tt.STRUCT,
            tt.INTERFACE,
        }:
            child = self.parse_class_int_struct_def()
            if child is None:
                return
            node.add_child(child)

            child = self.parse_class_int_struct_def_list()
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.EOF_MARKER}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected a class, struct or interface declaration")
        # self.advance()
        # return TreeNode("error")

    def parse_class_int_struct_def(self):
        node = TreeNode("class_int_struct_def")

        def_table_entry = DefinitionTableEntry()

        if self.curr_token.token_type in {
            tt.ACCESS_MODIFIER,
            tt.CLASS,
            tt.STRUCT,
            tt.INTERFACE,
        }:
            child = self.parse_access_mod_optional(def_table_entry)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_class_int_struct_def_2(def_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected a class, struct or interface declaration")
        # self.advance()
        # return TreeNode("error")

    def parse_access_mod_optional(
        self, table_entry: DefinitionTableEntry | MemberTableEntry
    ):
        node = TreeNode("access_mod_optional")
        if self.curr_token.token_type == tt.ACCESS_MODIFIER:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            table_entry.access_modifier = self.curr_token.value
            self.advance()
            return node

        elif self.curr_token.token_type in {
            tt.CLASS,
            tt.STRUCT,
            tt.INTERFACE,
            tt.STATIC,
            tt.DATA_TYPE,
            tt.VOID_TYPE,
            tt.IDENTIFIER,
            tt.DECLARE,
        }:
            node.add_child(TreeNode("null"))
            table_entry.access_modifier = "public"
            return node

        self.display_error(
            "expected a class, struct or interface declaration or member declaration"
        )
        # self.advance()
        # return TreeNode("error")

    def parse_class_int_struct_def_2(self, def_table_entry: DefinitionTableEntry):
        node = TreeNode("class_int_struct_def_2")
        if self.curr_token.token_type in {tt.CLASS}:
            child = self.parse_class_def(def_table_entry)
            if child is None:
                return
            node.add_child(child)
            return node

        elif self.curr_token.token_type in {tt.STRUCT}:
            child = self.parse_struct_def(def_table_entry)
            if child is None:
                return
            node.add_child(child)
            return node

        elif self.curr_token.token_type in {tt.INTERFACE}:
            child = self.parse_interface_def(def_table_entry)
            if child is None:
                return
            node.add_child(child)
            return node

        self.display_error("expected 'class' , 'struct' or 'interface' keyword")
        # self.advance()
        # return TreeNode("error")

    def parse_class_def(self, def_table_entry: DefinitionTableEntry):
        node = TreeNode("class_def")

        if self.curr_token.token_type == tt.CLASS:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            def_table_entry.type = "class"
            self.advance()
        else:
            self.display_error("expected a 'class' keyword")
            # self.advance()
            # return TreeNode("error")
            return

        if self.curr_token.token_type == tt.IDENTIFIER:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            def_table_entry.name = self.curr_token.value
            self.advance()
        else:
            self.display_error("expected an identifier")
            # self.advance()
            # return TreeNode("error")
            return

        child = self.parse_inherit_implement(def_table_entry)
        if child is None:
            return
        node.add_child(child)

        if not self.st_manager.insert_into_definition_table(def_table_entry):
            self.display_semantic_error(f"Definition Redeclaration error")
            return
        self.st_manager.current_def_name = def_table_entry.name

        child = self.parse_class_struct_body()
        if child is None:
            return
        node.add_child(child)

        implements_interface, interface_name = self.st_manager.check_implements_interface()
        if not implements_interface:
            self.display_semantic_error(f"{self.st_manager.current_def_name} does not implements {interface_name} completely")
            return

        if not self.st_manager.check_constructor_exist():
            member_table_entry = MemberTableEntry()
            member_table_entry.name = "constructor"
            member_table_entry.type.is_function = True
            member_table_entry.type.func_return_type = None
            member_table_entry.access_modifier = "public"
            member_table_entry.type.func_param_type_list = []
            self.st_manager.insert_into_member_table(member_table_entry)

        self.st_manager.current_def_name = None

        return node

    def parse_struct_def(self, def_table_entry):
        node = TreeNode("struct_def")
        if self.curr_token.token_type == tt.STRUCT:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            def_table_entry.type = "struct"
            self.advance()
        else:
            self.display_error("expected a 'struct' or keyword")
            # self.advance()
            # return TreeNode("error")
            return

        if self.curr_token.token_type == tt.IDENTIFIER:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            def_table_entry.name = self.curr_token.value
            self.advance()
        else:
            self.display_error("expected an identifier")
            # self.advance()
            # return TreeNode("error")
            return

        child = self.parse_inherit_implement(def_table_entry)
        if child is None:
            return
        node.add_child(child)

        if not self.st_manager.insert_into_definition_table(def_table_entry):
            self.display_semantic_error(f"Definition Redeclaration error")
            return

        self.st_manager.current_def_name = def_table_entry.name

        child = self.parse_class_struct_body()
        if child is None:
            return
        node.add_child(child)

        implements_interface, interface_name = self.st_manager.check_implements_interface()
        if not implements_interface:
            self.display_semantic_error(f"{self.st_manager.current_def_name} does not implements {interface_name} completely")
            return

        if not self.st_manager.check_constructor_exist():
            member_table_entry = MemberTableEntry()
            member_table_entry.name = "constructor"
            member_table_entry.type.is_function = True
            member_table_entry.type.func_return_type = None
            member_table_entry.access_modifier = "public"
            member_table_entry.type.func_param_type_list = []
            self.st_manager.insert_into_member_table(member_table_entry)

        self.st_manager.current_def_name = None

        return node

    def parse_interface_def(self, def_table_entry):
        node = TreeNode("interface_def")
        if self.curr_token.token_type == tt.INTERFACE:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            def_table_entry.type = "interface"
            self.advance()
        else:
            self.display_error("expected 'interface' keyword")
            # self.advance()
            # return TreeNode("error")
            return

        if self.curr_token.token_type == tt.IDENTIFIER:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            def_table_entry.name = self.curr_token.value
            self.advance()
        else:
            self.display_error("expected an identifier")
            # self.advance()
            # return TreeNode("error")
            return

        child = self.parse_inherit(def_table_entry)
        if child is None:
            return
        node.add_child(child)

        if not self.st_manager.insert_into_definition_table(def_table_entry):
            self.display_semantic_error(f"Definition Redeclaration error")
            return

        self.st_manager.current_def_name = def_table_entry.name

        child = self.parse_interface_body()
        if child is None:
            return
        node.add_child(child)

        self.st_manager.current_def_name = None

        return node

    def parse_inherit_implement(self, def_table_entry: DefinitionTableEntry):
        node = TreeNode("inherit_implement")
        if self.curr_token.token_type in {
            tt.INHERITS,
            tt.IMPLEMENTS,
            tt.CURLY_BRACKET_OPEN,
        }:
            child = self.parse_inherit(def_table_entry)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_implement(def_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected 'inherits' or 'implements' or '{'")
        # self.advance()
        # return TreeNode("error")

    def parse_inherit(self, def_table_entry: DefinitionTableEntry):
        node = TreeNode("inherit")
        if self.curr_token.token_type == tt.INHERITS:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(
                    self.curr_token.token_type.name,
                )
                node.add_child(child)

                parent_class_name = self.curr_token.value
                parent_class_def_table = self.st_manager.lookup_definition_table(
                    parent_class_name
                )
                if parent_class_def_table is None:
                    self.display_semantic_error(
                        f"Parent class {parent_class_name} is undeclared"
                    )
                    return
                
                if parent_class_def_table.access_modifier == "private":
                    self.display_semantic_error(f"cannot inherit from a private (class/struct/interface)")
                    return
                
                if parent_class_def_table.type != def_table_entry.type:
                    self.display_semantic_error(f"{def_table_entry.type} cannot inherit from {parent_class_def_table.type}")
                    return
                

                def_table_entry.parent_class = parent_class_name

                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        elif self.curr_token.token_type in {tt.CURLY_BRACKET_OPEN, tt.IMPLEMENTS}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected 'inherits' or 'implements' or '{'")
        # self.advance()
        # return TreeNode("error")

    def parse_implement(self, def_table_entry: DefinitionTableEntry):
        node = TreeNode("implement")
        if self.curr_token.token_type == tt.IMPLEMENTS:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                interface_name = self.curr_token.value
                interface_def_table = self.st_manager.lookup_definition_table(
                    interface_name
                )
                if interface_def_table is None:
                    self.display_semantic_error(
                        f"Interface {interface_name} is undeclared"
                    )
                    return
                if interface_def_table.type != "interface":
                    self.display_semantic_error(f"{interface_name} is not an interface")
                    return

                if interface_name in def_table_entry.interface_list:
                    self.display_semantic_error(
                        f"interface {interface_name} already implemented"
                    )
                    return

                def_table_entry.interface_list.append(interface_name)
                self.advance()

            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_implement_list(def_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.CURLY_BRACKET_OPEN}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected 'implements' or '{'")
        # self.advance()
        # return TreeNode("error")

    def parse_implement_list(self, def_table_entry: DefinitionTableEntry):
        node = TreeNode("implement")
        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                interface_name = self.curr_token.value
                interface_def_table = self.st_manager.lookup_definition_table(
                    interface_name
                )
                if interface_def_table is None:
                    self.display_semantic_error(
                        f"Interface {interface_name} is undeclared"
                    )
                    return
                if interface_def_table.type != "interface":
                    self.display_semantic_error(f"{interface_name} is not an interface")
                    return

                if interface_name in def_table_entry.interface_list:
                    self.display_semantic_error(
                        f"interface {interface_name} already implemented"
                    )
                    return

                def_table_entry.interface_list.append(interface_name)
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_implement_list(def_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.CURLY_BRACKET_OPEN}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected ',' or '{'")
        # self.advance()
        # return TreeNode("error")

    def parse_class_struct_body(self):
        node = TreeNode("class_struct_body")
        if self.curr_token.token_type == tt.CURLY_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_class_struct_members()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.CURLY_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '}'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        self.display_error("expected '{'")
        # self.advance()
        # return TreeNode("error")

    def parse_class_struct_members(self):
        node = TreeNode("class_struct_members")
        if self.curr_token.token_type in {
            tt.CONSTRUCTOR,
            tt.MAIN,
            tt.ACCESS_MODIFIER,
            tt.STATIC,
            tt.DATA_TYPE,
            tt.VOID_TYPE,
            tt.IDENTIFIER,
            tt.DECLARE,
        }:
            child = self.parse_class_struct_member()
            if child is None:
                return
            node.add_child(child)

            child = self.parse_class_struct_members()
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.CURLY_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected a class and struct member or '}'")
        # self.advance()
        # return TreeNode("error")

    def parse_class_struct_member(self):
        node = TreeNode("class_struct_member")
        member_table_entry = MemberTableEntry()
        if self.curr_token.token_type in {
            tt.ACCESS_MODIFIER,
            tt.STATIC,
            tt.DATA_TYPE,
            tt.VOID_TYPE,
            tt.IDENTIFIER,
            tt.DECLARE,
        }:
            child = self.parse_field_declaration_method_def(member_table_entry)
            if child is None:
                return
            node.add_child(child)
            return node

        elif self.curr_token.token_type in {tt.CONSTRUCTOR}:
            child = self.parse_constructor_def(member_table_entry)
            if child is None:
                return
            node.add_child(child)
            return node

        elif self.curr_token.token_type in {tt.MAIN}:
            if (
                self.st_manager.lookup_definition_table(
                    self.st_manager.current_def_name
                ).type
                != "class"
            ):
                self.display_semantic_error(
                    "Main method can only be declared inside class"
                )
                return
            if self.st_manager.is_main_found:
                self.display_semantic_error("Main method redeclaration")
                return
            self.st_manager.is_main_found = True
            child = self.parse_main_method(member_table_entry)
            if child is None:
                return
            node.add_child(child)
            return node

        self.display_error("expected a class and struct member")
        # self.advance()
        # return TreeNode("error")

    def parse_field_declaration_method_def(self, member_table_entry: MemberTableEntry):
        node = TreeNode("field_declaration_method_def")
        if self.curr_token.token_type in {
            tt.ACCESS_MODIFIER,
            tt.STATIC,
            tt.DATA_TYPE,
            tt.VOID_TYPE,
            tt.IDENTIFIER,
            tt.DECLARE,
        }:
            child = self.parse_access_mod_optional(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_static_optional(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_field_declaration_method_def_2(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected a field declaration or method definition")
        # self.advance()
        # return TreeNode("error")

    def parse_field_declaration_method_def_2(
        self, member_table_entry: MemberTableEntry
    ):
        node = TreeNode("field_declaration_method_def_2")
        if self.curr_token.token_type in {tt.DECLARE}:
            child = self.parse_variable_declaration(member_table_entry, is_member=True)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        elif self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER, tt.VOID_TYPE}:
            child = self.parse_function_def(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected a field declaration or method definition")
        # self.advance()
        # return TreeNode("error")

    def parse_static_optional(self, member_table_entry: MemberTableEntry):
        node = TreeNode("static_optional")
        if self.curr_token.token_type == tt.STATIC:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            member_table_entry.is_static = True
            self.advance()
            return node

        elif self.curr_token.token_type in {
            tt.DATA_TYPE,
            tt.VOID_TYPE,
            tt.IDENTIFIER,
            tt.DECLARE,
        }:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected a type or 'static' keyword")
        # self.advance()
        # return TreeNode("error")

    def parse_constructor_def(self, member_table_entry: MemberTableEntry):
        node = TreeNode("constructor_def")
        if self.curr_token.token_type == tt.CONSTRUCTOR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            member_table_entry.name = "constructor"
            member_table_entry.type.is_function = True
            member_table_entry.type.func_return_type = None
            self.st_manager.curr_func_return_type = None
            member_table_entry.access_modifier = "public"
            self.advance()

            if self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.st_manager.create_scope()
                self.advance()
            else:
                self.display_error("expected '('")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_parameter_list(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            if not self.st_manager.insert_into_member_table(member_table_entry):
                self.display_semantic_error("Redeclaration error")
                return

            if self.curr_token.token_type == tt.CURLY_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '{'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_multiple_statements()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.CURLY_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '}'")
                # self.advance()
                # return TreeNode("error")
                return

            self.st_manager.destroy_scope()

            return node

        self.display_error("expected a 'constructor' function")
        # self.advance()
        # return TreeNode("error")

    def parse_main_method(self, member_table_entry: MemberTableEntry):
        node = TreeNode("constructor_def")
        if self.curr_token.token_type == tt.MAIN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            member_table_entry.name = "mainEntry"
            member_table_entry.type.is_function = True
            member_table_entry.type.func_return_type = None
            self.st_manager.curr_func_return_type = None
            member_table_entry.access_modifier = "public"
            self.advance()

            if self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.st_manager.create_scope()
                self.advance()
            else:
                self.display_error("expected '('")
                # self.advance()
                # return TreeNode("error")
                return

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            if not self.st_manager.insert_into_member_table(member_table_entry):
                self.display_semantic_error("Redeclaration error")
                return

            if self.curr_token.token_type == tt.CURLY_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '{'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_multiple_statements()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.CURLY_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '}'")
                # self.advance()
                # return TreeNode("error")
                return

            self.st_manager.destroy_scope()

            return node

        self.display_error("expected main method")
        # self.advance()
        # return TreeNode("error")

    def parse_function_def(self, member_table_entry: MemberTableEntry):
        node = TreeNode("function_def")
        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER, tt.VOID_TYPE}:
            child = self.parse_function_declaration(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.CURLY_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '{'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_multiple_statements()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.CURLY_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '}'")
                # self.advance()
                # return TreeNode("error")
                return

            self.st_manager.curr_func_return_type = None
            self.st_manager.destroy_scope()

            return node

        self.display_error("expected method return type")
        # self.advance()
        # return TreeNode("error")

    def parse_function_declaration(self, member_table_entry: MemberTableEntry):
        node = TreeNode("function_declaration")

        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER, tt.VOID_TYPE}:
            type = TypeInfo()
            child = self.parse_return_type(type)
            if child is None:
                return
            node.add_child(child)
            member_table_entry.type.is_function = True
            member_table_entry.type.func_return_type = type

            self.st_manager.curr_func_return_type = type

            if self.curr_token.token_type == tt.FUNCTION:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected 'function' keyword")
                # self.advance()
                # return TreeNode("error")
                return

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                member_table_entry.name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            if self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.st_manager.create_scope()
                self.advance()
            else:
                self.display_error("expected '('")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_parameter_list(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            if not self.st_manager.insert_into_member_table(member_table_entry):
                self.display_semantic_error("Redeclaration error")
                return

            return node

        self.display_error("expected method return type")
        # self.advance()
        # return TreeNode("error")

    def parse_parameter_list(self, member_table_entry: MemberTableEntry):
        node = TreeNode("parameter_list")
        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER}:
            child = self.parse_parameter(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_parameter_list_2(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.ROUND_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected a variable type or ')'")
        # self.advance()
        # return TreeNode("error")

    def parse_parameter(self, member_table_entry: MemberTableEntry):
        node = TreeNode("parameter")
        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER}:
            scope_table_entry = ScopeTableEntry()
            type = TypeInfo()
            child = self.parse_type(type)
            if child is None:
                return
            node.add_child(child)
            scope_table_entry.type = type
            member_table_entry.type.func_param_type_list.append(type)

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                scope_table_entry.name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            if not self.st_manager.insert_into_scope_table(scope_table_entry):
                self.display_semantic_error("Redeclaration error")
                return

            return node

        self.display_error("expected a variable type or ')'")
        # self.advance()
        # return TreeNode("error")

    def parse_parameter_list_2(self, member_table_entry: MemberTableEntry):
        node = TreeNode("parameter_list_2")
        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_parameter(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_parameter_list_2(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.ROUND_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected ',' or ')'")
        # self.advance()
        # return TreeNode("error")

    def parse_interface_body(self):
        node = TreeNode("interface_body")
        if self.curr_token.token_type == tt.CURLY_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_interface_members()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.CURLY_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '}'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        self.display_error("expected '{'")
        # self.advance()
        # return TreeNode("error")

    def parse_interface_members(self):
        node = TreeNode("interface_members")

        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER, tt.VOID_TYPE}:
            child = self.parse_interface_member()
            if child is None:
                return
            node.add_child(child)

            child = self.parse_interface_members()
            if child is None:
                return
            node.add_child(child)

            return node
        elif self.curr_token.token_type in {tt.CURLY_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected a type or '}'")
        # self.advance()
        # return TreeNode("error")

    def parse_interface_member(self):
        node = TreeNode("interface_member")
        member_table_entry = MemberTableEntry()
        member_table_entry.access_modifier = None
        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER, tt.VOID_TYPE}:
            child = self.parse_function_declaration(member_table_entry)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        self.st_manager.destroy_scope()

        self.display_error("expected a type")
        # self.advance()
        # return TreeNode("error")

    def parse_multiple_statements(self):
        node = TreeNode("multiple_statements")
        if self.curr_token.token_type in {
            tt.BR_CONT,
            tt.RETURN,
            tt.FOR,
            tt.WHILE,
            tt.IF,
            tt.DECLARE,
            tt.IDENTIFIER,
            tt.THIS,
            tt.SUPER,
            tt.POINTER_MULTIPLY,
            tt.CALL,
        }:
            child = self.parse_statement()
            if child is None:
                return
            node.add_child(child)

            child = self.parse_multiple_statements()
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.CURLY_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected a valid statement")
        # self.advance()
        # return TreeNode("error")

    def parse_statement(self):
        node = TreeNode("statement")
        if self.curr_token.token_type == tt.BR_CONT:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            if not self.st_manager.check_inside_loop():
                self.display_semantic_error(
                    "break or continue can only be used inside loop"
                )
                return
            self.advance()

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        elif self.curr_token.token_type in {tt.RETURN}:
            child = self.parse_return_statement()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        elif self.curr_token.token_type in {tt.IF}:
            child = self.parse_if_else_statement()
            if child is None:
                return
            node.add_child(child)

            return node
        elif self.curr_token.token_type in {tt.WHILE}:
            child = self.parse_while_statement()
            if child is None:
                return
            node.add_child(child)

            return node
        elif self.curr_token.token_type in {tt.FOR}:
            child = self.parse_for_loop_statement()
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.DECLARE}:
            child = self.parse_variable_declaration()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            return node
        elif self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.POINTER_MULTIPLY,
        }:
            child = self.parse_assignment_statement()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        self.display_error("expected a valid statement")
        # self.advance()
        # return TreeNode("error")

    def parse_return_statement(self):
        node = TreeNode("return_statement")
        if self.curr_token.token_type == tt.RETURN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_return_statement_2()
            if child is None:
                return
            node.add_child(child)

            return node
        self.display_error("expected 'return' keyword")
        # self.advance()
        # return TreeNode("error")

    def parse_return_statement_2(self):
        node = TreeNode("return_statement_2")
        if self.curr_token.token_type in {
            tt.REF_OPERATOR,
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
            tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_value()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if (
                self.st_manager.curr_func_return_type is None
                or self.st_manager.curr_func_return_type.data_type == "void"
            ):
                self.display_semantic_error("the function must not return a value")
                return
            if (
                self.st_manager.check_compatibility_binary_op(
                    self.st_manager.curr_func_return_type, result_type, "="
                )
                is None
            ):
                self.display_semantic_error(
                    f"function can not return {result_type} and can only return {self.st_manager.curr_func_return_type}"
                )
                return

            return node
        elif self.curr_token.token_type in {tt.SEMICOLON}:
            node.add_child(TreeNode("null"))

            if (
                self.st_manager.curr_func_return_type is not None
                and self.st_manager.curr_func_return_type.data_type != "void"
            ):
                self.display_semantic_error(
                    f"the function must return {self.st_manager.curr_func_return_type}"
                )
                return

            return node

        self.display_error("expected a valid value to return")
        # self.advance()
        # return TreeNode("error")

    def parse_value(self):
        node = TreeNode("value")
        if self.curr_token.token_type in {tt.REF_OPERATOR}:
            child = self.parse_pointer_initialization()
            if child is None:
                return
            child, type = child
            node.add_child(child)
            return node, type

        elif self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            # tt.OBJ_CREATOR,
            # tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_OPEN}:
            child = self.parse_array_initialization()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type

        elif self.curr_token.token_type in {tt.OBJ_CREATOR}:
            child = self.parse_object_creation()
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type

        self.display_error("expected a valid value (an expression or pointer init or object)")
        # self.advance()
        # return TreeNode("error")

    def parse_variable_declaration(
        self, table_entry: MemberTableEntry | ScopeTableEntry = None, is_member=False
    ):
        node = TreeNode("variable_declaration")
        if table_entry is None:
            table_entry = ScopeTableEntry()
        if self.curr_token.token_type == tt.DECLARE:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            type = TypeInfo()
            child = self.parse_type(type)
            if child is None:
                return
            node.add_child(child)

            if is_member:
                table_entry.type.var_type = type
            else:
                table_entry.type = type

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                table_entry.name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            if is_member:
                if not self.st_manager.insert_into_member_table(table_entry):
                    self.display_semantic_error("Redeclaration error")
                    return
            else:
                if not self.st_manager.insert_into_scope_table(table_entry):
                    self.display_semantic_error("Redeclaration error")
                    return

            child = self.parse_init(type)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_list(table_entry, is_member)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected 'declare' keyword for variable declaration")
        # self.advance()
        # return TreeNode("error")

    def parse_init(self, left_operand_type: TypeInfo):
        node = TreeNode("init")
        if self.curr_token.token_type == tt.ASSIGNMENT_OPERATOR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_value()
            if child is None:
                return
            child, right_operand_type = child
            node.add_child(child)

            if (
                self.st_manager.check_compatibility_binary_op(
                    left_operand_type, right_operand_type, "="
                )
                is None
            ):
                self.display_semantic_error(
                    f"unable to assign {right_operand_type} to variable of type {left_operand_type}"
                )
                return

            return node

        elif self.curr_token.token_type in {tt.COMMA, tt.SEMICOLON}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected '=' , ',' or ';'")
        # self.advance()
        # return TreeNode("error")

    def parse_list(
        self, prev_table_entry: MemberTableEntry | ScopeTableEntry, is_member: bool
    ):
        node = TreeNode("list")

        if is_member:
            table_entry = MemberTableEntry()
            table_entry.type = prev_table_entry.type
            table_entry.access_modifier = prev_table_entry.access_modifier
            table_entry.is_static = prev_table_entry.is_static
        else:
            table_entry = ScopeTableEntry()
            table_entry.type = prev_table_entry.type

        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                table_entry.name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            if is_member:
                if not self.st_manager.insert_into_member_table(table_entry):
                    self.display_semantic_error("Redeclaration error")
                    return
            else:
                if not self.st_manager.insert_into_scope_table(table_entry):
                    self.display_semantic_error("Redeclaration error")
                    return

            child = self.parse_init()
            if child is None:
                return
            node.add_child(child)

            child = self.parse_list(prev_table_entry, is_member)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SEMICOLON}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected ',' or ';'")
        # self.advance()
        # return TreeNode("error")

    def parse_pointer_initialization(self):
        node = TreeNode("pointer_initialization")
        if self.curr_token.token_type == tt.REF_OPERATOR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            # if self.curr_token.token_type == tt.IDENTIFIER:
            #     child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            #     node.add_child(child)
            #     self.advance()
            # else:
            #     self.display_error("expected an identifier")
            #     # self.advance()
            #     # return TreeNode("error")
            #     return

            child = self.parse_function_call()
            if child is None:
                return
            child, operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_binary_op(
                operand_type, "&"
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator(&) for operand of type {operand_type}"
                )
                return

            return node, result_type

        self.display_error("expected reference operator '&'")
        # self.advance()
        # return TreeNode("error")

    def parse_if_else_statement(self):
        node = TreeNode("if_else_statement")
        if self.curr_token.token_type == tt.IF:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '('")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.data_type != "bool":
                self.display_semantic_error("expression should return a bool value")

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            self.st_manager.create_scope()

            child = self.parse_body()
            if child is None:
                return
            node.add_child(child)

            self.st_manager.destroy_scope()

            child = self.parse_else()
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected 'if' keyword")
        # self.advance()
        # return TreeNode("error")

    def parse_else(self):
        node = TreeNode("else")
        if self.curr_token.token_type == tt.ELSE:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            self.st_manager.create_scope()

            child = self.parse_body()
            if child is None:
                return
            node.add_child(child)

            self.st_manager.destroy_scope()

            return node

        elif self.curr_token.token_type in {
            tt.BR_CONT,
            tt.RETURN,
            tt.FOR,
            tt.WHILE,
            tt.IF,
            tt.DECLARE,
            tt.IDENTIFIER,
            tt.THIS,
            tt.SUPER,
            tt.POINTER_MULTIPLY,
            tt.CURLY_BRACKET_CLOSE,
        }:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected 'else' keyword or a statement")
        # self.advance()
        # return TreeNode("error")

    def parse_body(self):
        node = TreeNode("body")
        if self.curr_token.token_type in {
            tt.BR_CONT,
            tt.RETURN,
            tt.FOR,
            tt.WHILE,
            tt.IF,
            tt.DECLARE,
            tt.IDENTIFIER,
            tt.THIS,
            tt.SUPER,
            tt.POINTER_MULTIPLY,
        }:
            child = self.parse_statement()
            if child is None:
                return
            node.add_child(child)

            return node
        elif self.curr_token.token_type == tt.CURLY_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_multiple_statements()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.CURLY_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '}'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        self.display_error("expected a statement or '{'")
        # self.advance()
        # return TreeNode("error")

    def parse_for_loop_statement(self):
        node = TreeNode("for_loop_statement")
        if self.curr_token.token_type == tt.FOR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '('")
                # self.advance()
                # return TreeNode("error")
                return

            self.st_manager.create_scope(is_loop=True)

            child = self.parse_c1()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_c2()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SEMICOLON:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ';'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_c3()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_body()
            if child is None:
                return
            node.add_child(child)

            self.st_manager.destroy_scope()

            return node

        self.display_error("expected 'for' keyword")
        # self.advance()
        # return TreeNode("error")

    def parse_c1(self):
        node = TreeNode("c1")
        if self.curr_token.token_type in {tt.DECLARE}:
            child = self.parse_variable_declaration()
            if child is None:
                return
            node.add_child(child)

            return node
        elif self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.POINTER_MULTIPLY,
        }:
            child = self.parse_assignment_statement()
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected a variable declaration or assignment")
        # self.advance()
        # return TreeNode("error")

    def parse_c2(self):
        node = TreeNode("c2")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            # tt.OBJ_CREATOR,
            # tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.data_type != "bool":
                self.display_semantic_error("expression should return a bool value")

            return node

        self.display_error("expected an expression")
        # self.advance()
        # return TreeNode("error")

    def parse_c3(self):
        node = TreeNode("c3")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.POINTER_MULTIPLY,
        }:
            child = self.parse_assignment_statement()
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected an assignment statement")
        # self.advance()
        # return TreeNode("error")

    def parse_while_statement(self):
        node = TreeNode("while_statement")
        if self.curr_token.token_type == tt.WHILE:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '('")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.data_type != "bool":
                self.display_semantic_error("expression should return a bool value")

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            self.st_manager.create_scope(is_loop=True)

            child = self.parse_body()
            if child is None:
                return
            node.add_child(child)

            self.st_manager.destroy_scope()

            return node

        self.display_error("expected 'while' keyword")
        # self.advance()
        # return TreeNode("error")

    def parse_assignment_statement(self):
        node = TreeNode("assignment_statement")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.POINTER_MULTIPLY,
        }:
            is_pointer = False
            if self.curr_token.token_type == tt.POINTER_MULTIPLY:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                is_pointer = True
                self.advance()

            child = self.parse_this_super_optional()
            if child is None:
                return
            child, ref_type = child
            node.add_child(child)

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            class_name = None
            if ref_type == "this":
                class_name = self.st_manager.current_def_name
            elif ref_type == "super":
                class_name = self.st_manager.lookup_definition_table(
                    self.st_manager.current_def_name
                ).parent_class
                if class_name is None:
                    self.display_semantic_error("No parent class exists")
                    return

            child = self.parse_assignment_statement_2(name, class_name, is_pointer)
            if child is None:
                return
            node.add_child(child)

            # child = self.parse_assignment()
            # if child is None:
            #     return
            # node.add_child(child)

            return node

        self.display_error("expected 'this', 'super' or an identifier")
        # self.advance()
        # return TreeNode("error")

    def parse_assignment_statement_2(
        self, name, class_name, is_pointer, is_static = False
    ):
        node = TreeNode("assignment_statement_2")
        if self.curr_token.token_type in {tt.DOT, tt.ARROW}:
            static_class_name = None
            if class_name is None:
                var_type = self.st_manager.lookup_scope_table(name)
                if var_type is None:
                    def_table_entry = self.st_manager.lookup_definition_table(name)
                    if def_table_entry is None:
                        self.display_semantic_error(f"Undeclared variable {name}")
                        return
                    is_static = True
                    static_class_name = name
                    var_type = TypeInfo()

            elif class_name in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error(
                    "cannot use '.' or '->' with primitive datatypes"
                )
                return
            elif class_name == "void":
                self.display_semantic_error("method has a void return type")
                return
            else:
                member_table_entry = self.st_manager.lookup_member_table(
                    name, class_name
                )
                if member_table_entry is None:
                    self.display_semantic_error(
                        f"Undeclared variable {name} in '{self.st_manager.current_def_name}'"
                    )
                    return
                if member_table_entry.type.is_function:
                    self.display_semantic_error(f"{name} is a function not a variable")
                    return
                if member_table_entry.access_modifier == "private" and self.st_manager.current_def_name != class_name:
                    self.display_semantic_error("cannot access private member")
                    return

                if member_table_entry.access_modifier == "protected":
                    curr_parent_class = self.st_manager.lookup_definition_table(self.st_manager.current_def_name).parent_class
                    if self.st_manager.current_def_name != class_name and curr_parent_class != class_name:
                        self.display_semantic_error("protected members can only be accessed inside own (class/struct) and child (class/struct)")
                        return

                if member_table_entry.is_static and not is_static:
                    self.display_semantic_error(f"{name} is a static class variable")
                    return

                if not member_table_entry.is_static and is_static:
                    self.display_semantic_error(f"{name} is not a static class variable")
                    return

                is_static = False
                var_type = member_table_entry.type.var_type

            child = self.parse_dot_arrow(var_type, is_static)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            class_name = static_class_name if is_static else var_type.data_type
            child = self.parse_assignment_statement_2(name, class_name, is_pointer, is_static)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_OPEN}:
            if class_name is None:
                var_type = self.st_manager.lookup_scope_table(name)
                if var_type is None:
                    self.display_semantic_error(f"Undeclared variable {name}")
                    return
            elif class_name in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error("cannot subscript primitive datatypes")
                return
            elif class_name == "void":
                self.display_semantic_error("method has a void return type")
                return
            else:
                member_table_entry = self.st_manager.lookup_member_table(
                    name, class_name
                )
                if member_table_entry is None:
                    self.display_semantic_error(
                        f"Undeclared variable {name} in parent of {self.st_manager.current_def_name}"
                    )
                    return
                if member_table_entry.type.is_function:
                    self.display_semantic_error(f"{name} is a function not a variable")
                    return
                if member_table_entry.access_modifier == "private" and self.st_manager.current_def_name != class_name:
                    self.display_semantic_error("cannot access private member")
                    return

                if member_table_entry.access_modifier == "protected":
                    curr_parent_class = self.st_manager.lookup_definition_table(self.st_manager.current_def_name).parent_class
                    if self.st_manager.current_def_name != class_name and curr_parent_class != class_name:
                        self.display_semantic_error("protected members can only be accessed inside own (class/struct) and child (class/struct)")
                        return

                if member_table_entry.is_static and not is_static:
                    self.display_semantic_error(f"{name} is a static class variable")
                    return

                if not member_table_entry.is_static and is_static:
                    self.display_semantic_error(f"{name} is not a static class variable")
                    return

                is_static = False
                var_type = member_table_entry.type.var_type

            if not var_type.is_array:
                self.display_semantic_error(f"{name} is not an array")
                return

            # child = self.parse_array_indexing_slicing()
            child = self.parse_array_indexing_1d(var_type)
            if child is None:
                return
            child, dimensions_indexed = child
            node.add_child(child)

            child = self.parse_assignment_statement_4(
                var_type, dimensions_indexed, is_pointer
            )
            if child is None:
                return
            node.add_child(child)

            return node
        elif self.curr_token.token_type in {tt.ROUND_BRACKET_OPEN}:
            param_type_list = []
            child = self.parse_func_args(param_type_list)
            if child is None:
                return
            node.add_child(child)

            if class_name is None:
                class_name = self.st_manager.current_def_name

            member_table_entry = self.st_manager.lookup_member_table_func(
                name, param_type_list, class_name
            )
            if member_table_entry is None:
                self.display_semantic_error("Undeclared method error")
                return

            child = self.parse_assignment_statement_3(
                member_table_entry.type.func_return_type, is_pointer
            )
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {
            tt.ASSIGNMENT_OPERATOR,
            tt.COMP_ASSIGNMENT_OPERATOR,
        }:

            if class_name is None:
                var_type = self.st_manager.lookup_scope_table(name)
                if var_type is None:
                    self.display_semantic_error(f"Undeclared variable {name}")
                    return
            elif class_name == "void":
                self.display_semantic_error("method has a void return type")
                return
            else:
                member_table_entry = self.st_manager.lookup_member_table(
                    name, class_name
                )
                if member_table_entry is None:
                    self.display_semantic_error(
                        f"Undeclared variable {name} in '{self.st_manager.current_def_name}'"
                    )
                    return
                if member_table_entry.type.is_function:
                    self.display_semantic_error(f"{name} is a function not a variable")
                    return
                if member_table_entry.access_modifier == "private" and self.st_manager.current_def_name != class_name:
                    self.display_semantic_error("cannot access private member")
                    return

                if member_table_entry.access_modifier == "protected":
                    curr_parent_class = self.st_manager.lookup_definition_table(self.st_manager.current_def_name).parent_class
                    if self.st_manager.current_def_name != class_name and curr_parent_class != class_name:
                        self.display_semantic_error("protected members can only be accessed inside own (class/struct) and child (class/struct)")
                        return

                if member_table_entry.is_static and not is_static:
                    self.display_semantic_error(f"{name} is a static class variable")
                    return

                if not member_table_entry.is_static and is_static:
                    self.display_semantic_error(f"{name} is not a static class variable")
                    return

                is_static = False
                var_type = member_table_entry.type.var_type

            if is_pointer:
                result_type = self.st_manager.check_compatibility_unirary_op(
                var_type, "*"
                )
                if result_type is None:
                    self.display_semantic_error(
                        f"Unsupported operator(*) for operand {var_type}"
                    )
                    return
            else:
                result_type = var_type

            child = self.parse_assignment(result_type)
            if child is None:
                return
            node.add_child(child)
            return node

        self.display_error(
            "expected '->', '.', '[', '(', '=' or a compound assignment "
        )
        # self.advance()
        # return TreeNode("error")

    def parse_assignment_statement_3(self, var_type: TypeInfo, is_pointer):
        node = TreeNode("assignment_statement_3")
        if self.curr_token.token_type in {tt.DOT, tt.ARROW}:
            child = self.parse_dot_arrow(var_type)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_assignment_statement_2(
                name, var_type.data_type, is_pointer
            )
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_OPEN}:
            if not var_type.is_array:
                self.display_semantic_error(f"function does not returns an array")
                return

            # child = self.parse_array_indexing_slicing()
            child = self.parse_array_indexing_1d(var_type)
            if child is None:
                return
            child, dimensions_indexed = child
            node.add_child(child)

            child = self.parse_assignment_statement_4(var_type, dimensions_indexed, is_pointer)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SEMICOLON}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected '->', '.' , '[' or ';'")
        # self.advance()
        # return TreeNode("error")

    def parse_assignment_statement_4(
        self, var_type: TypeInfo, dimensions_indexed, is_pointer
    ):
        node = TreeNode("assignment_statement_4")
        if self.curr_token.token_type in {tt.DOT}:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            if var_type.is_pointer:
                self.display_semantic_error("'.' cannot be used with pointer type")
                return
            if var_type.is_array and dimensions_indexed != var_type.dimensions:
                self.display_semantic_error("'.' cannot be used with array type")
                return
            if var_type.data_type in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error("cannot use '.' with primitive datatypes")
                return
            if var_type.data_type == "void":
                self.display_semantic_error("method has a void return type")
                return
            self.advance()

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            class_name = var_type.data_type
            child = self.parse_assignment_statement_2(name, class_name, is_pointer)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type

        elif self.curr_token.token_type in {
            tt.ASSIGNMENT_OPERATOR,
            tt.COMP_ASSIGNMENT_OPERATOR,
        }:
            # <assignment> here
            new_type = TypeInfo(var_type.data_type)
            new_type.dimensions = var_type.dimensions - dimensions_indexed
            node.add_child(TreeNode("null"))

            if is_pointer:
                result_type = self.st_manager.check_compatibility_unirary_op(
                new_type, "*"
                )
                if result_type is None:
                    self.display_semantic_error(
                        f"Unsupported operator(*) for operand {new_type}"
                    )
                    return
            else:
                result_type = new_type

            child = self.parse_assignment(result_type)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected '.', '=' or a compound assignment ")

    def parse_assignment(self, left_operand_type: TypeInfo):
        node = TreeNode("assignment")
        if self.curr_token.token_type in {
            tt.ASSIGNMENT_OPERATOR,
            tt.COMP_ASSIGNMENT_OPERATOR,
        }:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            operator = self.curr_token.value
            self.advance()

            child = self.parse_value()
            if child is None:
                return
            child, right_operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_binary_op(
                left_operand_type, right_operand_type, operator
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator({operator}) for operands of type {left_operand_type} and {right_operand_type}"
                )
                return

            return node

        self.display_error("expected '=' or a compound assignment operator")
        # self.advance()
        # return TreeNode("error")

    def parse_this_super_optional(self):
        node = TreeNode("this_super_optional")
        if self.curr_token.token_type == tt.THIS:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.ARROW:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '->'")
                # self.advance()
                # return TreeNode("error")
                return

            return node, "this"
        elif self.curr_token.token_type == tt.SUPER:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.ARROW:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected '->'")
                # self.advance()
                # return TreeNode("error")
                return

            return node, "super"
        elif self.curr_token.token_type in {tt.IDENTIFIER}:
            node.add_child(TreeNode("null"))
            return node, None

        self.display_error("expected 'this', 'super' or an identifier")
        # self.advance()
        # return TreeNode("error")

    def parse_dot_arrow(self, type: TypeInfo, is_static=False):
        node = TreeNode("dot_arrow")
        if self.curr_token.token_type == tt.DOT:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            if type.is_pointer:
                self.display_semantic_error("'.' cannot be used with pointer type")
                return
            if type.is_array:
                self.display_semantic_error("'.' cannot be used with array type")
                return
            if type.data_type in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error("cannot use '.' with primitive datatypes")
                return
            if type.data_type == "void":
                self.display_semantic_error("method has a void return type")
                return
            self.advance()

            return node
        elif self.curr_token.token_type == tt.ARROW:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            if is_static:
                self.display_semantic_error("static variables can only be accessed using (.) operator")
                return
            if not type.is_pointer:
                self.display_semantic_error("'->' can only be used with pointer type")
                return
            if type.is_array:
                self.display_semantic_error("'->' cannot be used with array type")
                return
            if type.data_type in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error("cannot use '->' with primitive datatypes")
                return
            if type.data_type == "void":
                self.display_semantic_error("method has a void return type")
                return
            self.advance()

            return node

        self.display_error("expected '->' or '.'")
        # self.advance()
        # return TreeNode("error")

    def parse_func_args(self, param_type_list: List):
        node = TreeNode("func_args")
        if self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_arguments(param_type_list)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        self.display_error("expected '('")
        # self.advance()
        # return TreeNode("error")

    def parse_arguments(self, param_type_list: List):
        node = TreeNode("arguments")
        if self.curr_token.token_type in {
            tt.REF_OPERATOR,
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
            tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_value()
            if child is None:
                return
            child, param_type = child
            node.add_child(child)

            param_type_list.append(param_type)

            child = self.parse_argument_list(param_type_list)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.ROUND_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected a value or expression or ')'")
        # self.advance()
        # return TreeNode("error")

    def parse_argument_list(self, param_type_list: List):
        node = TreeNode("arguments_list")
        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_value()
            if child is None:
                return
            child, param_type = child
            node.add_child(child)

            param_type_list.append(param_type)

            child = self.parse_argument_list(param_type_list)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.ROUND_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected ',' or ')'")
        # self.advance()
        # return TreeNode("error")

    def parse_array_indexing_slicing(self):
        node = TreeNode("array_indexing_slicing")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.data_type != "int":
                self.display_semantic_error("Array can only be indexed by an integer")
                return

            # child = self.parse_array_slicing()
            # if child is None:
            #     return
            # node.add_child(child)

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        self.display_error("expected '['")
        # self.advance()
        # return TreeNode("error")

    def parse_array_slicing(self):
        node = TreeNode("array_slicing")
        if self.curr_token.token_type == tt.COLON:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression()
            if child is None:
                return
            node.add_child(child)

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected ':' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_expression(self):
        node = TreeNode("expression")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            # tt.OBJ_CREATOR,
            # tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_or_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            # print(
            #     f"Result type of expression on line {self.curr_token.line_number}: ",
            #     result_type,
            # )

            return node, result_type

        self.display_error("expected an expression")
        # self.advance()
        # return TreeNode("error")

    def parse_or_expression(self):
        node = TreeNode("or-expression")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            # tt.OBJ_CREATOR,
            # tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_and_expression()
            if child is None:
                return
            child, left_operand_type = child
            node.add_child(child)

            child = self.parse_or_expression_2(left_operand_type)
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type

        self.display_error("expected an expression")
        # self.advance()
        # return TreeNode("error")

    def parse_or_expression_2(self, left_operand_type: TypeInfo):
        node = TreeNode("or_expression_2")
        if self.curr_token.token_type == tt.LOGICAL_OR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_and_expression()
            if child is None:
                return
            child, right_operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_binary_op(
                left_operand_type, right_operand_type, "||"
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator(||) for operands of type {left_operand_type} and {right_operand_type}"
                )
                return

            child = self.parse_or_expression_2(result_type)
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type

        elif self.curr_token.token_type in {
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
        }:
            node.add_child(TreeNode("null"))
            return node, left_operand_type

        self.display_error("expected '||' or expected OR expression to end")
        # self.advance()
        # return TreeNode("error")

    def parse_and_expression(self):
        node = TreeNode("and_expression")

        child = self.parse_relational_expression()
        if child is None:
            return
        child, left_operand_type = child
        node.add_child(child)

        child = self.parse_and_expression_2(left_operand_type)
        if child is None:
            return
        child, result_type = child
        node.add_child(child)

        return node, result_type

    def parse_and_expression_2(self, left_operand_type: TypeInfo):
        node = TreeNode("and_expression_2")
        if self.curr_token.token_type == tt.LOGICAL_AND:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_relational_expression()
            if child is None:
                return
            child, right_operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_binary_op(
                left_operand_type, right_operand_type, "&&"
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator(&&) for operands of type {left_operand_type} and {right_operand_type}"
                )
                return

            child = self.parse_and_expression_2(result_type)
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        elif self.curr_token.token_type in {
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
            tt.LOGICAL_OR,
        }:
            node.add_child(TreeNode("null"))
            return node, left_operand_type

        self.display_error("expected '&&' or expected AND expression to end")
        # self.advance()
        # return TreeNode("error")

    def parse_relational_expression(self):
        node = TreeNode("relational_expression")

        child = self.parse_plus_minus_exp()
        if child is None:
            return
        child, left_operand_type = child
        node.add_child(child)

        child = self.parse_relational_expression_2(left_operand_type)
        if child is None:
            return
        child, result_type = child
        node.add_child(child)

        return node, result_type

    def parse_relational_expression_2(self, left_operand_type: TypeInfo):
        node = TreeNode("relational_expression_2")
        if self.curr_token.token_type == tt.RELATIONAL_OPERATOR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            operator = self.curr_token.value
            self.advance()

            child = self.parse_plus_minus_exp()
            if child is None:
                return
            child, right_operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_binary_op(
                left_operand_type, right_operand_type, operator
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator({operator}) for operands of type {left_operand_type} and {right_operand_type}"
                )
                return

            child = self.parse_relational_expression_2(result_type)
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        elif self.curr_token.token_type in {
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
        }:
            node.add_child(TreeNode("null"))
            return node, left_operand_type

        self.display_error(
            "expected a rel. operator or expected relational expression to end"
        )
        # self.advance()
        # return TreeNode("error")

    def parse_plus_minus_exp(self):
        node = TreeNode("plus_minus_exp")

        child = self.parse_mul_div_mod_exp()
        if child is None:
            return
        child, left_operand_type = child
        node.add_child(child)

        child = self.parse_plus_minus_exp_2(left_operand_type)
        if child is None:
            return
        child, result_type = child
        node.add_child(child)

        return node, result_type

    def parse_plus_minus_exp_2(self, left_operand_type: TypeInfo):
        node = TreeNode("plus_minus_exp_2")
        if self.curr_token.token_type == tt.PLUS_MINUS:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            operator = self.curr_token.value
            self.advance()

            child = self.parse_mul_div_mod_exp()
            if child is None:
                return
            child, right_operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_binary_op(
                left_operand_type, right_operand_type, operator
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator({operator}) for operands of type {left_operand_type} and {right_operand_type}"
                )
                return

            child = self.parse_plus_minus_exp_2(result_type)
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        elif self.curr_token.token_type in {
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
            tt.RELATIONAL_OPERATOR,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
        }:
            node.add_child(TreeNode("null"))
            return node, left_operand_type

        self.display_error("expected '+', '-' or expected plus minus expression to end")
        # self.advance()
        # return TreeNode("error")

    def parse_mul_div_mod_exp(self):
        node = TreeNode("mul_div_mod_exp")

        child = self.parse_factor()
        if child is None:
            return
        child, left_operand_type = child
        node.add_child(child)

        child = self.parse_mul_div_mod_exp_2(left_operand_type)
        if child is None:
            return
        child, result_type = child
        node.add_child(child)

        return node, result_type

    def parse_mul_div_mod_exp_2(self, left_operand_type: TypeInfo):
        node = TreeNode("mul_div_mod_exp_2")
        if self.curr_token.token_type in {tt.POINTER_MULTIPLY, tt.DIVIDE_MODULUS}:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            operator = self.curr_token.value
            self.advance()

            child = self.parse_factor()
            if child is None:
                return
            child, right_operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_binary_op(
                left_operand_type, right_operand_type, operator
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator({operator}) for operands of type {left_operand_type} and {right_operand_type}"
                )
                return

            child = self.parse_mul_div_mod_exp_2(result_type)
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        elif self.curr_token.token_type in {
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
            tt.PLUS_MINUS,
            tt.RELATIONAL_OPERATOR,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
        }:
            node.add_child(TreeNode("null"))
            return node, left_operand_type

        self.display_error(
            "expected '*', '/', '%' or expected mul div mod expression to end"
        )
        # self.advance()
        # return TreeNode("error")

    def parse_factor(self):
        node = TreeNode("factor")
        if self.curr_token.token_type in {tt.THIS, tt.SUPER, tt.IDENTIFIER}:
            child = self.parse_function_call()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        elif self.curr_token.token_type in {
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.BOOL_LITERAL,
        }:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            if self.curr_token.token_type == tt.INTEGER_LITERAL:
                result_type = TypeInfo("int")
            elif self.curr_token.token_type == tt.FLOAT_LITERAL:
                result_type = TypeInfo("float")
            elif self.curr_token.token_type == tt.CHAR_LITERAL:
                result_type = TypeInfo("char")
            elif self.curr_token.token_type == tt.STRING_LITERAL:
                result_type = TypeInfo("string")
            else:
                result_type = TypeInfo("bool")
            self.advance()

            return node, result_type

        elif self.curr_token.token_type == tt.ROUND_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if self.curr_token.token_type == tt.ROUND_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ')'")
                # self.advance()
                # return TreeNode("error")
                return

            return node, result_type

        elif self.curr_token.token_type == tt.NOT_OPERATOR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_factor()
            if child is None:
                return
            child, operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_unirary_op(
                operand_type, "!"
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator(!) for operand {operand_type}"
                )
                return

            return node, result_type
        elif self.curr_token.token_type in {tt.POINTER_MULTIPLY}:
            child = self.parse_pointer_dereferencing()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        # elif self.curr_token.token_type in {tt.OBJ_CREATOR}:
        #     child = self.parse_object_creation()
        #     if child is None:
        #         return
        #     node.add_child(child)

        # return node
        # elif self.curr_token.token_type in {tt.SQUARE_BRACKET_OPEN}:
        #     child = self.parse_array_initialization()
        #     if child is None:
        #         return
        #     node.add_child(child)

        # return node

        self.display_error("expected a factor term")
        # self.advance()
        # return TreeNode("error")

    def parse_function_call(self):
        node = TreeNode("function_call")
        if self.curr_token.token_type in {tt.THIS, tt.SUPER, tt.IDENTIFIER}:
            child = self.parse_this_super_optional()
            if child is None:
                return
            child, ref_type = child
            node.add_child(child)

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return
            ref = None
            if ref_type == "this":
                ref = self.st_manager.current_def_name
                # table_entry = self.st_manager.lookup_member_table(name, self.st_manager.current_def_name)
                # if table_entry is None:
                #     self.display_semantic_error(f"Undeclared variable {name} in class {self.st_manager.current_def_name}")
                #     return
                # if table_entry.type.is_function:
                #     self.display_semantic_error(f"{name} is a function not a variable")
                #     return
                # type = table_entry.type.var_type
            elif ref_type == "super":
                ref = self.st_manager.lookup_definition_table(
                    self.st_manager.current_def_name
                ).parent_class
                if ref is None:
                    self.display_semantic_error("No parent class exists")
                    return
                # parent_class_name = self.st_manager.lookup_definition_table(self.st_manager.current_def_name).parent_class
                # table_entry = self.st_manager.lookup_member_table(name, parent_class_name)
                # if table_entry is None:
                #     self.display_semantic_error(f"Undeclared variable {name} in parent of {self.st_manager.current_def_name}")
                #     return
                # if table_entry.type.is_function:
                #     self.display_semantic_error(f"{name} is a function not a variable")
                #     return
                # type = table_entry.type.var_type
            # else:
            #     type = self.st_manager.lookup_scope_table(name)
            #     if type is None:
            #         self.display_semantic_error(f"Undeclared variable {name}")
            #         return

            child = self.parse_chaining(name, ref)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type

        self.display_error("expected 'this', 'super' or an identifier")
        # self.advance()
        # return TreeNode("error")

    def parse_chaining(self, name, class_name, is_static = False):
        node = TreeNode("chaining")
        if self.curr_token.token_type in {tt.DOT, tt.ARROW}:
            static_class_name = None
            if class_name is None:
                var_type = self.st_manager.lookup_scope_table(name)
                if var_type is None:
                    def_table_entry = self.st_manager.lookup_definition_table(name)
                    if def_table_entry is None:
                        self.display_semantic_error(f"Undeclared variable {name}")
                        return
                    is_static = True
                    static_class_name = name
                    var_type = TypeInfo()
                    
            elif class_name in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error(
                    "cannot use '.' or '->' with primitive datatypes"
                )
                return
            elif class_name == "void":
                self.display_semantic_error("method has a void return type")
                return
            else:
                member_table_entry = self.st_manager.lookup_member_table(
                    name, class_name
                )
                if member_table_entry is None:
                    self.display_semantic_error(
                        f"Undeclared variable {name} in '{self.st_manager.current_def_name}'"
                    )
                    return
                if member_table_entry.type.is_function:
                    self.display_semantic_error(f"{name} is a function not a variable")
                    return

                if member_table_entry.access_modifier == "private" and self.st_manager.current_def_name != class_name:
                    self.display_semantic_error("cannot access private member")
                    return

                if member_table_entry.access_modifier == "protected":
                    curr_parent_class = self.st_manager.lookup_definition_table(self.st_manager.current_def_name).parent_class
                    if self.st_manager.current_def_name != class_name and curr_parent_class != class_name:
                        self.display_semantic_error("protected members can only be accessed inside own (class/struct) and child (class/struct)")
                        return

                if member_table_entry.is_static and not is_static:
                    self.display_semantic_error(f"{name} is a static class variable")
                    return

                if not member_table_entry.is_static and is_static:
                    self.display_semantic_error(f"{name} is not a static class variable")
                    return

                is_static = False

                var_type = member_table_entry.type.var_type

            child = self.parse_dot_arrow(var_type, is_static)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            class_name = static_class_name if is_static else var_type.data_type
            child = self.parse_chaining(name, class_name, is_static)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_OPEN}:
            if class_name is None:
                var_type = self.st_manager.lookup_scope_table(name)
                if var_type is None:
                    self.display_semantic_error(f"Undeclared variable {name}")
                    return
            elif class_name in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error("cannot subscript primitive datatypes")
                return
            elif class_name == "void":
                self.display_semantic_error("method has a void return type")
                return
            else:
                member_table_entry = self.st_manager.lookup_member_table(
                    name, class_name
                )
                if member_table_entry is None:
                    self.display_semantic_error(
                        f"Undeclared variable {name} in parent of {self.st_manager.current_def_name}"
                    )
                    return
                if member_table_entry.type.is_function:
                    self.display_semantic_error(f"{name} is a function not a variable")
                    return

                if member_table_entry.access_modifier == "private" and self.st_manager.current_def_name != class_name:
                    self.display_semantic_error("cannot access private member")
                    return

                if member_table_entry.access_modifier == "protected":
                    curr_parent_class = self.st_manager.lookup_definition_table(self.st_manager.current_def_name).parent_class
                    if self.st_manager.current_def_name != class_name and curr_parent_class != class_name:
                        self.display_semantic_error("protected members can only be accessed inside own (class/struct) and child (class/struct)")
                        return

                if member_table_entry.is_static and not is_static:
                    self.display_semantic_error(f"{name} is a static class variable")
                    return

                if not member_table_entry.is_static and is_static:
                    self.display_semantic_error(f"{name} is not a static class variable")
                    return

                is_static = False
                
                var_type = member_table_entry.type.var_type

            if not var_type.is_array:
                self.display_semantic_error(f"{name} is not an array")
                return

            # child = self.parse_array_indexing_slicing()
            child = self.parse_array_indexing_1d(var_type)
            if child is None:
                return
            child, dimensions_indexed = child
            node.add_child(child)

            child = self.parse_chaining_3(var_type, dimensions_indexed)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type
        elif self.curr_token.token_type in {tt.ROUND_BRACKET_OPEN}:
            param_type_list = []
            child = self.parse_func_args(param_type_list)
            if child is None:
                return
            node.add_child(child)

            if class_name is None:
                class_name = self.st_manager.current_def_name

            member_table_entry = self.st_manager.lookup_member_table_func(
                name, param_type_list, class_name
            )
            if member_table_entry is None:
                self.display_semantic_error("Undeclared method error")
                return

            child = self.parse_chaining_2(member_table_entry.type.func_return_type)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type
        elif self.curr_token.token_type in {
            tt.POINTER_MULTIPLY,
            tt.DIVIDE_MODULUS,
            tt.PLUS_MINUS,
            tt.RELATIONAL_OPERATOR,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
        }:
            if class_name is None:
                var_type = self.st_manager.lookup_scope_table(name)
                if var_type is None:
                    self.display_semantic_error(f"Undeclared variable {name}")
                    return
            elif class_name == "void":
                self.display_semantic_error("method has a void return type")
                return
            else:
                member_table_entry = self.st_manager.lookup_member_table(
                    name, class_name
                )
                if member_table_entry is None:
                    self.display_semantic_error(
                        f"Undeclared variable {name} in '{self.st_manager.current_def_name}'"
                    )
                    return
                if member_table_entry.type.is_function:
                    self.display_semantic_error(f"{name} is a function not a variable")
                    return

                if member_table_entry.access_modifier == "private" and self.st_manager.current_def_name != class_name:
                    self.display_semantic_error("cannot access private member")
                    return

                if member_table_entry.access_modifier == "protected":
                    curr_parent_class = self.st_manager.lookup_definition_table(self.st_manager.current_def_name).parent_class
                    if self.st_manager.current_def_name != class_name and curr_parent_class != class_name:
                        self.display_semantic_error("protected members can only be accessed inside own (class/struct) and child (class/struct)")
                        return

                if member_table_entry.is_static and not is_static:
                    self.display_semantic_error(f"{name} is a static class variable")
                    return

                if not member_table_entry.is_static and is_static:
                    self.display_semantic_error(f"{name} is not a static class variable")
                    return

                is_static = False
                var_type = member_table_entry.type.var_type

            node.add_child(TreeNode("null"))
            return node, var_type

        self.display_error("expected '->', '.', '[', '(' or expected expression to end")
        # self.advance()
        # return TreeNode("error")

    def parse_chaining_2(self, var_type: TypeInfo):
        node = TreeNode("chaining_2")
        if self.curr_token.token_type in {tt.DOT, tt.ARROW}:
            child = self.parse_dot_arrow(var_type)
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_chaining(name, var_type.data_type)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_OPEN}:
            if not var_type.is_array:
                self.display_semantic_error(f"function does not returns an array")
                return

            # child = self.parse_array_indexing_slicing()
            child = self.parse_array_indexing_1d(var_type)
            if child is None:
                return
            child, dimensions_indexed = child
            node.add_child(child)

            child = self.parse_chaining_3(var_type, dimensions_indexed)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type

        elif self.curr_token.token_type in {
            tt.POINTER_MULTIPLY,
            tt.DIVIDE_MODULUS,
            tt.PLUS_MINUS,
            tt.RELATIONAL_OPERATOR,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
        }:
            node.add_child(TreeNode("null"))
            return node, var_type

        self.display_error("expected '->', '.', '[', '(' or expected expression to end")

    def parse_chaining_3(self, var_type: TypeInfo, dimensions_indexed):
        node = TreeNode("chaining_3")
        if self.curr_token.token_type in {tt.DOT}:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            if var_type.is_pointer:
                self.display_semantic_error("'.' cannot be used with pointer type")
                return
            if var_type.is_array and dimensions_indexed != var_type.dimensions:
                self.display_semantic_error("'.' cannot be used with array type")
                return
            if var_type.data_type in ["int", "float", "char", "string", "bool"]:
                self.display_semantic_error("cannot use '.' with primitive datatypes")
                return
            if var_type.data_type == "void":
                self.display_semantic_error("method has a void return type")
                return
            self.advance()

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                name = self.curr_token.value
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            class_name = var_type.data_type
            child = self.parse_chaining(name, class_name)
            if child is None:
                return
            child, type = child
            node.add_child(child)

            return node, type

        elif self.curr_token.token_type in {
            tt.POINTER_MULTIPLY,
            tt.DIVIDE_MODULUS,
            tt.PLUS_MINUS,
            tt.RELATIONAL_OPERATOR,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
        }:
            new_type = TypeInfo(var_type.data_type)
            new_type.dimensions = var_type.dimensions - dimensions_indexed
            node.add_child(TreeNode("null"))
            return node, new_type

        self.display_error("expected '->', '.', '[', '(' or expected expression to end")

    def parse_array_indexing_1d(self, var_type: TypeInfo):
        node = TreeNode("array_indexing_1d")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            if var_type.dimensions < 1:
                self.display_semantic_error("cannot subscript array further")
                return

            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.data_type != "int":
                self.display_semantic_error("Array can only be indexed by an integer")
                return

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_array_indexing_2d(var_type)
            if child is None:
                return
            child, dimensions_indexed = child
            node.add_child(child)

            return node, dimensions_indexed

        self.display_error("expected '['")
        # self.advance()
        # return TreeNode("error")

    def parse_array_indexing_2d(self, var_type: TypeInfo):
        node = TreeNode("array_indexing_2d")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            if var_type.dimensions < 2:
                self.display_semantic_error("cannot subscript array further")
                return
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.data_type != "int":
                self.display_semantic_error("Array can only be indexed by an integer")
                return

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_array_indexing_3d(var_type)
            if child is None:
                return
            child, dimensions_indexed = child
            node.add_child(child)

            return node, dimensions_indexed

        elif self.curr_token.token_type in {
            tt.DOT,
            tt.ARROW,
            tt.POINTER_MULTIPLY,
            tt.DIVIDE_MODULUS,
            tt.PLUS_MINUS,
            tt.RELATIONAL_OPERATOR,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
        }:
            node.add_child(TreeNode("null"))
            return node, 1

        self.display_error(
            "expected '[' , '.' , an operator or an expression termination"
        )
        # self.advance()
        # return TreeNode("error")

    def parse_array_indexing_3d(self, var_type: TypeInfo):
        node = TreeNode("parse_array_indexing_3d")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            if var_type.dimensions < 3:
                self.display_semantic_error("cannot subscript array further")
                return
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.data_type != "int":
                self.display_semantic_error("Array can only be indexed by an integer")
                return

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            return node, 3

        elif self.curr_token.token_type in {
            tt.DOT,
            tt.ARROW,
            tt.POINTER_MULTIPLY,
            tt.DIVIDE_MODULUS,
            tt.PLUS_MINUS,
            tt.RELATIONAL_OPERATOR,
            tt.LOGICAL_AND,
            tt.LOGICAL_OR,
            tt.SEMICOLON,
            tt.COMMA,
            tt.ROUND_BRACKET_CLOSE,
            tt.SQUARE_BRACKET_CLOSE,
            tt.COLON,
        }:
            node.add_child(TreeNode("null"))
            return node, 2

        self.display_error(
            "expected '[' , '.' , an operator or an expression termination"
        )

    def parse_pointer_dereferencing(self, result_type: TypeCheckingInfo):
        node = TreeNode("pointer_dereferencing")
        if self.curr_token.token_type == tt.POINTER_MULTIPLY:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_function_call()
            if child is None:
                return
            child, operand_type = child
            node.add_child(child)

            result_type = self.st_manager.check_compatibility_unirary_op(
                operand_type, "*"
            )
            if result_type is None:
                self.display_semantic_error(
                    f"Unsupported operator(*) for operand {operand_type}"
                )
                return

            return node, result_type

        self.display_error("expected dereferencing operator '*'")
        # self.advance()
        # return TreeNode("error")

    def parse_object_creation(self):
        node = TreeNode("object_creation")
        if self.curr_token.token_type == tt.OBJ_CREATOR:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            if self.curr_token.token_type == tt.IDENTIFIER:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                class_name = self.curr_token.value
                def_table_entry = self.st_manager.lookup_definition_table(class_name)
                if def_table_entry is None:
                    self.display_semantic_error(f"Undeclared definition {class_name}")
                    return
                if def_table_entry.type == "interface":
                    self.display_semantic_error("cannot create object of an interface")
                    return
                if def_table_entry.access_modifier == "private" and class_name != self.st_manager.current_def_name:
                    self.display_semantic_error("cannot create object of private (struct / class)")
                    return
                self.advance()
            else:
                self.display_error("expected an identifier")
                # self.advance()
                # return TreeNode("error")
                return

            param_type_list = []
            child = self.parse_func_args(param_type_list)
            if child is None:
                return
            node.add_child(child)

            if class_name is None:
                class_name = self.st_manager.current_def_name

            member_table_entry = self.st_manager.lookup_member_table_func(
                "constructor", param_type_list, class_name
            )
            if member_table_entry is None:
                self.display_semantic_error(
                    "undeclared constructor with the specified parameters"
                )
                return

            return node, TypeInfo(class_name)

        self.display_error("expected keyword 'makeObj'")
        # self.advance()
        # return TreeNode("error")

    def parse_expression_or_object_creation(self):
        node = TreeNode("expression_or_object_creation")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
        }:
            child = self.parse_expression()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        
        elif self.curr_token.token_type in {tt.OBJ_CREATOR}:
            child = self.parse_object_creation()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            return node, result_type
        self.display_error("expected expression or object creation")

    def parse_array_initialization(self):
        node = TreeNode("array_initialization")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            # arr_type = TypeInfo()

            child = self.parse_1d_array_elements()
            if child is None:
                return
            child, arr_type = child
            node.add_child(child)

            # arr_type.dimensions += 1

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            return node, arr_type

        self.display_error("expected '['")
        # self.advance()
        # return TreeNode("error")

    def parse_1d_array_elements(self):
        node = TreeNode("1d_array_elements")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
            tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_1d_array_element()
            if child is None:
                return
            child, arr_type_1d = child
            node.add_child(child)


            child = self.parse_1d_array_elements_2(arr_type_1d)
            if child is None:
                return
            node.add_child(child)

            arr_type_1d.dimensions +=1

            return node, arr_type_1d
        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            arr_type_1d = TypeInfo()
            arr_type_1d.dimensions +=1
            return node, arr_type_1d

        self.display_error("expected an expression or '[' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_1d_array_element(self, arr_type_1d: TypeInfo=None):
        node = TreeNode("1d_array_element")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
        }:
            child = self.parse_expression_or_object_creation()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.is_pointer:
                self.display_semantic_error("array cannot have type pointer")
                return

            if arr_type_1d is not None and arr_type_1d != result_type:
                self.display_semantic_error("All array elements must have same type")
                return
            elif result_type.dimensions > 2:
                self.display_semantic_error("Arrays can be at most 3d")
                return
            # if is_initial or arr_type.data_type == "":
            #     arr_type.data_type = result_type.data_type
            #     if arr_type.dimensions + result_type.dimensions > 3:
            #         self.display_semantic_error("Arrays can be at most 3d")
            #         return
            #     arr_type.dimensions += result_type.dimensions
                
            # elif arr_type != result_type:
            #     self.display_semantic_error("All array elements must have same type")
            #     return

            return node, result_type

        elif self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            # if is_initial:
            #     arr_type.dimensions += 1

            child = self.parse_2d_array_elements()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if arr_type_1d is not None and arr_type_1d != result_type:
                self.display_semantic_error("All array elements must have same type")
                return
            elif result_type.dimensions > 2:
                self.display_semantic_error("Arrays can be at most 3d")
                return


            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            return node, result_type

        self.display_error("expected expression or '['")
        # self.advance()
        # return TreeNode("error")

    def parse_1d_array_elements_2(self, arr_type_1d: TypeInfo):
        node = TreeNode("1d_array_elements_2")
        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_1d_array_element(arr_type_1d)
            if child is None:
                return
            child, arr_type_1d = child
            node.add_child(child)

            child = self.parse_1d_array_elements_2(arr_type_1d)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node
        self.display_error("expected expression or '[' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_2d_array_elements(self):
        node = TreeNode("2d_array_elements")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
            tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_2d_array_element()
            if child is None:
                return
            child, arr_type_2d = child
            node.add_child(child)

            child = self.parse_2d_array_elements_2(arr_type_2d)
            if child is None:
                return
            node.add_child(child)

            arr_type_2d.dimensions +=1

            return node, arr_type_2d
        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            arr_type_2d = TypeInfo()
            arr_type_2d.dimensions +=1
            return node, arr_type_2d

        self.display_error("expected an expression or '[' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_2d_array_element(self, arr_type_2d: TypeInfo=None):
        node = TreeNode("2d_array_element")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
        }:
            child = self.parse_expression_or_object_creation()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.is_pointer:
                self.display_semantic_error("array cannot have type pointer")
                return

            if arr_type_2d is not None and arr_type_2d != result_type:
                self.display_semantic_error("All array elements must have same type")
                return
            elif result_type.dimensions > 1:
                self.display_semantic_error("Arrays can be at most 3d")
                return

            # if is_initial or arr_type.data_type == "":
            #     arr_type.data_type = result_type.data_type
            #     if arr_type.dimensions + result_type.dimensions > 3:
            #         self.display_semantic_error("Arrays can be at most 3d")
            #         return
            #     arr_type.dimensions += result_type.dimensions
            # elif arr_type != result_type:
            #     self.display_semantic_error("All array elements must have same type")
            #     return

            return node, result_type

        elif self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()


            child = self.parse_3d_array_elements()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if arr_type_2d is not None and arr_type_2d != result_type:
                self.display_semantic_error("All array elements must have same type")
                return
            elif result_type.dimensions > 1:
                self.display_semantic_error("Arrays can be at most 3d")
                return
            
            # if is_initial:
            #     arr_type.dimensions += 1

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            return node, result_type

        self.display_error("expected expression or '['")
        # self.advance()
        # return TreeNode("error")

    def parse_2d_array_elements_2(self, arr_type_2d: TypeInfo):
        node = TreeNode("2d_array_elements_2")
        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_2d_array_element(arr_type_2d)
            if child is None:
                return
            child, arr_type_2d = child
            node.add_child(child)

            child = self.parse_2d_array_elements_2(arr_type_2d)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node
        self.display_error("expected expression or '[' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_3d_array_elements(self):
        node = TreeNode("3d_array_elements")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
        }:
            child = self.parse_3d_array_element()
            if child is None:
                return
            child, arr_type_3d = child
            node.add_child(child)


            child = self.parse_3d_array_elements_2(arr_type_3d)
            if child is None:
                return
            node.add_child(child)

            arr_type_3d.dimensions +=1

            return node, arr_type_3d
        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            arr_type_3d = TypeInfo()
            arr_type_3d.dimensions +=1
            return node, arr_type_3d

        self.display_error("expected an expression or '[' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_3d_array_element(self, arr_type_3d: TypeInfo=None):
        node = TreeNode("2d_array_element")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            tt.OBJ_CREATOR,
        }:
            child = self.parse_expression_or_object_creation()
            if child is None:
                return
            child, result_type = child
            node.add_child(child)

            if result_type.is_pointer:
                self.display_semantic_error("array cannot have type pointer")
                return

            if arr_type_3d is not None and arr_type_3d != result_type:
                self.display_semantic_error("All array elements must have same type")
                return
            elif result_type.dimensions > 0:
                self.display_semantic_error("Arrays can be at most 3d")
                return

            # if is_initial or arr_type.data_type == "":
            #     arr_type.data_type = result_type.data_type
            #     if arr_type.dimensions + result_type.dimensions > 3:
            #         self.display_semantic_error("Arrays can be at most 3d")
            #         return
            #     arr_type.dimensions += result_type.dimensions
            # elif arr_type != result_type:
            #     self.display_semantic_error("All array elements must have same type")
            #     return

            return node, result_type

        
        self.display_error("expected expression ")
        # self.advance()
        # return TreeNode("error")

    def parse_3d_array_elements_2(self, arr_type_3d: TypeInfo):
        node = TreeNode("3d_array_elements_2")
        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_3d_array_element(arr_type_3d)
            if child is None:
                return
            node.add_child(child)

            child = self.parse_3d_array_elements_2(arr_type_3d)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node
        self.display_error("expected expression or '[' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_array_elements(self):
        node = TreeNode("array_elements")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            # tt.OBJ_CREATOR,
            # tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_expression()
            if child is None:
                return
            node.add_child(child)

            child = self.parse_array_element_list()
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected an expression or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_array_element_list(self):
        node = TreeNode("array_element_list")
        if self.curr_token.token_type == tt.COMMA:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression()
            if child is None:
                return
            node.add_child(child)

            child = self.parse_array_element_list()
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected ',' or ']'")
        # self.advance()
        # return TreeNode("error")

    def parse_return_type(self, type: TypeInfo):
        node = TreeNode("return_type")
        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER}:
            child = self.parse_type(type)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type == tt.VOID_TYPE:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            type.data_type = "void"
            self.advance()

            return node

        self.display_error("expected a return type")
        # self.advance()
        # return TreeNode("error")

    def parse_type(self, type: TypeInfo):
        node = TreeNode("type")
        if self.curr_token.token_type in {tt.DATA_TYPE, tt.IDENTIFIER}:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            if self.curr_token.token_type == tt.IDENTIFIER:
                class_name = self.curr_token.value
                if self.st_manager.lookup_definition_table(class_name) is None:
                    self.display_semantic_error(f"Undeclared definition {class_name}")
                    return
            type.data_type = self.curr_token.value
            self.advance()

            child = self.parse_type_2(type)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected a type")
        # self.advance()
        # return TreeNode("error")

    def parse_type_2(self, type: TypeInfo):
        node = TreeNode("type_2")
        if self.curr_token.token_type == tt.POINTER_MULTIPLY:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            type.is_pointer = True
            self.advance()

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_OPEN}:
            child = self.parse_array_type(type)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.FUNCTION, tt.IDENTIFIER}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error(
            "expected pointer type or array type or 'function' or identifier"
        )
        # self.advance()
        # return TreeNode("error")

    def parse_array_type(self, type: TypeInfo):
        node = TreeNode("array_type")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression_optional()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                type.dimensions += 1
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_array_dimension_list(type)
            if child is None:
                return
            node.add_child(child)

            return node

        self.display_error("expected '['")
        # self.advance()
        # return TreeNode("error")

    def parse_array_dimension_list(self, type: TypeInfo):
        node = TreeNode("array_dimension_list")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression_optional()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                type.dimensions += 1
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            child = self.parse_array_dimension_list_2(type)
            if child is None:
                return
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.FUNCTION, tt.IDENTIFIER}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected '[' or 'function' or an identifier")
        # self.advance()
        # return TreeNode("error")

    def parse_array_dimension_list_2(self, type: TypeInfo):
        node = TreeNode("array_dimension_list_2")
        if self.curr_token.token_type == tt.SQUARE_BRACKET_OPEN:
            child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
            node.add_child(child)
            self.advance()

            child = self.parse_expression_optional()
            if child is None:
                return
            node.add_child(child)

            if self.curr_token.token_type == tt.SQUARE_BRACKET_CLOSE:
                child = TreeNode(self.curr_token.token_type.name, self.curr_token.value)
                node.add_child(child)
                type.dimensions += 1
                self.advance()
            else:
                self.display_error("expected ']'")
                # self.advance()
                # return TreeNode("error")
                return

            return node

        elif self.curr_token.token_type in {tt.FUNCTION, tt.IDENTIFIER}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected '[' or 'function' or an identifier")
        # self.advance()
        # return TreeNode("error")

    def parse_expression_optional(self):
        node = TreeNode("expression_optional")
        if self.curr_token.token_type in {
            tt.THIS,
            tt.SUPER,
            tt.IDENTIFIER,
            tt.INTEGER_LITERAL,
            tt.FLOAT_LITERAL,
            tt.BOOL_LITERAL,
            tt.CHAR_LITERAL,
            tt.STRING_LITERAL,
            tt.ROUND_BRACKET_OPEN,
            tt.NOT_OPERATOR,
            tt.POINTER_MULTIPLY,
            # tt.OBJ_CREATOR,
            # tt.SQUARE_BRACKET_OPEN,
        }:
            child = self.parse_expression()
            if child is None:
                return
            child, _ = child
            node.add_child(child)

            return node

        elif self.curr_token.token_type in {tt.SQUARE_BRACKET_CLOSE}:
            node.add_child(TreeNode("null"))
            return node

        self.display_error("expected an expression or ']'")
        # self.advance()
        # return TreeNode("error")
