class Ontology:
    id: str
    name: str
    description: str
    created_at = None

    @staticmethod
    def create(*a, **k):
        return Ontology()
