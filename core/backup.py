import io
import os
import tempfile
import datetime
from django.core.management import call_command
from django.db import transaction

class BackupManager:
    @staticmethod
    def create_backup():
        """Creates a JSON backup of the entire database and returns a BytesIO buffer."""
        buffer = io.StringIO()
        # We exclude auto-generated content types and permissions to avoid conflicts on restore
        call_command(
            'dumpdata', 
            format='json', 
            exclude=['contenttypes', 'auth.permission', 'sessions.session', 'core.auditlog'], 
            indent=2,
            stdout=buffer
        )
        
        byte_buffer = io.BytesIO(buffer.getvalue().encode('utf-8'))
        byte_buffer.seek(0)
        
        filename = f"erp_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return byte_buffer, filename
        
    @staticmethod
    @transaction.atomic
    def restore_backup(file_stream):
        """Restores the database from a JSON backup stream."""
        fd, temp_path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(file_stream.read())
            
            # Note: loaddata updates existing records with matching PKs.
            call_command('loaddata', temp_path)
            return True, "Database restored successfully."
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
