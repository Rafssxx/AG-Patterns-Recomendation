"""Gerador de respostas do assistente para o chat.

Fornece uma resposta de demonstração (mock) que pode ser trocada por uma
integração real com um LLM (ex.: langchain) no futuro, sem alterar a UI.
"""

from .utils import contains_code_request


class Response:
    """Gera as respostas exibidas na área de saída do chat."""

    def reply(self, user_input: str) -> str:
        """Devolve uma resposta em markdown para a mensagem do usuário."""
        # Se o usuário pedir um exemplo de código, devolve um com destaque.
        if contains_code_request(user_input):
            return (
                "Claro! Veja um exemplo do padrão **Singleton** em Python:\n\n"
                "```python\n"
                "class Singleton:\n"
                "    _instance = None\n\n"
                "    def __new__(cls):\n"
                "        if cls._instance is None:\n"
                "            cls._instance = super().__new__(cls)\n"
                "        return cls._instance\n"
                "```\n\n"
                "Ele garante que a classe tenha apenas uma única instância."
            )

        # Resposta genérica enquanto não há um LLM conectado.
        return (
            "Recebi sua mensagem! Como este é um protótipo, respondo com este "
            "texto de exemplo. Conecte um LLM no `cli/responder.py` para obter "
            "respostas reais sobre **padrões de projeto**."
        )
