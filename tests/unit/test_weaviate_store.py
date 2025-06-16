from palantir.core.weaviate_store import (_memory_store, get_data_by_job_id,
                                          store_to_weaviate)


def test_store_and_get():
    job_id = "jobid"
    obj = {"job_id": job_id, "x": 1}
    _memory_store[job_id] = obj
    store_to_weaviate(obj)
    assert get_data_by_job_id(job_id)["x"] == 1
    assert get_data_by_job_id("notfound") is None
