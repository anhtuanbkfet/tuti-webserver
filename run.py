from app import app
from app.auto_backupdata import AutoBackupData, onTimerTicked

from app import db
# db.create_all()

# backup = AutoBackupData(6*3600, onTimerTicked)
# backup.start()
# run auto backup every 6h:
if __name__ == '__main__': 
    app.run(port=5000)
    # backup.cancel()