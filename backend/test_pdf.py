import sys
import os

# Set up paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal
import models
from main import export_scan_pdf, export_history_pdf

def test():
    db = SessionLocal()
    # Get any user
    user = db.query(models.User).first()
    if not user:
        print("No users in DB")
        return
        
    scan = db.query(models.Scan).filter(models.Scan.user_id == user.id).first()
    if not scan:
        print("No scans for user")
        return
        
    print(f"Testing for user {user.email}, scan {scan.id}")
    
    try:
        # Test scan pdf
        res_scan = export_scan_pdf(scan.id, current_user=user, db=db)
        print(f"Scan PDF status: {getattr(res_scan, 'status_code', 'OK')}")
        if hasattr(res_scan, 'body') and len(res_scan.body) > 1000:
             pass
        else:
             print(f"Scan response body might be error: {getattr(res_scan, 'body', res_scan)}")
    except Exception as e:
        print(f"Scan PDF threw: {e}")
        
    try:
        # Test history pdf
        res_hist = export_history_pdf(current_user=user, db=db)
        print(f"History PDF status: {getattr(res_hist, 'status_code', 'OK')}")
        if hasattr(res_hist, 'body') and len(res_hist.body) > 1000:
             pass
        else:
             print(f"History response body might be error: {getattr(res_hist, 'body', res_hist)}")
    except Exception as e:
        print(f"History PDF threw: {e}")
        
    db.close()

if __name__ == "__main__":
    test()
