from typing import Hashable, TypeVar

__all__ = ["K", "V"]

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
