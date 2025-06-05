class DummyScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, func, *a, **k):
        self.jobs.append((func, a, k))


def add_pipeline_job(dag):
    pass


scheduler = DummyScheduler()
