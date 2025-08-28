# Table of Contents

*Pages 10-15*

## Page 10

Table of Contents Preface 1 Section 1: Automated Testing - A General Overview Chapter 1: Introduction to Automated Testing 7 Why automated testing? 9 Why not? 9 Why yes? 10 Drive testing upstream and save costs 10 Dynamics 365 Business Central platform enables test automation 11 Relying on customers to do the testing isn't a great idea 11 Having a hard time finding people – start automating your tests 12 Test automation will free up time for everyday business 12 Keep on handling different projects because of test automation 12 Automated tests are code too 13 Some more arguments 13 Nobody loves testing 14 Reduced risks and higher satisfaction 14 Once the learning curve is over, it will often be quicker than manual testing 14 Shorter update cycles 15 Test automation is required 15 Silver bullet? 15 When to use automated testing 15 After go-live bug fixing 16 Buggy code 16 Frequently modified code 17 Business-critical code being changed 17 Refactoring of existing code 17 New feature development 17 Microsoft updates 18 What is automated testing? 18 Summary 19 Section 2: Automated Testing in Microsoft Dynamics 365 Business Central Chapter 2: The Testability Framework 21 The five pillars of the testability framework 22 Pillar 1 – Test codeunits and test functions 22 Test codeunits 22 Test functions 23 Pillar 2 – asserterror 25.

## Page 11

Table of Contents [ ii ] Pillar 3 – handler functions 27 Pillar 4 – Test runner and test isolation 29 Test runner 30 Test isolation 31 Pillar 5 – Test pages 32 Summary 35 Chapter 3: The Test Tool and Standard Tests 36 Test Tool 37 Standard tests 42 Categorization by FEATURE 46 Standard libraries 47 Summary 49 Section 3: Designing and Building Automated Tests for Microsoft Dynamics 365 Business Central Chapter 4: Test Design 51 No design, no test 52 Understanding test case design patterns 53 Acceptance Test-Driven Development 54 A note on test verification 55 Understanding test data setup design patterns 56 Test fixture, data agnostics, and prebuilt fixture 57 Test fixture and test isolation 58 Shared fixture implementation 58 Fresh fixture implementation 59 Using customer wish as test design 60 Summary 61 Chapter 5: From Customer Wish to Test Automation - The Basics 62 From customer wish to test automation 63 Data model 63 Business logic 64 LookupValue extension 64 Implementing a defined customer wish 65 Test example 1 – a first headless test 65 Customer wish 66 FEATURE 66 SCENARIO 66 GIVEN 66 WHEN 66 THEN 67 Complete scenario 67 Application code 67 Test code 69 Steps to take 69.

## Page 12

Table of Contents [ iii ] Create a test codeunit 69 Embed the customer wish into a test function 69 Write your test story 70 Construct the real code 71 CreateLookupValueCode 71 CreateCustomer 72 SetLookupValueOnCustomer 73 VerifyLookupValueOnCustomer 73 Test execution 76 Test the test 77 Test the data being created 77 Adjust the test so the verification errs 78 Test example 2 – a first positive-negative test 80 Test code 80 Steps to take 80 Create a test codeunit 80 Embed the customer wish into a test function 81 Write your test story 81 Construct the real code 82 VerifyNonExistingLookupValueError 82 Test execution 83 Test the test 83 Adjust the test so the verification errs 83 Removing asserterror 84 Test example 3 – a first UI test 85 Customer wish 85 Application code 86 Test code 86 Create a test codeunit 86 Embed the customer wish into a test function 86 Write your test story 87 Construct the real code 88 CreateCustomerCard 88 SetLookupValueOnCustomerCard 88 Test execution 90 Test the test 92 Adjust the test so the verification errs 92 Headless versus UI 93 Summary 94 Chapter 6: From Customer Wish to Test Automation - Next Level 95 Sales documents, customer template, and warehouse shipment 95 Test example 4 – how to set up a shared fixture 96 Customer wish 97 Application code 97 Test Code 98 Create a test codeunit 98 Embed the customer wish into a test function 99 Write your test story 100.

![Image from page 12](../images/page_12_img_3.png)

![Image from page 12](../images/page_12_img_5.png)

![Image from page 12](../images/page_12_img_7.png)

![Image from page 12](../images/page_12_img_9.png)

![Image from page 12](../images/page_12_img_18.png)

![Image from page 12](../images/page_12_img_19.png)

![Image from page 12](../images/page_12_img_21.png)

![Image from page 12](../images/page_12_img_22.png)

