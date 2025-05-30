from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal

class Ticket(BaseModel):
    id: str = Field(description='Ticket identifier')
    category_1: str = Field(description='Ticket first level category')
    category_2: str = Field(description='Ticket second level category')
    category_3: str = Field(description='Ticket third level category')
    status: str = Field(description='Ticket status')
    created_by: str = Field(description='Ticket creator role')
    eic: str = Field('external identification code')
    email: str = Field('customer email')
    request_content: str = Field(description='Customer claim')
    response_content: Optional[str] = Field(description='Response to the customer claim', default=None)

class Address(BaseModel):
    street: str = Field(description='Street')
    house_number: str = Field(description='House number')
    city: str = Field(description='City name')
    zip_code: str = Field(description='Zip code')
    country: str = Field(description='Country')

class Customer(BaseModel):
    customer_id: str = Field(description='Customer identifier')
    first_name: str = Field(description='Customer first name')
    last_name: str = Field(description='Customer last name')
    id_card_num: str = Field(description='Customer identification card number')
    permanent_residence_address: Address = Field(description='Customer permanent residence address')
    contact_address: Optional[Address] = Field(description='Customer contact address. If empty, use permanent residence address', default=None)
    email: str = Field(description='Customer email')
    phone: str = Field(description='Customer phone number')

class ConsumptionPoint(BaseModel):
    consumption_point_id: str = Field(description='Consumption point identifier')
    customer_id: str = Field('Active customer identifier for the consumption point')
    product_family: str = Field(description='Family of products - "electricity" or "gas"')
    contract_id: Optional[str] = Field(description='Active contract id for the consumption point', default=None)
    address: Address = Field(description='Consumption point address')

class Contract(BaseModel):
    contract_id: str = Field(description='Contract identifier')
    customer_id: str = Field(description='Customer identifier on the contract')
    consumption_point: str = Field(description='Contract consumption point')
    product_id: str = Field(description='Product identifier')
    point_of_sale: str = Field(description='Point of sale where the contract was closed')
    sales_person_id: Optional[str] = Field(description='Sales person identifier', default=None)
    customer_sign_date: str = Field(description='Date of the contract signature by customer in ISO format')
    start_date: str = Field(description='Contract start date in ISO format')
    end_date: Optional[str] = Field(description='Contract end date in ISO format', default=None)
    advance_payment_amount: str = Field(description='Advance payment amount')

class Payment(BaseModel):
    payment_id: str = Field(description='Payment identifier')
    contract_id: str = Field(description='Contract identifier')
    payer_account: str = Field(description='Payer account number')
    payee_account: str = Field(description='Payee account number')
    due_amount: str = Field(description='Due amount')
    actual_amount: str = Field(description='Actual payed amount')
    due_date: str = Field(description='Payment due date in ISO format')
    actual_payment_date: Optional[str] = Field(description='Actual payment date in ISO format', default=None)
    variable_symbol: str = Field(description='Payment variable symbol')
    constant_symbol: str = Field(description='Payment constant symbol')
    specific_symbol: str = Field(description='Payment specific symbol')
    message: Optional[str] = Field(description='Message for the payee', default=None)