import csv
import json
import io
from django.db import transaction
from django.apps import apps
from django.core.exceptions import ValidationError

class DataImporter:
    """
    Generic Data Importer for parsing CSV, JSON, and Excel formats 
    and bulk inserting them into Django models.
    """
    
    @staticmethod
    def parse_csv(file_stream):
        """Parse a CSV file stream into a list of dictionaries."""
        decoded_file = file_stream.read().decode('utf-8-sig') # Handle BOM if present
        reader = csv.DictReader(io.StringIO(decoded_file))
        return [row for row in reader]
        
    @staticmethod
    def parse_json(file_stream):
        """Parse a JSON file stream into a list of dictionaries."""
        return json.load(file_stream)
        
    @staticmethod
    def parse_excel(file_stream):
        """Parse an Excel file stream into a list of dictionaries."""
        import openpyxl
        workbook = openpyxl.load_workbook(file_stream, data_only=True)
        sheet = workbook.active
        
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []
            
        headers = rows[0]
        data = []
        for row in rows[1:]:
            # Ignore completely empty rows
            if not any(row):
                continue
            row_dict = dict(zip(headers, row))
            data.append(row_dict)
        return data

    @staticmethod
    def import_data(app_label, model_name, file_stream, fmt, mapping, unique_fields=None):
        """
        Parses a file and imports data into a specified model.
        - `fmt`: 'csv', 'json', or 'excel'
        - `mapping`: dict mapping { "File Column Name": "model_field_name" }
        - `unique_fields`: list of model fields to check for existing records (upsert logic).
        """
        if fmt == 'csv':
            parsed_data = DataImporter.parse_csv(file_stream)
        elif fmt == 'json':
            parsed_data = DataImporter.parse_json(file_stream)
        elif fmt == 'excel':
            parsed_data = DataImporter.parse_excel(file_stream)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
            
        model_class = apps.get_model(app_label, model_name)
        return DataImporter._process_data(model_class, parsed_data, mapping, unique_fields)
        
    @staticmethod
    @transaction.atomic
    def _process_data(model_class, data, mapping, unique_fields=None):
        """Core engine that loops through rows and upserts/creates records safely."""
        created_count = 0
        updated_count = 0
        errors = []
        
        for index, row in enumerate(data):
            try:
                # Transform row using mapping
                model_data = {}
                for file_col, model_field in mapping.items():
                    # Handle missing columns gracefully
                    if file_col in row and row[file_col] is not None:
                        # Optional: Add custom transformers here if needed (e.g., date parsing)
                        model_data[model_field] = row[file_col]
                        
                if not model_data:
                    continue
                    
                # Clean the data using the model's built in validations
                instance = model_class(**model_data)
                instance.clean_fields()
                
                # Perform Upsert if unique_fields are provided
                if unique_fields:
                    lookup = {field: model_data[field] for field in unique_fields if field in model_data}
                    if lookup:
                        obj, created = model_class.objects.update_or_create(
                            defaults=model_data,
                            **lookup
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                        continue
                
                # Default to Create
                instance.save()
                created_count += 1
                    
            except ValidationError as e:
                errors.append(f"Row {index + 1} Validation Error: {e.message_dict}")
            except Exception as e:
                errors.append(f"Row {index + 1} Error: {str(e)}")
                
        return {
            'success': len(errors) == 0,
            'created': created_count,
            'updated': updated_count,
            'errors': errors
        }
