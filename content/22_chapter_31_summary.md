# 22. Summary
*Pages 76-76*
## Page 76
Test Design Chapter 4 [ 61 ] Through this, your test automation will be a logical result of previous work. New insights, resulting in requirement updates, will be reflected in this list and accordingly in your test automation.
Whereas your current requirement documentation might not always be in sync with the latest version of the implementation, they will be, when promoting your test design to requirements, as your automated tests will have to reflect the latest version of your app code.
In this manner, your test automation is your up-to-date documentation. Killing five birds with one stone, indeed. As we will be doing in the next chapters, we will specify our requirements as a test design, initially at the feature and scenario level, using the FEATURE and SCENARIO tags.
Then, this will be followed by a detailed specification using the GIVEN, WHEN, and THEN tags. Have a peek preview of how this looks in the following example, being one scenario for the LookupValue extensions that we are going to work on in the next chapters: [FEATURE] LookupValue UT Sales Document [SCENARIO #0006] Assign lookup value on sales quote document page [GIVEN] A lookup value [GIVEN] A sales quote document page [WHEN] Set lookup value on sales quote document [THEN] Sales quote has lookup value code field populate The full ATDD test design is stored as an Excel sheet LookupValue on GitHub.
Summary Test automation will profit from a structured approach and, for this, we introduced a set of concepts and test patterns, such as the ATDD pattern and test fixture patterns. Now, in the next chapter, Chapter 5, From Customer Wish to Test Automation – The Basics, we will utilize these patterns to finally implement test code.

---
**Chapter Statistics:**
- Pages: 1
- Words: ~287
