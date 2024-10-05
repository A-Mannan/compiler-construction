from typing import List


class TypeInfo:
    def __init__(self, data_type: str = "") -> None:
        self.data_type: str = data_type
        self.dimensions = 0
        self.is_pointer = False

    @property
    def is_user_defined_type(self) -> bool:
        return self.data_type not in ["int", "float", "char", "string", "bool"]

    @property
    def is_array(self) -> bool:
        return self.dimensions > 0

    def __eq__(self, other):
        if isinstance(other, TypeInfo):
            return (
                self.data_type == other.data_type
                and self.dimensions == other.dimensions
                and self.is_pointer == other.is_pointer
            )
        return False

    def __repr__(self) -> str:
        if self.is_pointer:
            return self.data_type + "*"

        return self.data_type + "".join(["[]" for _ in range(self.dimensions)])


class MemberType:
    is_function: bool
    func_param_type_list: List[TypeInfo] | None
    func_return_type: TypeInfo | None

    var_type: TypeInfo

    def __init__(self) -> None:
        self.is_function = False
        self.func_param_type_list = []

    def __repr__(self) -> str:
        if self.is_function:
            str_param_list = (
                ",".join([str(i) for i in self.func_param_type_list])
                if self.func_param_type_list
                else str(None)
            )
            return "Function: " + str_param_list + "->" + str(self.func_return_type)
        return "Var: " + str(self.var_type)


class ScopeTableEntry:
    name: str
    type: TypeInfo
    scope: int


class MemberTableEntry:
    name: str
    type: MemberType
    access_modifier: str
    is_static: bool

    def __init__(self) -> None:
        self.access_modifier = "private"
        self.is_static = False
        self.type = MemberType()


class DefinitionTableEntry:
    name: str
    type: str
    access_modifier: str
    parent_class: str
    interface_list: List[str]
    member_table: List[MemberTableEntry]

    def __init__(self) -> None:
        self.access_modifier = "public"
        self.parent_class = None
        self.interface_list = []
        self.member_table = []
