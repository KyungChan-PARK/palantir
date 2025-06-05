class LLMManager:
    def __init__(self, offline: bool = False):
        self.offline = offline
        self.client = None

    def generate_code(self, prompt: str, mode: str = "sql") -> str:
        if mode not in ("sql", "pyspark"):
            raise ValueError("unsupported mode")
        return "SELECT 1" if mode == "sql" else "df.filter()"
