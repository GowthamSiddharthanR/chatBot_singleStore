from app.extension import db
from datetime import datetime

class UploadedPDF(db.Model):
    __tablename__ = 'uploaded_pdfs'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=True)  # Optional: link to a user
    file_path = db.Column(db.String(512), nullable=False)
