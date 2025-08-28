# 24. From customer wish to test automation
*Pages 78-79*
## Page 78
From Customer Wish to Test Automation - The Basics Chapter 5 [ 63 ] From customer wish to test automation Our customer wishes to extend standard Dynamics 365 Business Central with an elementary feature: the addition of a lookup field to the Customer table to be populated by the user.
This field has to be carried over to the whole bunch of sales documents and also needs to be included in the warehouse shipping. Data model Even though the purpose of such a field will be very specific, we will generically name it Lookup Value Code.
As with any other lookup field in Business Central, this Lookup Value Code field will have a table relation (foreign key) with another table, in our case a new table called Lookup Value. The following relational diagram schematically describes the data model of this new feature, with the new table in the middle and the extended standard tables on the left and right sides: The Lookup Value Code field has to be editable on all tables except for the posted document header tables, that is, Sales Shipment Header, Sales Invoice Header, Sales Cr.Memo Header, Return Receipts Header, and Posted Whse.
Shipment Line. 

## Page 79
From Customer Wish to Test Automation - The Basics Chapter 5 [ 64 ] Business logic In compliance with standard Business Central behavior, the following business logic applies: When creating a customer from a customer template, the Lookup Value Code field should be inherited from Customer Template to Customer When selecting a customer in the Sell-to Customer field on a sales document, the Lookup Value Code field should be inherited from the Customer to Sales Header When posting a sales document, it is mandatory that the Lookup Value Code field is populated When posting a sales document, the Lookup Value Code field should be inherited from Sales Header to the header of the posted document.
That is, Sales Shipment Header Sales Invoice Header Sales Cr.Memo Header Return Receipt Header When archiving a sales document, the Lookup Value Code field should be inherited from Sales Header to Sales Header Archive When creating a warehouse shipment from a sales order, the Lookup Value Code field should be inherited from Sales Header to Warehouse Shipment Line When posting a warehouse shipment, the Lookup Value Code field should be inherited from Warehouse Shipment Line to Posted Whse.
Shipment Line LookupValue extension Based on these requirements, the LookupValue extension will be built, including automated tests. 

---
**Chapter Statistics:**
- Pages: 2
- Words: ~408
