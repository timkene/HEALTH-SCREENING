#!/usr/bin/env python3
"""
Database Configuration for MotherDuck Integration
Handles customer data and PDF report storage in the cloud
"""

import os
import duckdb
import pandas as pd
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MotherDuckDB:
    def __init__(self, token: Optional[str] = None):
        """
        Initialize MotherDuck connection
        
        Args:
            token: MotherDuck API token (can be set via environment variable)
        """
        self.token = token or os.environ.get('MOTHERDUCK_TOKEN')
        if not self.token:
            raise ValueError("MotherDuck token is required. Set MOTHERDUCK_TOKEN environment variable.")
        
        # Connect to MotherDuck (create database if it doesn't exist)
        try:
            self.conn = duckdb.connect(f"md:health_screening?motherduck_token={self.token}")
        except Exception as e:
            # If database doesn't exist, create it first
            print(f"Creating database 'health_screening' in MotherDuck...")
            self.conn = duckdb.connect(f"md:?motherduck_token={self.token}")
            self.conn.execute("CREATE DATABASE health_screening")
            self.conn.close()
            # Now connect to the created database
            self.conn = duckdb.connect(f"md:health_screening?motherduck_token={self.token}")
        
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Create customers table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    email VARCHAR NOT NULL,
                    phone VARCHAR NOT NULL,
                    report_file_name VARCHAR NOT NULL,
                    company_name VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create reports table for storing PDF metadata
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id VARCHAR PRIMARY KEY,
                    customer_id VARCHAR NOT NULL,
                    report_name VARCHAR NOT NULL,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    company_name VARCHAR,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            
            # Create companies table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    total_staff INTEGER,
                    screening_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create PDF reports table for storing actual PDF data
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS pdf_reports (
                    id VARCHAR PRIMARY KEY,
                    customer_id VARCHAR NOT NULL,
                    file_name VARCHAR NOT NULL,
                    file_data TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    company_name VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def store_customers_from_excel(self, excel_file_path: str, company_name: str) -> int:
        """
        Store customer data from Excel file into MotherDuck
        
        Args:
            excel_file_path: Path to Excel file
            company_name: Name of the company
            
        Returns:
            Number of customers stored
        """
        try:
            # Read Excel file
            df = pd.read_excel(excel_file_path)
            
            # Prepare customer data
            customers_data = []
            for _, row in df.iterrows():
                enrollee_id = str(row['ENROLLEE ID']).strip()
                name = str(row['NAME']).strip()
                email = str(row['EMAIL']).strip().lower()
                phone = str(row['TEL NO']).strip()
                
                # Clean enrollee ID for filename compatibility
                clean_enrollee_id = enrollee_id.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                report_file_name = f"{clean_enrollee_id}.pdf"
                
                customers_data.append({
                    'id': enrollee_id,
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'report_file_name': report_file_name,
                    'company_name': company_name
                })
            
            # Convert to DataFrame and insert
            customers_df = pd.DataFrame(customers_data)
            
            # Insert or update customers
            self.conn.execute("""
                INSERT OR REPLACE INTO customers (id, name, email, phone, report_file_name, company_name, updated_at)
                SELECT id, name, email, phone, report_file_name, company_name, CURRENT_TIMESTAMP
                FROM customers_df
            """, {"customers_df": customers_df})
            
            logger.info(f"Stored {len(customers_data)} customers for {company_name}")
            return len(customers_data)
            
        except Exception as e:
            logger.error(f"Error storing customers: {e}")
            raise
    
    def store_report_metadata(self, customer_id: str, report_name: str, file_size: int, company_name: str):
        """
        Store PDF report metadata
        
        Args:
            customer_id: Customer ID
            report_name: Name of the report file
            file_size: Size of the PDF file in bytes
            company_name: Company name
        """
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO reports (id, customer_id, report_name, file_size, company_name)
                VALUES (?, ?, ?, ?, ?)
            """, [f"{customer_id}_{report_name}", customer_id, report_name, file_size, company_name])
            
            logger.info(f"Stored report metadata for {customer_id}: {report_name}")
            
        except Exception as e:
            logger.error(f"Error storing report metadata: {e}")
            raise
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer data by ID"""
        try:
            result = self.conn.execute("""
                SELECT id, name, email, phone, report_file_name, company_name
                FROM customers 
                WHERE id = ?
            """, [customer_id]).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'email': result[2],
                    'phone': result[3],
                    'report_file_name': result[4],
                    'company_name': result[5]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {e}")
            return None
    
    def verify_customer(self, customer_id: str, email: str, phone: str) -> Optional[Dict[str, Any]]:
        """
        Verify customer credentials
        
        Args:
            customer_id: Customer ID
            email: Email address
            phone: Phone number
            
        Returns:
            Customer data if verified, None otherwise
        """
        try:
            # Normalize phone number
            phone_normalized = phone[1:] if phone.startswith('0') else phone
            
            result = self.conn.execute("""
                SELECT id, name, email, phone, report_file_name, company_name
                FROM customers 
                WHERE id = ? AND LOWER(email) = LOWER(?)
            """, [customer_id, email]).fetchone()
            
            if result:
                stored_phone = result[3]
                stored_phone_normalized = stored_phone[1:] if stored_phone.startswith('0') else stored_phone
                
                # Check phone match (with or without leading 0)
                if (stored_phone == phone or stored_phone_normalized == phone_normalized):
                    return {
                        'id': result[0],
                        'name': result[1],
                        'email': result[2],
                        'phone': result[3],
                        'report_file_name': result[4],
                        'company_name': result[5]
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error verifying customer {customer_id}: {e}")
            return None
    
    def get_all_customers(self, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all customers, optionally filtered by company"""
        try:
            if company_name:
                result = self.conn.execute("""
                    SELECT id, name, email, phone, report_file_name, company_name
                    FROM customers 
                    WHERE company_name = ?
                    ORDER BY name
                """, [company_name]).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT id, name, email, phone, report_file_name, company_name
                    FROM customers 
                    ORDER BY name
                """).fetchall()
            
            customers = []
            for row in result:
                customers.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'report_file_name': row[4],
                    'company_name': row[5]
                })
            
            return customers
            
        except Exception as e:
            logger.error(f"Error getting customers: {e}")
            return []
    
    def store_company_info(self, company_name: str, total_staff: int, screening_date: str = None):
        """Store company information"""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO companies (id, name, total_staff, screening_date)
                VALUES (?, ?, ?, ?)
            """, [company_name.replace(' ', '_').lower(), company_name, total_staff, screening_date])
            
            logger.info(f"Stored company info for {company_name}")
            
        except Exception as e:
            logger.error(f"Error storing company info: {e}")
            raise
    
    def get_company_stats(self, company_name: str) -> Dict[str, Any]:
        """Get company statistics"""
        try:
            # Get customer count
            customer_count = self.conn.execute("""
                SELECT COUNT(*) FROM customers WHERE company_name = ?
            """, [company_name]).fetchone()[0]
            
            # Get report count
            report_count = self.conn.execute("""
                SELECT COUNT(*) FROM reports WHERE company_name = ?
            """, [company_name]).fetchone()[0]
            
            return {
                'company_name': company_name,
                'customer_count': customer_count,
                'report_count': report_count
            }
            
        except Exception as e:
            logger.error(f"Error getting company stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

# Global database instance
db_instance = None

def get_db() -> MotherDuckDB:
    """Get database instance (singleton pattern)"""
    global db_instance
    if db_instance is None:
        db_instance = MotherDuckDB()
    return db_instance

def close_db():
    """Close database connection"""
    global db_instance
    if db_instance:
        db_instance.close()
        db_instance = None
