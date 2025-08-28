# 13. Standard tests
*Pages 57-61*
## Page 57
The Test Tool and Standard Tests Chapter 3 [ 42 ] When diving into test coding, the Test Tool will be our companion. There we will be using various other features of it, including the following: Run selected Drilling into the test results Referencing the call stack Clearing the results Test coverage map Regarding on-premises installation: The Test Tool can be accessed and executed using an end-user license.
This has been enabled since the fall of 2017. Standard tests Goal: Get to know the basics of the standard tests provided by Microsoft. Ever since NAV 2016, Microsoft made their own application test collateral a part of the product.
A humongous set of tests is delivered as a.fob file on the product DVD, in the TestToolKit folder, and in the Docker images. Indeed, the tests haven't been delivered as an extension yet. The standard test suite does contain mainly test codeunits.
But there are also a number of supporting table, page, report, and XMLport objects in the.fob file. For Dynamics 365 Business Central, the whole set contains almost 23,000 tests in more than 700 test codeunits, for w1 and local functionality for each country in which Microsoft releases.
And with every bug that's fixed and with every new feature introduced in the application, the number of tests is growing. It has been built over the last ten years and it covers all functional areas of Business Central.
Let's set up a new suite in the Test Tool called ALL W1: Click on the Assist Edit button in the Suite Name control 1. In the CAL Test Suites pop-up window select New 2. Populate the Name and Description fields 3.
Click OK 4. 

## Page 58
The Test Tool and Standard Tests Chapter 3 [ 43 ] To open the newly created test suite: Now, using the Get Test Codeunits action, let Business Central fetch all standard test codeunits as shown in the next screenshot.
Note that I did remove our test codeunit 60000 through 60003:

## Page 59
The Test Tool and Standard Tests Chapter 3 [ 44 ] Reading the names of all test codeunits will give you a first impression of what they entail, which are as follows: Enterprise Resource Management (ERM) and Supply Chain Management (SCM) codeunits: These two categories contain almost 450 codeunits to form the major part of standard test collateral ERM test codeunits cover G/L, sales, purchase, and inventory SCM test codeunits cover warehouse and production.

## Page 60
The Test Tool and Standard Tests Chapter 3 [ 45 ] Apart from ERM and SCM, several other categories can be noted, of which the biggest are: Service (approximately 50 test codeunits) O365 integration (approximately 35) Job (approximately 25) Marketing (approximately 15) Most of these test codeunits contain functional, end-to-end tests.
But there are also codeunits that hold unit tests (UT). These are marked by the addition of Unit Test to their name. Some examples are as follows: Codeunit 134155 - ERM Table Fields UT Codeunit 134164 - Company Init UT II Codeunit 134825 - UT Customer Table With headless testing being the initial trigger for bringing the testability framework into the platform, it's no surprise that the clear majority of standard test codeunits comprises headless tests.
Test codeunits that are meant to test the user interface (UI) are marked using UI or UX in their name. Some examples are as follows: Codeunit 134280 - Simple Data Exchange UI UT Codeunit 134339 - UI Workflow Factboxes Codeunit 134711 - Autom.
Payment Registration.UX Codeunit 134927 - ERM Budget UI Note that these are not the only test codeunits addressing the UI. Any other might contain one or more UI tests, where, in general, the bulk will be headless tests.
As I am often asked how to test reports, it is noteworthy to mention as a last category those test codeunits that are dedicated to testing reports. Search for any test codeunit that is marked with the word Report in its name.
You will find 50+ of them. The following are a couple of examples: Codeunit 134063 - ERM Intrastat Reports Codeunit 136311 - Job Reports II Codeunit 137351 - SCM Inventory Reports – IV

## Page 61
The Test Tool and Standard Tests Chapter 3 [ 46 ] Categorization by FEATURE By inspecting the names of the standard test codeunits, we got an impression of what kind of tests this collateral is made. Microsoft, however, has a better structured categorization, which so far, due to low priority, hasn't been explicitly shared with the outside world.
Now that automated testing is being picked up more and more, it's pressing on Microsoft to put this on higher priority. But for now, we can access it already inside most of the test codeunits. You need to look for the FEATURE tag.
This tag is part of the Acceptance TestDriven Development (ATDD) test case design pattern, which we will be discussing later in Chapter 4, Test Design. Using the [FEATURE] tag, Microsoft categorizes their test codeunits and, in some cases, individual test functions.
Note that this tagging is far from complete as not all test codeunits have it, yet. Have a look at the (partial) abstract of the following codeunits: Codeunit 134000 - ERM Apply Sales/Receivables: OnRun: [FEATURE] [Sales] [Test] PROCEDURE VerifyAmountApplToExtDocNoWhenSetValue: [FEATURE] [Application] [Cash Receipt] [Test] PROCEDURE PmtJnlApplToInvWithNoDimDiscountAndDefDimErr: [FEATURE] [Dimension] [Payment Discount] Codeunit 134012 - ERM Reminder Apply Unapply: OnRun: [FEATURE] [Reminder] [Sales] [Test] PROCEDURE CustomerLedgerEntryFactboxReminderPage: [FEATURE] [UI] In later chapters, we will look in more detail at various standard test functions.
You will see how to take them as examples for your own test writing (Chapter 4, Test Design, Chapter 5, From Customer Wish to Test Automation - The Basics, Chapter 6, From Customer Wish to Test Automation - Next Level, and Chapter 7, From Customer Wish to Test Automation - And Some More), and how to get them to run on your own solution (Chapter 9, Getting Business Central Standard Tests Working on Your Code).

---
**Chapter Statistics:**
- Pages: 5
- Words: ~988
