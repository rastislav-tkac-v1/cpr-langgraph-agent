from fastapi import FastAPI
from typing import Optional, List
from mock_server.models import Address, Customer, ConsumptionPoint, Contract, Payment
import datetime

app = FastAPI(title="Mock REST server")

# fake endpoints ----------------------------------------
@app.get("/customers/by_email")
def get_customer_by_email(email: str) -> Customer:
    return Customer(
        customer_id='123456789',
        first_name='Karel',
        last_name='Vomáčka',
        id_card_num='AB987654321',
        permanent_residence_address=Address(
            street='Bedřicha Smetany',
            house_number='987',
            city='Praha 4',
            zip_code='14000',
            country='Czech Republic'
        ),
        contact_address=Address(
            street='Antonína Dvořáka',
            house_number='654',
            city='Praha 5',
            zip_code='15000',
            country='Czech Republic'
        ),
        email='kare.vomacka@testmail.test',
        phone='+420987654321'
    )

@app.get("/customers/{customer_id}/consumption_points")
def get_customer_consumption_points(customer_id: str, product_family: Optional[str] = None) -> List[ConsumptionPoint]:
    response = []
    if product_family == 'electricity' or (not product_family):
        response.append(ConsumptionPoint(
            consumption_point_id='EL654987321',
            customer_id=customer_id,
            product_family='electricity',
            contract_id='ELC321654897',
            address=Address(
                street='Antonína Dvořáka',
                house_number='654',
                city='Praha 5',
                zip_code='15000',
                country='Czech Republic'
            )
        ))
    if product_family == 'gas' or (not product_family):
        response.append(ConsumptionPoint(
            consumption_point_id='G655498736',
            customer_id=customer_id,
            product_family='gas',
            contract_id='GC546763133',
            address=Address(
                street='Antonína Dvořáka',
                house_number='654',
                city='Praha 5',
                zip_code='15000',
                country='Czech Republic'
            )
        ))
    return response

@app.get("/customers/{customer_id}/contracts")
def get_customer_contracts(customer_id: str) -> List[Contract]:
    return [
        Contract(
            contract_id='ELC321654897',
            customer_id=customer_id,
            consumption_point='EL654987321',
            product_id='ELEKTRINA_FIX_1R',
            point_of_sale='ZC_PRG_4',
            sales_person_id='ZAM_654321474',
            customer_sign_date=datetime.date(2024,4,16),
            start_date=datetime.date(2024,10,1),
            end_date=datetime.date(2025,10,1),
            advance_payment_amount=1500,
        ),
        Contract(
            contract_id='GC546763133',
            customer_id=customer_id,
            consumption_point='G655498736',
            product_id='PLYN_FIX_2R',
            point_of_sale='ZC_PRG_4',
            sales_person_id='ZAM_654321474',
            customer_sign_date=datetime.date(2024,4,16),
            start_date=datetime.date(2024,5,1),
            end_date=datetime.date(2026,5,1),
            advance_payment_amount=1500,
        )
    ]

@app.get("/customers/customer/{customer_id}/contracts/{contract_id}/payments")
def get_customer_contract_payments(customer_id: str, contract_id: str) -> List[Payment]:
    if contract_id == 'ELC321654897':
        return [
            Payment(
                payment_id='3546687321354',
                contract_id=contract_id,
                payer_account='6546-7324638735/1234',
                payee_account='3548-6387321169/4321',
                due_amount='1500',
                actual_amount='500',
                due_date=datetime(2025,4,15),
                actual_payment_date=datetime(2025,4,5),
                variable_symbol=contract_id,
                constant_symbol='0123',
                specific_symbol='65498',
                message='Záloha na elektřinu' 
            ),
            Payment(
                payment_id='3546687321354',
                contract_id=contract_id,
                payer_account='6546-7324638735/1234',
                payee_account='3548-6387321169/4321',
                due_amount='1500',
                actual_amount='500',
                due_date=datetime(2025,3,15),
                actual_payment_date=datetime(2025,3,5),
                variable_symbol=contract_id,
                constant_symbol='0123',
                specific_symbol='65498',
                message='Záloha na elektřinu' 
            ),
            Payment(
                payment_id='3546687321354',
                contract_id=contract_id,
                payer_account='6546-7324638735/1234',
                payee_account='3548-6387321169/4321',
                due_amount='1500',
                actual_amount='500',
                due_date=datetime(2025,2,15),
                actual_payment_date=datetime(2025,2,5),
                variable_symbol=contract_id,
                constant_symbol='0123',
                specific_symbol='65498',
                message='Záloha na elektřinu' 
            )
        ]
    elif contract_id == 'GC546763133':
        return [
            Payment(
                payment_id='3546687321354',
                contract_id=contract_id,
                payer_account='6546-7324638735/1234',
                payee_account='3548-6387321169/4321',
                due_amount='1500',
                actual_amount='500',
                due_date=datetime(2025,4,15),
                actual_payment_date=datetime(2025,4,5),
                variable_symbol=contract_id,
                constant_symbol='0123',
                specific_symbol='65498',
                message='Záloha na plyn' 
            ),
            Payment(
                payment_id='3546687321354',
                contract_id=contract_id,
                payer_account='6546-7324638735/1234',
                payee_account='3548-6387321169/4321',
                due_amount='1500',
                actual_amount='500',
                due_date=datetime(2025,3,15),
                actual_payment_date=datetime(2025,3,5),
                variable_symbol=contract_id,
                constant_symbol='0123',
                specific_symbol='65498',
                message='Záloha na plyn' 
            ),
            Payment(
                payment_id='3546687321354',
                contract_id=contract_id,
                payer_account='6546-7324638735/1234',
                payee_account='3548-6387321169/4321',
                due_amount='1500',
                actual_amount='500',
                due_date=datetime(2025,2,15),
                actual_payment_date=datetime(2025,2,5),
                variable_symbol=contract_id,
                constant_symbol='0123',
                specific_symbol='65498',
                message='Záloha na plyn' 
            )
        ]
    else:
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mock_server.app:app", host="0.0.0.0", port=9000, reload=False)
