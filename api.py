from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
import pandas as pd
import numpy as np
import json
import os
from backend.hybrid_decision import make_decision
from backend.utils import get_feature_engineered_path, load_model
from backend.autoencoder import AutoencoderInference
from backend.rule_engine import calculate_all_limits
from backend.db_service import get_db_service
from backend.velocity_service import get_velocity_service
from backend.file_operations import get_safe_file_ops
from backend.input_validator import get_validator

app = FastAPI(title="Banking Fraud Detection API", version="1.0.0")

class TransactionRequest(BaseModel):
    customer_id: str = Field(..., min_length=6, max_length=10)
    from_account_no: str = Field(..., min_length=5, max_length=20)
    to_account_no: str = Field(..., min_length=5, max_length=20)
    transaction_amount: float = Field(..., gt=0, le=1000000)
    transfer_type: str = Field(..., regex="^[OILQS]$")
    datetime: datetime
    bank_country: Optional[str] = "UAE"
    
    @validator('customer_id')
    def validate_customer_id(cls, v):
        if not v.isdigit():
            raise ValueError('Customer ID must contain only digits')
        return v
    
    @validator('transaction_amount')
    def validate_amount(cls, v):
        if v < 1:
            raise ValueError('Minimum amount is AED 1')
        return round(v, 2)
    
    @validator('transfer_type')
    def validate_transfer_type(cls, v):
        return v.upper()
    
    @validator('datetime')
    def validate_datetime(cls, v):
        now = datetime.now()
        if v > now:
            raise ValueError('Transaction datetime cannot be in the future')
        if (now - v).days > 1:
            raise ValueError('Transaction datetime cannot be more than 1 day old')
        return v

class TransactionResponse(BaseModel):
    decision: str
    risk_score: float
    confidence_level: float
    reasons: List[str]
    individual_scores: dict
    transaction_id: str
    processing_time_ms: int


from backend.file_operations import get_safe_file_ops
from backend.velocity_service import get_velocity_service

class DatabaseStatsManager:
    def __init__(self):
        self.stats_file = "data/user_stats.json"
        self.db_service = get_db_service()
        self.velocity_service = get_velocity_service()
        self.file_ops = get_safe_file_ops()
        self.stats = self.load_stats()
    
    def load_stats(self):
        return self.file_ops.read_json_safe(self.stats_file)
    
    def save_stats(self):
        self.file_ops.write_json_atomic(self.stats_file, self.stats)
    
    def get_user_stats(self, customer_id: str, account_no: str):
        try:
            if not self.db_service.connect():
                raise Exception("Cannot connect to database")
            
            return self.db_service.get_user_statistics(customer_id, account_no)
        except Exception as e:
            print(f"Error getting user stats from DB: {e}")
            return {
                "user_avg_amount": 5000.0,
                "user_std_amount": 2000.0,
                "user_max_amount": 15000.0,
                "user_txn_frequency": 0,
                "user_international_ratio": 0.0,
                "current_month_spending": 0.0
            }
    
    def get_velocity_metrics(self, customer_id: str, account_no: str):
        return self.velocity_service.get_velocity_metrics(customer_id, account_no)
    
    def record_transaction(self, customer_id: str, account_no: str, amount: float):
        self.velocity_service.record_transaction(customer_id, account_no, amount)
        
        if hasattr(self, '_cleanup_counter'):
            self._cleanup_counter += 1
        else:
            self._cleanup_counter = 1
        
        if self._cleanup_counter % 100 == 0:
            cleanup_stats = self.velocity_service.cleanup_old_data()
            print(f"Cleanup performed: {cleanup_stats}")
        
        self.save_stats()
    
    def check_is_new_beneficiary(self, customer_id: str, recipient_account: str):
        try:
            if not self.db_service.connect():
                return 1
            
            return self.db_service.check_new_beneficiary(customer_id, recipient_account)
        except Exception as e:
            print(f"Error checking beneficiary: {e}")
            return 1
    
    def save_transaction_history(self, request, decision: str, result: dict, transaction_id: str):
        row_data = [
            transaction_id,
            request.customer_id,
            request.from_account_no,
            request.transaction_amount,
            decision,
            "|".join(result.get('reasons', [])) if result.get('reasons') else "Normal transaction",
            datetime.now().isoformat()
        ]
        
        self.file_ops.append_csv_safe("data/transaction_history.csv", row_data)

