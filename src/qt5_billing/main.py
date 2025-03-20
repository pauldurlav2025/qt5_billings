import os
import sys
import mysql.connector
from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox, QSplashScreen, QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QFont, QPalette, QPixmap

PROG_PATH               = __file__.replace(os.path.basename(__file__), '')
ICON_PATH               = os.path.join(PROG_PATH, "media", "icons")
PROGRAM_ICON_PATH       = os.path.join(ICON_PATH, "qt5-billing-application.png")

HOST_NAME = "localhost"
USER = "root"
PASSWORD = ""
DATABASE_NAME = "infoware_billing_system"

TABLE_NAME = "infoware_customer_bills"


class BillingForm(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Infoware Billing Form')

        self.db = mysql.connector.connect(
            host=HOST_NAME,     
            user=USER,          
            password=PASSWORD,  
            database=DATABASE_NAME  
        )
        self.cursor = self.db.cursor()

        self.layout = QVBoxLayout()

        self.customer_name_label = QLabel("Customer Name:")
        self.customer_name_input = QLineEdit()
        self.layout.addWidget(self.customer_name_label)
        self.layout.addWidget(self.customer_name_input)

        self.fetch_bills_button = QPushButton("Show Bills")
        self.fetch_bills_button.clicked.connect(self.show_bills_for_company)
        self.layout.addWidget(self.fetch_bills_button)

        self.product_description_label = QLabel("Product Description:")
        self.product_description_input = QLineEdit()
        self.layout.addWidget(self.product_description_label)
        self.layout.addWidget(self.product_description_input)

        self.quantity_label = QLabel("Quantity:")
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1000)  # Set range for quantity
        self.layout.addWidget(self.quantity_label)
        self.layout.addWidget(self.quantity_input)

        self.price_label = QLabel("Price per Unit:")
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.01, 10000.00)  # Set range for price per unit
        self.price_input.setDecimals(2)  # Set number of decimals for price
        self.layout.addWidget(self.price_label)
        self.layout.addWidget(self.price_input)

        self.add_button = QPushButton("Add to Bill")
        self.add_button.clicked.connect(self.add_to_bill)
        self.layout.addWidget(self.add_button)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Product Description", "Quantity", "Price per Unit", "Total"])
        self.layout.addWidget(self.table)

        self.total_label = QLabel("Total: ₹0.00")
        self.layout.addWidget(self.total_label)

        self.finalize_button = QPushButton("Finalize Billing")
        self.finalize_button.clicked.connect(self.finalize_billing)
        self.layout.addWidget(self.finalize_button)

        self.setLayout(self.layout)


    def show_bills_for_company(self):
        company_name = self.customer_name_input.text()
        if company_name:
            fetch_bills_query = f"""
                SELECT bill_id, customer_name, product_description, quantity, price_per_unit, total
                FROM {TABLE_NAME}
                WHERE customer_name LIKE %s
            """
            self.cursor.execute(fetch_bills_query, (f"%{company_name}%",))
            bills = self.cursor.fetchall()

            self.table.setRowCount(0)

            for bill in bills:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for i in range(2, 6):
                    self.table.setItem(row_position, i-2, QTableWidgetItem(str(bill[i])))

            print(f"Fetched {len(bills)} bills for company: {company_name}")
        else:
            print("Please enter a company name.")        

    def add_to_bill(self):
        product_description = self.product_description_input.text()
        quantity = self.quantity_input.text()
        price = self.price_input.text()

        if product_description and quantity.isdigit() and price.replace('.', '', 1).isdigit():
            quantity = int(quantity)
            price = float(price)
            total = quantity * price

            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            self.table.setItem(row_position, 0, QTableWidgetItem(product_description))
            self.table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
            self.table.setItem(row_position, 2, QTableWidgetItem(f"₹{price:.2f}"))
            self.table.setItem(row_position, 3, QTableWidgetItem(f"₹{total:.2f}"))

            self.update_total()

        self.product_description_input.clear()
        self.quantity_input.clear()
        self.price_input.clear()

    def update_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            total += float(self.table.item(row, 3).text().strip('₹'))
        self.total_label.setText(f"Total: ₹{total:.2f}")

    def finalize_billing(self):
        customer_name = self.customer_name_input.text()
        if customer_name and self.table.rowCount() > 0:
            total = self.total_label.text()
            print(f"Billing for {customer_name}:\n{total}")
            
            self.insert_bill(customer_name, total)

            for row in range(self.table.rowCount()):
                product_description = self.table.item(row, 0).text()
                quantity = int(self.table.item(row, 1).text())
                price = float(self.table.item(row, 2).text().strip('₹'))
                item_total = float(self.table.item(row, 3).text().strip('₹'))

                self.insert_item(customer_name, product_description, quantity, price, item_total)

            print("Bill finalized and saved to database.")
        else:
            print("Please fill in all the details and add items to the bill.")

    def insert_bill(
        self, 
        customer_name, 
        total
    ):
        insert_bill_query = f"""
            INSERT INTO {TABLE_NAME} (customer_name, product_description, quantity, price_per_unit, total)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_bill_query, (customer_name, "N/A", 0, 0, total))
        self.db.commit()

    def insert_item(
        self, 
        customer_name, 
        product_description, 
        quantity, 
        price, 
        item_total
    ):
        insert_item_query = f"""
            INSERT INTO {TABLE_NAME} (customer_name, product_description, quantity, price_per_unit, total)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_item_query, (customer_name, product_description, quantity, price, item_total))
        self.db.commit()

def main():
    billing_application = QApplication(sys.argv)
    billing_application.setWindowIcon(QIcon(PROGRAM_ICON_PATH))

    splash_screen = QSplashScreen(QPixmap(PROGRAM_ICON_PATH))
    splash_screen.show()

    billing_application_window = BillingForm() # Most time is consumed here.
    billing_application_window.setWindowTitle("Infoware Billing Program")
    splash_screen.finish(billing_application_window)

    billing_application_window.show()    
    sys.exit(billing_application.exec_())


if __name__ == '__main__':
    main()
