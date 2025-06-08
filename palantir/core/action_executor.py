from typing import Any, Dict
import asyncio
from prefect.client.orchestration import get_client

async def run_deployment(handler: str, parameters: Dict[str, Any]) -> str:
    """
    Prefect 2.x API를 통해 지정한 handler(flow/deployment)와 파라미터로 실행 요청을 보낸다.
    handler: Prefect flow 이름 또는 deployment 이름 (예: 'notify_user')
    parameters: dict (flow에 전달할 파라미터)
    반환값: flow_run_id
    """
    async with get_client() as client:
        # deployment_name은 handler로 전달 (예: 'notify_user')
        deployment = await client.read_deployment_by_name(handler)
        flow_run = await client.create_flow_run_from_deployment(
            deployment_id=deployment.id,
            parameters=parameters
        )
        return str(flow_run.id) 