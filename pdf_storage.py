#!/usr/bin/env python3
"""
PDF Storage Handler for MotherDuck Integration
Handles storing and retrieving PDF reports from the cloud database
"""

import os
import base64
import hashlib
from typing import Optional, Dict, Any
import logging
from database_config import get_db

logger = logging.getLogger(__name__)

class PDFStorage:
    def __init__(self):
        self.db = get_db()
    
    def store_pdf(self, file_path: str, customer_id: str, company_name: str) -> bool:
        """
        Store PDF file in MotherDuck database with fallback to local storage
        
        Args:
            file_path: Path to the PDF file
            customer_id: Customer ID
            company_name: Company name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"PDF file not found: {file_path}")
                return False
            
            # Read PDF file
            with open(file_path, 'rb') as f:
                pdf_data = f.read()
            
            # Get file info
            file_size = len(pdf_data)
            file_name = os.path.basename(file_path)
            
            # Check if file is too large for MotherDuck (4MB limit)
            if file_size > 4 * 1024 * 1024:  # 4MB
                logger.warning(f"PDF too large for MotherDuck ({file_size} bytes), storing locally only")
                return self._store_locally(file_path, customer_id, company_name, file_name, file_size)
            
            # Encode to base64 for storage
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Store in database
            self.db.conn.execute("""
                INSERT OR REPLACE INTO pdf_reports (
                    customer_id, 
                    file_name, 
                    file_data, 
                    file_size, 
                    company_name,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, [customer_id, file_name, pdf_base64, file_size, company_name])
            
            # Store metadata
            self.db.store_report_metadata(customer_id, file_name, file_size, company_name)
            
            logger.info(f"Stored PDF for {customer_id} in MotherDuck: {file_name} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error storing PDF for {customer_id} in MotherDuck: {e}")
            # Fallback to local storage
            logger.info(f"Falling back to local storage for {customer_id}")
            return self._store_locally(file_path, customer_id, company_name, os.path.basename(file_path), len(pdf_data))
    
    def _store_locally(self, file_path: str, customer_id: str, company_name: str, file_name: str, file_size: int) -> bool:
        """
        Store PDF locally as fallback when MotherDuck fails
        
        Args:
            file_path: Path to the PDF file
            customer_id: Customer ID
            company_name: Company name
            file_name: Original file name
            file_size: File size in bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import shutil
            
            # Create local reports directory if it doesn't exist
            local_reports_dir = "reports"
            os.makedirs(local_reports_dir, exist_ok=True)
            
            # Copy PDF to local reports directory
            local_file_path = os.path.join(local_reports_dir, f"{customer_id}.pdf")
            shutil.copy2(file_path, local_file_path)
            
            # Store metadata in database (without PDF data)
            self.db.conn.execute("""
                INSERT OR REPLACE INTO pdf_reports (
                    customer_id, 
                    file_name, 
                    file_data, 
                    file_size, 
                    company_name,
                    created_at,
                    storage_type
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'local')
            """, [customer_id, file_name, "", file_size, company_name])
            
            # Store metadata
            self.db.store_report_metadata(customer_id, file_name, file_size, company_name)
            
            logger.info(f"Stored PDF locally for {customer_id}: {file_name} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error storing PDF locally for {customer_id}: {e}")
            return False
    
    def get_pdf(self, customer_id: str) -> Optional[bytes]:
        """
        Retrieve PDF file from MotherDuck database or local storage
        
        Args:
            customer_id: Customer ID
            
        Returns:
            PDF data as bytes, or None if not found
        """
        try:
            result = self.db.conn.execute("""
                SELECT file_data, storage_type FROM pdf_reports 
                WHERE customer_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, [customer_id]).fetchone()
            
            if result:
                file_data, storage_type = result
                
                if storage_type == 'local':
                    # Read from local file
                    local_file_path = os.path.join("reports", f"{customer_id}.pdf")
                    if os.path.exists(local_file_path):
                        with open(local_file_path, 'rb') as f:
                            pdf_data = f.read()
                        logger.info(f"Retrieved PDF locally for {customer_id}")
                        return pdf_data
                    else:
                        logger.warning(f"Local PDF file not found for {customer_id}")
                        return None
                else:
                    # Decode from base64 (MotherDuck storage)
                    if file_data:
                        pdf_data = base64.b64decode(file_data)
                        logger.info(f"Retrieved PDF from MotherDuck for {customer_id}")
                        return pdf_data
                    else:
                        logger.warning(f"No PDF data in MotherDuck for {customer_id}")
                        return None
            
            logger.warning(f"No PDF found for customer {customer_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving PDF for {customer_id}: {e}")
            return None
    
    def get_pdf_metadata(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get PDF metadata for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            PDF metadata dictionary, or None if not found
        """
        try:
            result = self.db.conn.execute("""
                SELECT file_name, file_size, created_at, company_name
                FROM pdf_reports 
                WHERE customer_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, [customer_id]).fetchone()
            
            if result:
                return {
                    'file_name': result[0],
                    'file_size': result[1],
                    'created_at': result[2],
                    'company_name': result[3]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting PDF metadata for {customer_id}: {e}")
            return None
    
    def list_company_reports(self, company_name: str) -> list:
        """
        List all reports for a company
        
        Args:
            company_name: Company name
            
        Returns:
            List of report metadata
        """
        try:
            result = self.db.conn.execute("""
                SELECT customer_id, file_name, file_size, created_at
                FROM pdf_reports 
                WHERE company_name = ?
                ORDER BY created_at DESC
            """, [company_name]).fetchall()
            
            reports = []
            for row in result:
                reports.append({
                    'customer_id': row[0],
                    'file_name': row[1],
                    'file_size': row[2],
                    'created_at': row[3]
                })
            
            return reports
            
        except Exception as e:
            logger.error(f"Error listing reports for {company_name}: {e}")
            return []
    
    def delete_pdf(self, customer_id: str) -> bool:
        """
        Delete PDF for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.db.conn.execute("""
                DELETE FROM pdf_reports WHERE customer_id = ?
            """, [customer_id])
            
            logger.info(f"Deleted PDF for {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting PDF for {customer_id}: {e}")
            return False

# Global PDF storage instance
pdf_storage = None

def get_pdf_storage() -> PDFStorage:
    """Get PDF storage instance (singleton pattern)"""
    global pdf_storage
    if pdf_storage is None:
        pdf_storage = PDFStorage()
    return pdf_storage
