## Standard libraries

*Pages 62-63*

## Page 62

The Test Tool and Standard Tests Chapter 3 [ 47 ] At this very moment, the standard test suite objects are to be found in the following ID ranges: 134000 to 139999: w1 tests 144000 to 149999: local tests Standard libraries Goal: Get to know the basics about the standard test helper libraries provided by Microsoft.

Supporting their standard tests, Microsoft has created a nice and very useful collection of helper functions in more than 70 library codeunits. These helper functions range from random data generations and master data generation to standard generic and more specific check routines.

Need a new item? You might make use of the CreateItem or CreateItemWithoutVAT helper functions in Library - Inventory (codeunit 132201). Need a random text? Use the RandText helper function in Library – Random (codeunit 130440).

Want to get the same formatted error messages when verifying your test outcome? Use one of the helper functions in the Assert (codeunit 130000), such as IsTrue, AreNotEqual, and ExpectedError. A frequently reappearing question during my workshops is: How do I know if these libraries contain a helper function I need in my own test? Is there an overview of the various helper functions? Unfortunately, there is no overview of all available helper functions for Dynamics 365 Business Central.

However, up to NAV 2018, a.chm help file containing this information was included in the TestToolKit folder on the product DVD. You might want to make use of this, but I always use a very simple method. Having all our code in a source code management system, I can do a quick file search in the standard test objects folder.

In case I need a helper that will create me a service item, I might open VS Code on that folder and search for CreateServiceItem, as shown in the following screenshot:

![Image from page 62](../images/page_62_img_3.png)

![Image from page 62](../images/page_62_img_5.png)

![Image from page 62](../images/page_62_img_7.png)

![Image from page 62](../images/page_62_img_9.png)

![Image from page 62](../images/page_62_img_18.png)

![Image from page 62](../images/page_62_img_19.png)

![Image from page 62](../images/page_62_img_21.png)

![Image from page 62](../images/page_62_img_22.png)

![Image from page 62](../images/page_62_img_54.png)

![Image from page 62](../images/page_62_img_63.png)

![Image from page 62](../images/page_62_img_67.png)

## Page 63

The Test Tool and Standard Tests Chapter 3 [ 48 ] In Section 3, Designing and Building Automated Tests for Microsoft Dynamics 365 Business Central, of this book, when building tests, we will happily make use of various standard helper functions, making our work much more efficient and consistent.

At this very moment, the standard test library objects are to be found in the following ID ranges: 130000 to 133999: w1 test helper libraries Note that all test tool objects also reside in the lower part of this range: 140000 to 143999: local test helper libraries More on unit and functional tests? Go to: https:/​/​www.​softwaretestinghelp.​com/​the-​difference-​between-​unitintegration-​and-​functional-​testing/​.

![Image from page 63](../images/page_63_img_3.png)

![Image from page 63](../images/page_63_img_5.png)

![Image from page 63](../images/page_63_img_7.png)

![Image from page 63](../images/page_63_img_9.png)

![Image from page 63](../images/page_63_img_18.png)

![Image from page 63](../images/page_63_img_19.png)

![Image from page 63](../images/page_63_img_21.png)

![Image from page 63](../images/page_63_img_22.png)

![Image from page 63](../images/page_63_img_54.png)

![Image from page 63](../images/page_63_img_63.png)

![Image from page 63](../images/page_63_img_67.png)

---

**Chapter Statistics:**
- Pages: 2
- Words: ~411
