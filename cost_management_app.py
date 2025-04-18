import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime
import calendar
import warnings
import io
warnings.filterwarnings('ignore')

class CostManagementDB:
    def __init__(self):
        self.db_name = 'cost_management.db'
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        # Updated Recipes Table with more detailed fields
        c.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT,
                item_name TEXT,
                category TEXT,
                selling_price REAL,
                cost_price REAL,
                cost_percentage REAL,
                ingredients TEXT,
                preparation TEXT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Other existing tables remain the same
        c.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                store TEXT,
                item_group TEXT,
                item_code TEXT,
                item_name TEXT,
                uom TEXT,
                qty REAL,
                rate REAL,
                value REAL,
                cost_center TEXT,
                user TEXT,
                hotel TEXT,
                month TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item_code TEXT,
                item_name TEXT,
                quantity REAL,
                rate REAL,
                value REAL,
                discount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def process_and_store_recipe_data(self, df):
        """Process and store recipe data with validation"""
        try:
            # Basic data cleaning
            df = df.fillna('')

            # Ensure required columns exist
            required_columns = ['Item Code', 'Item Name', 'Selling Price', 'Cost Price']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

            # Calculate cost percentage if not present
            if 'Cost Percentage' not in df.columns:
                df['Cost Percentage'] = (df['Cost Price'] / df['Selling Price']) * 100

            # Prepare data for database
            df_to_store = df.rename(columns={
                'Item Code': 'item_code',
                'Item Name': 'item_name',
                'Selling Price': 'selling_price',
                'Cost Price': 'cost_price',
                'Cost Percentage': 'cost_percentage'
            })

            # Add timestamp
            df_to_store['last_updated'] = datetime.now()

            conn = self.get_connection()
            df_to_store.to_sql('recipes', conn, if_exists='append', index=False)
            conn.close()
            return True, "Recipe data successfully stored"
        except Exception as e:
            return False, f"Error storing recipe data: {str(e)}"

    def get_recipe_data(self):
        """Fetch recipe data with error handling"""
        try:
            conn = self.get_connection()
            df = pd.read_sql_query("""
                SELECT
                    item_code,
                    item_name,
                    category,
                    selling_price,
                    cost_price,
                    cost_percentage,
                    last_updated
                FROM recipes
                ORDER BY last_updated DESC
            """, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error fetching recipe data: {str(e)}")
            return pd.DataFrame()

class CostManagementApp:
    def __init__(self):
        st.set_page_config(page_title="Cost Management Dashboard", layout="wide")
        self.db = CostManagementDB()

    def main(self):
        st.title("Cost Management Dashboard")

        # Sidebar for navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Select Page",
            ["Overview", "Data Management", "Cost Analysis", "Recipe Management", "Reports"])

        if page == "Overview":
            self.show_overview_page()
        elif page == "Data Management":
            self.show_data_management_page()
        elif page == "Cost Analysis":
            self.show_cost_analysis_page()
        elif page == "Recipe Management":
            self.show_recipe_management_page()
        elif page == "Reports":
            self.show_reports_page()

    def process_uploaded_file(self, uploaded_file, file_type):
        """Process uploaded files with proper error handling"""
        try:
            if uploaded_file is None:
                return None, "No file uploaded"

            # Read the file based on its type
            if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
                df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                return None, "Unsupported file format. Please upload Excel or CSV files."

            # Basic data validation
            if df.empty:
                return None, "Uploaded file is empty"

            # Process based on file type
            if file_type == "recipe":
                success, message = self.db.process_and_store_recipe_data(df)
                if not success:
                    return None, message
                return df, "Recipe data successfully processed and stored"

            return df, "File successfully processed"

        except Exception as e:
            return None, f"Error processing file: {str(e)}"

    def show_recipe_management_page(self):
        st.header("Recipe Management")

        # File upload section
        st.subheader("Upload Recipe Data")
        uploaded_file = st.file_uploader("Upload Recipe File (Excel or CSV)",
                                       type=['xlsx', 'xls', 'csv'])

        if uploaded_file is not None:
            df, message = self.process_uploaded_file(uploaded_file, "recipe")
            if df is not None:
                st.success(message)
            else:
                st.error(message)

        # Display existing recipes
        st.subheader("Existing Recipes")
        recipe_df = self.db.get_recipe_data()

        if not recipe_df.empty:
            # Recipe filters
            col1, col2 = st.columns(2)
            with col1:
                selected_recipe = st.selectbox("Select Recipe",
                    recipe_df['item_name'].unique())

            # Display recipe details
            recipe_details = recipe_df[recipe_df['item_name'] == selected_recipe]
            if not recipe_details.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Selling Price",
                             f"{recipe_details['selling_price'].iloc[0]:,.0f} MMK")
                with col2:
                    st.metric("Cost Price",
                             f"{recipe_details['cost_price'].iloc[0]:,.0f} MMK")
                with col3:
                    st.metric("Cost Percentage",
                             f"{recipe_details['cost_percentage'].iloc[0]:.2f}%")

                # Display full recipe data
                st.subheader("Recipe Details")
                st.dataframe(recipe_details)

        else:
            st.info("No recipe data available. Please upload recipe data using the form above.")

if __name__ == "__main__":
    app = CostManagementApp()
    app.main()
