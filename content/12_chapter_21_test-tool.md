# 12. Test Tool
*Pages 52-56*
## Page 52
The Test Tool and Standard Tests Chapter 3 [ 37 ] Test Tool Goal: Understand what the Test Tool entails and learn how to use and apply it. The Test Tool is a standard application feature that allows you to manage and run the automated tests that reside in the database, and collect their results, be they test codeunits that belong to the standard application or that are part of extensions.
With the various hands-on example tests, we will be using this tool a lot. However, before we do this, let's elaborate a little bit on it. You can easily access the Test Tool using the TELL ME WHAT YOU WANT TO DO feature in Dynamics 365 Business Central, as displayed in the following screenshot:.

## Page 53
The Test Tool and Standard Tests Chapter 3 [ 38 ] When in a clean database, or at least a database or company where the Test Tool has not been used yet, this is how the Test Tool appears. A suite called DEFAULT with no records in it appears, as seen as follows: To populate the suite take the following steps: Select the Get Test Codeunits action.
1. On the dialog that opens, you have the following two options: 2. Select Test Codeunits: This will open a list page showing all test codeunits that are present in the database from which you can select specific test codeunits; once you have selected and clicked OK, these codeunits will be added to the suite All Test Codeunits: This will add all test codeunits that exist in the database to the test suite.

## Page 54
The Test Tool and Standard Tests Chapter 3 [ 39 ] Let's select the first option, Select Test Codeunits. This will open the CAL Test Get Codeunits page. Unsurprisingly, it shows the four test codeunits we have created in Chapter 2, The Testability Framework, followed by the long list of over 700 standard test codeunits: Select the four test codeunits 60000 through 60003 and click OK.
3. 

## Page 55
The Test Tool and Standard Tests Chapter 3 [ 40 ] The suite now shows for each test Codeunit a line with LINE TYPE = Codeunit and, linked to this line and indented, all its test functions (LINE TYPE = Function) as shown in the following screenshot: To run the tests, select the Run action.
4. 

## Page 56
The Test Tool and Standard Tests Chapter 3 [ 41 ] On the following dialog that opens, with options Active Codeunit and All, select 5. All and press OK. Now all four test codeunits will be run and each test will yield a result, Success or Failure: Had we selected the option Active Codeunit only, the selected codeunit would have been executed.
For each failure, the First Error field will display the error that caused the failure. As you can see, First Error is a FlowField. If you drill down into it, the CAL Test Result window opens. This displays the whole test run history for a specific test.
Note that the message dialog in MyFirstTestCodeunit yields an Unhandled UI error. Running the test by selecting Run will call the standard test runner codeunit CAL Test Runner (130400) and will make sure that the following happen: Tests run from the Test Tool will be run in isolation The results of each test function will be logged In this short overview of the Test Tool, we used the following features: Get test codeunits Creating multiple test suites.

---
**Chapter Statistics:**
- Pages: 5
- Words: ~574