![Image from page 12](../images/page_12_img_54.png)

![Image from page 12](../images/page_12_img_63.png)

![Image from page 12](../images/page_12_img_67.png)

## Page 13

Table of Contents [ iv ] Construct the real code 101 Test execution 103 Test the test 103 Test example 5 – how to parametrize tests 104 Customer wish 104 Application code 104 Test code 106 Create, embed, and write 106 Construct the real code 107 Test execution 109 Test the test 112 A missing scenario? 112 Test example 6 – how to hand over data to UI handlers 113 Customer wish 113 Test code 114 Create, embed, and write 114 Construct the real code 115 Enqueue 117 Dequeue 118 Test execution 118 Test the test 119 Summary 119 Chapter 7: From Customer Wish to Test Automation - And Some More 120 Test example 7 – how to test a report 120 Customer wish 121 Application code 122 Test code 123 Create, embed, and write 123 Construct the real code 124 Test execution 126 Test the test 126 Adjust the test so the verification errs 127 Test example 8 – how to construct an extensive scenario 127 Customer wish 127 Application code 130 Test code 131 Create, embed, and write 132 Construct the real code 134 Initialize 134 VerifyLookupValueOnWarehouseShipmentLine 136 CreateWarehouseShipmentFromSalesOrder 136 Test execution 139 Test the test 139 Adjust the test so the verification errs 139 Refactoring 140 Summary 141.

![Image from page 13](../images/page_13_img_3.png)

![Image from page 13](../images/page_13_img_5.png)

![Image from page 13](../images/page_13_img_7.png)

![Image from page 13](../images/page_13_img_9.png)

![Image from page 13](../images/page_13_img_18.png)

![Image from page 13](../images/page_13_img_19.png)

![Image from page 13](../images/page_13_img_21.png)

![Image from page 13](../images/page_13_img_22.png)

![Image from page 13](../images/page_13_img_54.png)

![Image from page 13](../images/page_13_img_63.png)

![Image from page 13](../images/page_13_img_67.png)

## Page 14

Table of Contents [ v ] Section 4: Integrating Automated Tests in Your Daily Development Practice Chapter 8: How to Integrate Test Automation in Daily Development Practice 143 Casting the customer wish into ATDD scenarios 144 Taking small steps 145 Making the test tool your friend 146 Test coverage map 147 Extending the test tool 148 Integrating with daily build 150 Maintaining your test code 152 Extensions and tests 153 Summary 153 Chapter 9: Getting Business Central Standard Tests Working on Your Code 154 Why use the standard tests? 154 Executing standard test 155 What does this tell us? 156 Fixing failing standard tests 156 Attacking the error 157 Fixing the error 165 Running the failing tests again 166 Viewing the call stack from the test tool 166 It's all about data 167 Making your code testable 170 Applying the Handled pattern 172 Is it all really about data? 174 Summary 174 Appendix A: Test-Driven Development 175 TDD, a short description 175 TDD, red-green-refactor 176 TDD and our test examples 177 Summary 178 Appendix B: Setting Up VS Code and Using the GitHub Project 179 VS Code and AL development 179 VS Code project 179 launch.json 180 app.json 181 The GitHub repository 182 Structure of the GitHub repository 182 Chapter 2 183.

## Page 15

Table of Contents [ vi ] ATDD Scenarios 183 LookupValue Extension (app only) 183 Chapter 5 (LookupValue Extension) 184 Chapter 6 (LookupValue Extension) 184 Chapter 7 (LookupValue Extension) 184 Chapter 7 (LookupValue Extension) - refactored and completed 184 Chapter 9 (LookupValue Extension) 184 LookupValue Test Extension (test only) 185 Notes on the AL code 185 VS Code versus C/SIDE 185 Prefix or suffix 185 Word wrap 186 Other Books You May Enjoy 187 Index 190.

![Image from page 15](../images/page_15_img_3.png)

![Image from page 15](../images/page_15_img_5.png)

![Image from page 15](../images/page_15_img_7.png)

![Image from page 15](../images/page_15_img_9.png)

![Image from page 15](../images/page_15_img_18.png)

![Image from page 15](../images/page_15_img_19.png)

![Image from page 15](../images/page_15_img_21.png)

![Image from page 15](../images/page_15_img_22.png)

![Image from page 15](../images/page_15_img_54.png)

![Image from page 15](../images/page_15_img_63.png)

![Image from page 15](../images/page_15_img_67.png)

---

**Chapter Statistics:**
- Pages: 6
- Words: ~1,172
