class Report:
    id: str
    title: str
    content: str
    status: str
    created_at = None

    @staticmethod
    def create(*a, **k):
        return Report()
