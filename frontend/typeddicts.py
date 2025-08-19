from typing import TypedDict, List, Any


class TopologyStructure(TypedDict):
    """拓扑结构"""
    nodes: List[Any]
    edges: List[Any]


class LoginedUserInfo(TypedDict):
    username: str
