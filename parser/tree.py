from typing import Union, List

class TreeNode:
    def __init__(self, node_type, value=None):
        self.node_type: str = node_type
        self.value: Union[str, None] = value
        self.children: List[TreeNode] = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def jsonify(self):
        node_dict = {
            "node_type": self.node_type,
        }
        if self.value is not None:
            node_dict["value"] = self.value
        if self.children:
            node_dict["children"] = [child.jsonify() for child in self.children]
        return node_dict
