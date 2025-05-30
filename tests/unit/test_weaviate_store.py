from palantir.core.weaviate_store import store_to_weaviate, get_data_by_job_id

def test_store_and_get():
    store_to_weaviate("jobid", {"x": 1})
    assert get_data_by_job_id("jobid") == {"x": 1}
    assert get_data_by_job_id("notfound") is None 