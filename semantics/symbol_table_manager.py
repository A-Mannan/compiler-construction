from typing import List, Dict, Tuple
from semantics.utils import (
    DefinitionTableEntry,
    MemberTableEntry,
    ScopeTableEntry,
    TypeInfo,
)
from tabulate import tabulate


class SymbolTableManager:
    def __init__(self) -> None:
        self.last_scope_num = 0
        self.scope_stack: List[int] = []
        self.scope_table: List[ScopeTableEntry] = []
        self.definition_table: List[DefinitionTableEntry] = []
        self.current_def_name: str | None = None
        self.is_curr_def_class = False
        self.is_main_found = False
        self.curr_func_return_type: TypeInfo | None = None

    def generate_scope_number(self) -> int:
        self.last_scope_num += 1
        return self.last_scope_num

    def create_scope(self, is_loop=False):
        self.scope_stack.append((self.generate_scope_number(), is_loop))

    def destroy_scope(self):
        self.scope_stack.pop()

    def check_constructor_exist(self):
        def_table = self.lookup_definition_table(self.current_def_name)
        for entry in def_table.member_table:
            if entry.name == "constructor" and entry.type.is_function:
                return True

        while def_table.parent_class is not None:
            def_table = self.lookup_definition_table(def_table.parent_class)
            for entry in def_table.member_table:
                if entry.name == "constructor" and entry.type.is_function:
                    return True
                
        return False

    def insert_into_scope_table(self, scope_table_entry: ScopeTableEntry) -> bool:
        scope_table_entry.scope, _ = self.scope_stack[-1]
        for entry in self.scope_table:
            if (
                entry.name == scope_table_entry.name
                and entry.scope == scope_table_entry.scope
            ):
                return False

        self.scope_table.append(scope_table_entry)
        return True

    def insert_into_definition_table(
        self, def_table_entry: DefinitionTableEntry
    ) -> bool:
        for entry in self.definition_table:
            if entry.name == def_table_entry.name:
                return False

        self.definition_table.append(def_table_entry)
        return True

    def insert_into_member_table(self, member_table_entry: MemberTableEntry) -> bool:
        member_table = self.lookup_definition_table(self.current_def_name).member_table
        for entry in member_table:
            if entry.name == member_table_entry.name:
                if (
                    not entry.type.is_function
                    or not member_table_entry.type.is_function
                ):
                    return False
                if (
                    entry.type.func_param_type_list
                    == member_table_entry.type.func_param_type_list
                ):
                    return False

        member_table.append(member_table_entry)
        return True

    def check_inside_loop(self):
        for _, is_loop in self.scope_stack[::-1]:
            if is_loop:
                return True
        return False

    def lookup_scope_table(self, name) -> TypeInfo:
        for scope, _ in self.scope_stack[::-1]:
            for entry in self.scope_table:
                if entry.name == name and entry.scope == scope:
                    return entry.type

    def lookup_definition_table(self, name) -> DefinitionTableEntry:
        for entry in self.definition_table:
            if entry.name == name:
                return entry

    def lookup_member_table(self, name, def_ref) -> MemberTableEntry:
        def_table = self.lookup_definition_table(def_ref)
        for entry in def_table.member_table:
            if entry.name == name:
                if not entry.type.is_function:
                    return entry

        while def_table.parent_class is not None:
            def_table = self.lookup_definition_table(def_table.parent_class)
            for entry in def_table.member_table:
                if entry.name == name:
                    if not entry.type.is_function:
                        return entry

    def lookup_member_table_func(
        self, name, param_type_list, def_ref
    ) -> MemberTableEntry:
        def_table = self.lookup_definition_table(def_ref)
        for entry in def_table.member_table:
            if entry.name == name:
                if (
                    entry.type.is_function
                    and entry.type.func_param_type_list == param_type_list
                ):
                    return entry

        while def_table.parent_class is not None:
            def_table = self.lookup_definition_table(def_table.parent_class)
            for entry in def_table.member_table:
                if entry.name == name:
                    if (
                        entry.type.is_function
                        and entry.type.func_param_type_list == param_type_list
                    ):
                        return entry

    def check_parent_class(self, parent_class_name, child_class_name) -> bool:
        def_table = self.lookup_definition_table(child_class_name)
        if (
            parent_class_name == def_table.parent_class
            or parent_class_name in def_table.interface_list
        ):
            return True

    def check_types_differ(self, left_operand_type, right_operand_type):
        return (
            left_operand_type.is_pointer
            and not right_operand_type.is_pointer
            or not left_operand_type.is_pointer
            and right_operand_type.is_pointer
            or left_operand_type.is_array
            and not right_operand_type.is_array
            or not left_operand_type.is_array
            and right_operand_type.is_array
        )

    def check_compatibility_binary_op(
        self, left_operand_type: TypeInfo, right_operand_type: TypeInfo, operator
    ) -> str:
        if operator == "=":
            if left_operand_type == right_operand_type:
                return left_operand_type
            elif (
                left_operand_type.data_type == "float"
                and right_operand_type.data_type == "int"
            ):
                if self.check_types_differ(left_operand_type, right_operand_type):
                    return
                return left_operand_type
            elif (
                left_operand_type.is_user_defined_type
                and right_operand_type.is_user_defined_type
            ):
                if self.check_parent_class(
                    left_operand_type.data_type, right_operand_type.data_type
                ):
                    if self.check_types_differ(left_operand_type, right_operand_type):
                        return
                    return left_operand_type

            elif (
                left_operand_type.is_array
                and right_operand_type.is_array
                and right_operand_type.data_type == ""
            ):
                return left_operand_type

            else:
                return

        if left_operand_type.is_array or right_operand_type.is_array:
            return
        if left_operand_type.is_pointer or right_operand_type.is_pointer:
            return

        if operator == "+":
            if (
                left_operand_type.data_type == "char"
                and right_operand_type.data_type == "char"
            ):
                return TypeInfo("char")
            if (
                left_operand_type.data_type == "char"
                and right_operand_type.data_type == "string"
            ):
                return TypeInfo("string")
            if (
                left_operand_type.data_type == "string"
                and right_operand_type.data_type == "char"
            ):
                return TypeInfo("string")
            if (
                left_operand_type.data_type == "string"
                and right_operand_type.data_type == "string"
            ):
                return TypeInfo("string")

            if (
                left_operand_type.data_type == "int"
                and right_operand_type.data_type == "int"
            ):
                return TypeInfo("int")
            if (
                left_operand_type.data_type == "int"
                and right_operand_type.data_type == "float"
            ):
                return TypeInfo("float")
            if (
                left_operand_type.data_type == "float"
                and right_operand_type.data_type == "int"
            ):
                return TypeInfo("float")
            if (
                left_operand_type.data_type == "float"
                and right_operand_type.data_type == "float"
            ):
                return TypeInfo("float")

        elif operator in ["-", "*", "/", "%"]:
            if (
                left_operand_type.data_type == "int"
                and right_operand_type.data_type == "int"
            ):
                return TypeInfo("int")
            if (
                left_operand_type.data_type == "int"
                and right_operand_type.data_type == "float"
            ):
                return TypeInfo("float")
            if (
                left_operand_type.data_type == "float"
                and right_operand_type.data_type == "int"
            ):
                return TypeInfo("float")
            if (
                left_operand_type.data_type == "float"
                and right_operand_type.data_type == "float"
            ):
                return TypeInfo("float")

        elif operator in ["=", "+=", "-=", "*=", "/=", "%="]:
            if left_operand_type.data_type == right_operand_type.data_type:
                return left_operand_type
            if (
                left_operand_type.data_type == "float"
                and right_operand_type.data_type == "int"
            ):
                return TypeInfo("float")

        elif operator == "==":
            if left_operand_type.data_type == right_operand_type.data_type:
                return TypeInfo("bool")
            if left_operand_type.data_type in [
                "int",
                "float",
            ] and right_operand_type.data_type in [
                "int",
                "float",
            ]:
                return TypeInfo("bool")

        elif operator in ["<", ">", "<=", ">="]:
            if left_operand_type.data_type in [
                "int",
                "float",
            ] and right_operand_type.data_type in [
                "int",
                "float",
            ]:
                return TypeInfo("bool")

        elif operator in ["&&", "||"]:
            if (
                left_operand_type.data_type == "bool"
                and right_operand_type.data_type == "bool"
            ):
                return TypeInfo("bool")

    def check_compatibility_unirary_op(
        self, operand_type: TypeInfo, operator
    ) -> TypeInfo:
        if operand_type.is_array:
            return None
        if (
            operator == "!"
            and operand_type.data_type == "bool"
            and not operand_type.is_pointer
        ):
            return TypeInfo("bool")
        if operator == "*" and operand_type.is_pointer:
            return TypeInfo(operand_type.data_type)
        if operator == "&" and not operand_type.is_pointer:
            new_type = TypeInfo(operand_type.data_type)
            new_type.is_pointer = True
            return new_type

    def print_def_table(self):
        print("Definition Table")
        entry_tuples = []
        for entry in self.definition_table:
            entry_tuples.append(
                (
                    entry.name,
                    entry.access_modifier,
                    entry.type,
                    entry.parent_class,
                    entry.interface_list,
                )
            )

        print(
            tabulate(
                entry_tuples,
                headers=["Name", "Access Modifier", "Type", "Parent", "Interface"],
                tablefmt="orgtbl",
            )
        )

    def print_all_member_tables(self):
        print("Member Tables: ")
        for def_entry in self.definition_table:
            entry_tuples = []
            print(f"\n {def_entry.name} Members")
            for entry in def_entry.member_table:
                entry_tuples.append(
                    (
                        entry.name,
                        entry.access_modifier,
                        entry.type,
                        entry.is_static,
                    )
                )

            print(
                tabulate(
                    entry_tuples,
                    headers=["Name", "Access Modifier", "Type", "Is Static"],
                    tablefmt="orgtbl",
                )
            )

    def print_scope_table(self):
        print("Scope Table:")
        entry_tuples = []
        for entry in self.scope_table:
            entry_tuples.append((entry.name, entry.type, entry.scope))

        print(
            tabulate(
                entry_tuples,
                headers=["Name", "Type", "Scope"],
                tablefmt="orgtbl",
            )
        )
