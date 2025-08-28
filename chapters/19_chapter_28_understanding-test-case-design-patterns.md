# 19. Understanding test case design patterns
*Pages 68-70*
## Page 68
Test Design Chapter 4 [ 53 ] Understanding test case design patterns Goal: Learn the basic patterns for designing tests. If you have been testing software, you might know that each test has a similar overall structure.
Before you can perform the action under test, for example, the posting of a document, first, the data needs to be set up. Then, the action will be exercised. And finally, the result of the action has to be verified.
In some cases, a fourth phase applies, a so-called teardown, which is used to revert the system under test to its previous state. The four phases of a test case design pattern are listed as follows: Set up Exercise Verify Teardown For a short and clear description of the four-phase design pattern, please refer to the following link: http:/​/​robots.​thoughtbot.​com/​four-​phase-​test This design pattern was typically the pattern used by Microsoft in the early years of C/SIDE test coding.
Like the following test function example, taken from codeunit 137295 - SCM Inventory Misc. III, you will encounter it in a vast number of older test codeunits: [Test] PstdSalesInvStatisticsWithSalesPrice() // Verify Amount on Posted Sales Invoice Statistics // after posting Sales Order.
// Setup: Create Sales Order, define Sales Price on Customer Initialize(); CreateSalesOrderWithSalesPriceOnCustomer(SalesLine, WorkDate()); LibraryVariableStorage.Enqueue(SalesLine."Line Amount"); // Enqueue for SalesInvoiceStatisticsPageHandler.
// Exercise: Post Sales Order. DocumentNo:= PostSalesDocument(SalesLine, true); // TRUE for Invoice. // Verify: Verify Amount on Posted Sales Invoice Statistics. // Verification done in SalesInvoiceStatisticsPageHandler PostedSalesInvoice.OpenView; PostedSalesInvoice.Filter.SetFilter("No.", DocumentNo); PostedSalesInvoice.Statistics.Invoke();.
![Image from page 68](../diagrams/page_68_img_67.png)
## Page 69
Test Design Chapter 4 [ 54 ] Acceptance Test-Driven Development Nowadays, Microsoft uses the Acceptance Test-Driven Development (ATDD) design pattern. This is a more complete structure and closer to the customer as tests are described from the user's perspective.
The pattern is defined by the following so-called tags: FEATURE: Defines what feature(s) the test or collection of test cases is testing SCENARIO: Defines for a single test the scenario being tested GIVEN: Defines what data setup is needed; a test case can have multiple GIVEN tags when data setup is more complex WHEN: Defines the action under test; each test case should have only one WHEN tag THEN: Defines the result of the action, or more specifically the verification of the result; if multiple results apply, multiple THEN tags will be needed The following test example, taken from test codeunit 134141 - ERM Bank Reconciliation displays an ATDD design pattern-based test: [Test] VerifyDimSetIDOfCustLedgerEntryAfterPostingBankAccReconLine() // [FEATURE] [Customer] // [SCENARIO 169462] "Dimension set ID" of Cust.
Ledger Entry // should be equal "Dimension Set ID" of Bank // Acc. Reconciliation Line after posting Initialize(); // [GIVEN] Posted sales invoice for a customer CreateAndPostSalesInvoice( CustomerNo,CustLedgerEntryNo,StatementAmount); // [GIVEN] Default dimension for the customer CreateDefaultDimension(CustomerNo,DATABASE::Customer); // [GIVEN] Bank Acc.
Reconciliation Line with "Dimension Set ID" = // "X" and "Account No." = the customer CreateApplyBankAccReconcilationLine( BankAccReconciliation,BankAccReconciliationLine, BankAccReconciliationLine."Account Type"::Customer, CustomerNo,StatementAmount,LibraryERM.CreateBankAccountNo); DimSetID:= ApplyBankAccReconcilationLine( BankAccReconciliationLine, CustLedgerEntryNo, BankAccReconciliationLine."Account Type"::Customer, ''); // [WHEN] Post Bank Acc.
Reconcilation Line
![Image from page 69](../diagrams/page_69_img_21.png)
## Page 70
Test Design Chapter 4 [ 55 ] LibraryERM.PostBankAccReconciliation(BankAccReconciliation); // [THEN] "Cust. Ledger Entry"."Dimension Set ID" = "X" VerifyCustLedgerEntry( CustomerNo,BankAccReconciliation."Statement No.", DimSetID); Before any test coding is done, the test case design should already have been conceived.
In the case of the preceding example, this is what would have been handed off to the developer before writing the test code: [FEATURE] [Customer] [SCENARIO 169462] "Dimension set ID" of Cust. Ledger Entry should be equal "Dimension Set ID" of Bank Acc.
Reconcilation Line after posting [GIVEN] Posted sales invoice for a customer [GIVEN] Default dimension for the customer [GIVEN] Bank Acc. Reconcilation Line with "Dimension Set ID" = "X" and "Account No." = the customer [WHEN] Post Bank Acc.
Reconcilation Line [THEN] "Cust. Ledger Entry"."Dimension Set ID" = "X" A note on test verification In my workshops, it is mainly developers that participate. For them, when working on test automation, one of the hurdles to take is the verification part.
It makes perfect sense to all of them that data setup, the GIVEN part, has to be accounted for, not to mention the action under test in the WHEN part. The THEN part, however, is something easily neglected, especially if their assignment is to come up with the GIVEN-WHEN-THEN design themselves.
Some might ask: why should I need verification if the code executes successfully? Because you need to check if: The data created is the right data, that is, the expected data The error thrown, in case of a positive-negative test, is the expected error The confirm handled is indeed the expected confirm Sufficient verification will make sure your tests will stand the test of time.
You might want to put the next phrase as a poster on the wall: A test without verification is no test at all!

---
**Chapter Statistics:**
- Pages: 3
- Words: ~782
