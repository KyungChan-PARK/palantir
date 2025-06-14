class Pipeline:
    id: str
    name: str
    status: str
    start_time = None
    end_time = None
    result = None

    @staticmethod
    def create(*a, **k):
        return Pipeline()
