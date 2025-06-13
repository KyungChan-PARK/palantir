from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
import json
import sqlite3
from pydantic import BaseModel

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataConfig(BaseModel):
    """데이터 파이프라인 설정"""
    input_path: str
    output_path: str
    db_path: str
    batch_size: int = 1000
    cache_size: int = 10000

class DataPipeline:
    """데이터 처리 파이프라인"""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self._setup_directories()
        self._setup_database()
    
    def _setup_directories(self):
        """디렉토리 설정"""
        Path(self.config.input_path).mkdir(parents=True, exist_ok=True)
        Path(self.config.output_path).mkdir(parents=True, exist_ok=True)
    
    def _setup_database(self):
        """데이터베이스 설정"""
        self.conn = sqlite3.connect(self.config.db_path)
        self._create_tables()
    
    def _create_tables(self):
        """테이블 생성"""
        cursor = self.conn.cursor()
        
        # 에이전트 로그 테이블
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            timestamp DATETIME,
            action TEXT,
            input_data TEXT,
            output_data TEXT,
            status TEXT,
            error TEXT
        )
        """)
        
        # 성능 메트릭 테이블
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            cpu_usage REAL,
            memory_usage REAL,
            active_agents INTEGER,
            total_requests INTEGER
        )
        """)
        
        # selfimprove_history 테이블
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS selfimprove_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file TEXT,
            timestamp DATETIME,
            diff TEXT,
            description TEXT
        )
        """)
        
        self.conn.commit()
    
    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """데이터 전처리"""
        # 결측치 처리
        data = data.fillna(method='ffill')
        
        # 이상치 처리
        for column in data.select_dtypes(include=[np.number]).columns:
            Q1 = data[column].quantile(0.25)
            Q3 = data[column].quantile(0.75)
            IQR = Q3 - Q1
            data = data[
                (data[column] >= Q1 - 1.5 * IQR) &
                (data[column] <= Q3 + 1.5 * IQR)
            ]
        
        return data
    
    def save_to_parquet(self, data: pd.DataFrame, filename: str):
        """Parquet 형식으로 저장"""
        output_path = Path(self.config.output_path) / f"{filename}.parquet"
        data.to_parquet(output_path, index=False)
        logger.info(f"데이터가 저장되었습니다: {output_path}")
    
    def log_agent_action(
        self,
        agent_id: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        status: str,
        error: Optional[str] = None
    ):
        """에이전트 액션 로깅"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO agent_logs (
            agent_id, timestamp, action, input_data, output_data, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            datetime.now(),
            action,
            json.dumps(input_data),
            json.dumps(output_data),
            status,
            error
        ))
        self.conn.commit()
    
    def log_performance_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        active_agents: int,
        total_requests: int
    ):
        """성능 메트릭 로깅"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO performance_metrics (
            timestamp, cpu_usage, memory_usage, active_agents, total_requests
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            cpu_usage,
            memory_usage,
            active_agents,
            total_requests
        ))
        self.conn.commit()
    
    def get_agent_logs(
        self,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """에이전트 로그 조회"""
        query = "SELECT * FROM agent_logs WHERE 1=1"
        params = []
        
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def get_performance_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """성능 메트릭 조회"""
        query = "SELECT * FROM performance_metrics WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def log_selfimprove_history(self, file: str, timestamp: str, diff: str, description: str):
        """자가 개선 변경 이력 기록"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO selfimprove_history (file, timestamp, diff, description)
        VALUES (?, ?, ?, ?)
        """, (file, timestamp, diff, description))
        self.conn.commit()
    
    def close(self):
        """리소스 정리"""
        self.conn.close() 