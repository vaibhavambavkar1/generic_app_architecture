import io
import csv
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

class DataExporter:
    """
    Generic Data Exporter for generating CSV, JSON, and Excel formats 
    from Django QuerySets or lists of objects.
    """
    
    @staticmethod
    def _get_field_value(obj, field_path):
        """Helper to resolve dot notation (e.g. 'item.name')"""
        if isinstance(obj, dict):
            return obj.get(field_path, "")
            
        val = obj
        for part in field_path.split('.'):
            if val is None:
                break
            val = getattr(val, part, None)
            if callable(val):
                val = val()
                
        # Coerce Django models to string if they slip through
        if isinstance(val, models.Model):
            return str(val)
        return val

    @staticmethod
    def export_csv(queryset, fields):
        """
        Export a queryset to a CSV BytesIO buffer.
        `fields` is a list of tuples: [('model_field_or_dot_path', 'Column Name')]
        """
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Write Headers
        writer.writerow([label for _, label in fields])
        
        # Write Data
        for obj in queryset:
            row = []
            for field, _ in fields:
                val = DataExporter._get_field_value(obj, field)
                row.append(str(val) if val is not None else '')
            writer.writerow(row)
            
        byte_buffer = io.BytesIO(buffer.getvalue().encode('utf-8'))
        return byte_buffer
        
    @staticmethod
    def export_json(queryset, fields):
        """
        Export a queryset to a JSON BytesIO buffer.
        """
        data = []
        for obj in queryset:
            row = {}
            for field, label in fields:
                row[label] = DataExporter._get_field_value(obj, field)
            data.append(row)
            
        json_str = json.dumps(data, cls=DjangoJSONEncoder, indent=2)
        return io.BytesIO(json_str.encode('utf-8'))

    @staticmethod
    def export_excel(queryset, fields):
        """
        Export a queryset to an Excel BytesIO buffer.
        Requires `openpyxl`.
        """
        import openpyxl
        
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Export Data"
        
        # Write Headers
        headers = [label for _, label in fields]
        sheet.append(headers)
        
        # Apply basic bold styling to headers
        for cell in sheet[1]:
            cell.font = openpyxl.styles.Font(bold=True)
        
        # Write Data
        for obj in queryset:
            row = []
            for field, _ in fields:
                val = DataExporter._get_field_value(obj, field)
                # Ensure no complex types leak into Excel engine
                if isinstance(val, (dict, list, tuple)):
                    val = str(val)
                row.append(val)
            sheet.append(row)
            
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer
