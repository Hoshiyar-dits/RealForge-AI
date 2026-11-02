from datetime import datetime
from app.database.database import get_db
from app.auth.models.otp_codes import OtpCode
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
class OtpRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, user_id: int, purpose: str, code_hash: str, expires_at: datetime):
        try:
            # only the newest code per purpose stays valid
            self.db.query(OtpCode).filter(
                OtpCode.user_id == user_id,
                OtpCode.purpose == purpose,
                OtpCode.deleted_at.is_(None),
            ).update({OtpCode.deleted_at: func.now()})
            otp = OtpCode(
                user_id=user_id,
                purpose=purpose,
                code=code_hash,
                expires_at=expires_at,
            )
            self.db.add(otp)
            self.db.commit()
            self.db.refresh(otp)
            return otp
        except Exception:
            self.db.rollback()
            raise

    def get_active(self, user_id: int, purpose: str, now: datetime):
        return self.db.query(OtpCode).filter(
            OtpCode.user_id == user_id,
            OtpCode.purpose == purpose,
            OtpCode.used_at.is_(None),
            OtpCode.deleted_at.is_(None),
            OtpCode.expires_at > now,
        ).order_by(OtpCode.id.desc()).first()

    def increment_attempts(self, otp: OtpCode):
        try:
            otp.attempts = otp.attempts + 1
            self.db.commit()
            self.db.refresh(otp)
            return otp
        except Exception:
            self.db.rollback()
            raise

    def mark_used(self, otp: OtpCode):
        try:
            otp.used_at = func.now()
            self.db.commit()
            self.db.refresh(otp)
            return otp
        except Exception:
            self.db.rollback()
            raise

    def delete(self, otp: OtpCode):
        try:
            otp.deleted_at = func.now()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