stats_manager = DatabaseStatsManager()
model, features, scaler = load_model()
autoencoder = AutoencoderInference()
autoencoder.load()


@app.get("/api/health")
def health_check():
    db_status = "connected"
    try:
        db = get_db_service()
        if not db.connect():
            db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    memory_stats = stats_manager.velocity_service.get_memory_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "models": {
            "isolation_forest": "loaded" if model else "unavailable",
            "autoencoder": "loaded" if autoencoder else "unavailable"
        },
        "memory": memory_stats
    }

@app.post("/api/analyze-transaction", response_model=TransactionResponse)
def analyze_transaction(request: TransactionRequest):
    start_time = datetime.now()
    
    try:
        validation_result = get_validator().validate_transaction_request({
            'customer_id': request.customer_id,
            'from_account_no': request.from_account_no,
            'to_account_no': request.to_account_no,
            'transaction_amount': request.transaction_amount,
            'transfer_type': request.transfer_type,
            'bank_country': request.bank_country,
            'datetime': request.datetime
        })
        
        if not validation_result['valid']:
            raise HTTPException(status_code=400, detail={
                "error": "Validation failed",
                "details": validation_result['errors']
            })
        
        cleaned_data = validation_result['cleaned_data']
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Input validation error: {str(e)}")
    
    user_stats = stats_manager.get_user_stats(cleaned_data['customer_id'], cleaned_data['from_account_no'])
    velocity = stats_manager.get_velocity_metrics(cleaned_data['customer_id'], cleaned_data['from_account_no'])
    session_spending = stats_manager.velocity_service.get_session_spending(cleaned_data['customer_id'], cleaned_data['from_account_no'])
    
    is_new_ben = stats_manager.check_is_new_beneficiary(cleaned_data['customer_id'], cleaned_data['to_account_no'])
    
    txn = {
        "amount": cleaned_data['transaction_amount'],
        "transfer_type": cleaned_data['transfer_type'],
        "bank_country": cleaned_data['bank_country'],
        "datetime": cleaned_data['datetime'],
        "txn_count_30s": 1,  
        "txn_count_10min": velocity["txn_count_10min"] + 1,
        "txn_count_1hour": velocity["txn_count_1hour"] + 1,
        "time_since_last_txn": velocity["time_since_last_txn"],
        "session_spending": session_spending,
        "is_new_beneficiary": is_new_ben
    }
    
    result = make_decision(txn, user_stats, model, features, autoencoder)
    
    decision = "REQUIRES_USER_APPROVAL" if result['is_fraud'] else "APPROVED"
    
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
    transaction_id = f"txn_{cleaned_data['datetime'].strftime('%Y%m%d_%H%M%S')}_{cleaned_data['customer_id']}"
    stats_manager.save_transaction_history(request, decision, result, transaction_id)
    
    if decision == "APPROVED":
        stats_manager.record_transaction(cleaned_data['customer_id'], cleaned_data['from_account_no'], cleaned_data['transaction_amount'])
    
    return TransactionResponse(
        decision=decision,
        risk_score=result.get('risk_score', 0.0),
        confidence_level=0.85,
        reasons=result.get('reasons', []),
        individual_scores={
            "rule_engine": {"violated": result['rule_violation'], "threshold": result.get('threshold', 0)},
            "isolation_forest": {"anomaly_score": result.get('risk_score', 0), "is_anomaly": result.get('ml_anomaly', False)},
            "autoencoder": {"reconstruction_error": result.get('ae_reconstruction_error'), "is_anomaly": result.get('ae_anomaly', False)}
        },
        transaction_id=transaction_id,
        processing_time_ms=processing_time
    )

@app.get("/api/cleanup")
def manual_cleanup():
    cleanup_stats = stats_manager.velocity_service.cleanup_old_data()
    memory_stats = stats_manager.velocity_service.get_memory_stats()
    
    return {
        "cleanup_performed": cleanup_stats,
        "current_memory": memory_stats,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
