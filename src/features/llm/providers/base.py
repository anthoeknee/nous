from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class BaseProvider(ABC):
    def __init__(self, identifier: str = "default"):
        self.identifier = identifier

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        pass
