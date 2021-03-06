"""
PyCharm sets PythonPath to the root folder, VSC does not by default - imports fail
Hence, add this to the launch config:
"env": {"PYTHONPATH": "${workspaceFolder}:${env:PYTHONPATH}"}

ref: https://stackoverflow.com/questions/53653083/how-to-correctly-set-pythonpath-for-visual-studio-code
"""

import os
import sys
from datetime import datetime

from sqlalchemy import inspect

cwd = os.getcwd()   # eg, /Users/val/python/pycharm/logic-bank/nw/tests
required_path_python_rules = cwd  # seeking /Users/val/python/pycharm/logic-bank
required_path_python_rules = required_path_python_rules.replace("/nw/tests", "")
required_path_python_rules = required_path_python_rules.replace("\\nw\\tests", "")

sys_path = ""
required_path_present = False
for each_node in sys.path:
    sys_path += each_node + "\n"
    if each_node == required_path_python_rules:
        required_path_present = True

if not required_path_present:
    print("Fixing path (so can run from terminal)")
    sys.path.append(required_path_python_rules)
else:
    pass
    print("NOT Fixing path (default PyCharm, set in VSC Launch Config)")

run_environment_info = "Run Environment info...\n\n"
run_environment_info += " Current Working Directory: " + cwd + "\n\n"
run_environment_info += "sys.path: (Python imports)\n" + sys_path + "\n"
run_environment_info += "From: " + sys.argv[0] + "\n\n"
run_environment_info += "Using Python: " + sys.version + "\n\n"
run_environment_info += "At: " + str(datetime.now()) + "\n\n"

print("\n" + run_environment_info + "\n\n")

from nw.tests import setup_db  # careful - this must follow fix-path, above
setup_db()

import nw.db.models as models
from logic_bank.exec_row_logic.logic_row import LogicRow
from logic_bank.util import prt
from nw.logic import session  # opens db, activates logic listener <--

def toggle_order_shipped():
    """ toggle Shipped Date, to trigger balance adjustment """

    pre_cust = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()
    pre_adjusted_product = session.query(models.Product).filter(models.Product.Id == 58).one()
    session.expunge(pre_cust)
    session.expunge(pre_adjusted_product)

    print("")
    test_order = session.query(models.Order).filter(models.Order.Id == 11011).join(models.Employee).one()
    if test_order.ShippedDate is None or test_order.ShippedDate == "":
        test_order.ShippedDate = str(datetime.now())
        print(prt("Shipping order - ShippedDate: ['' -> " + test_order.ShippedDate + "]"))
    else:
        test_order.ShippedDate = None
        print(prt("Returning order - ShippedDate: [ -> None]"))
    insp = inspect(test_order)
    session.commit()

    print("")
    post_cust = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()
    logic_row = LogicRow(row=post_cust, old_row=pre_cust, ins_upd_dlt="*", nest_level=0, a_session=session, row_sets=None)

    if abs(post_cust.Balance - pre_cust.Balance) == 960:
        logic_row.log("Correct adjusted Customer Result")
        assert True
    else:
        logic_row.log(post_cust, "ERROR - incorrect adjusted Customer Result")
        assert False

    if post_cust.Balance == 0:
        pass
    else:
        logic_row.log("ERROR - balance should be 0")
        assert False

    if post_cust.UnpaidOrderCount == 2 and pre_cust.UnpaidOrderCount == 3:
        pass
    else:
        logic_row.log("Error - UnpaidOrderCount should be 2")
        assert False

    post_adjusted_product = session.query(models.Product).filter(models.Product.Id == 58).one()
    logic_row = LogicRow(row=post_adjusted_product, old_row=pre_adjusted_product, ins_upd_dlt="*", nest_level=0,
                         a_session=session, row_sets=None)
    if post_adjusted_product.UnitsShipped == pre_adjusted_product.UnitsShipped + 40:
        logic_row.log("Product adjusted properly on ship order")
    else:
        logic_row.log("Product adjusted improperly on ship order")
        assert False


toggle_order_shipped()
pre_adjusted_product = session.query(models.Product).filter(models.Product.Id == 58).one()
session.expunge(pre_adjusted_product)
print("\ndlt_order, shipped... now delete")
delete_cust = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()
session.delete(delete_cust)
session.commit()

post_adjusted_product = session.query(models.Product).filter(models.Product.Id == 58).one()
logic_row = LogicRow(row=post_adjusted_product, old_row=pre_adjusted_product, ins_upd_dlt="*", nest_level=0, a_session=session, row_sets=None)
if post_adjusted_product.UnitsShipped == pre_adjusted_product.UnitsShipped - 40:
    logic_row.log("Product adjusted properly on delete customer")
else:
    logic_row.log("Product adjusted improperly on delete customer")
    assert False

print("\ndlt_order, shipped... deleted - check log")


