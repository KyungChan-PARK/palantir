from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

def add_pipeline_job(dag):
    # 실제로는 DAG의 각 task를 스케줄링해야 함. 예시는 이름만 출력
    print(f"[SCHEDULED] DAG: {dag['dag_name']}") 