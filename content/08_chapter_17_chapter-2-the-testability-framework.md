# 8. Chapter 2: The Testability Framework
*Pages 36-36*
## Page 36
2 The Testability Framework With Dynamics NAV 2009 Service Pack 1, Microsoft introduced the testability framework in the platform. This enabled developers to build test scripts in C/AL to run so-called headless tests; that is, tests that do not use the user interface (UI) to execute business logic.
It was a follow-up on an internal tool called the NAV Test Framework (NTF) and had been used and worked on for a couple of years already. It allowed tests to be programmed in C# and ran against the Dynamics NAV UI.
It was a neat system, with a neat technical concept behind it. However, this running test against the UI was one of the major reasons for leaving NTF behind. I seem to recall that it was the major reason because accessing business logic through the UI is slow – too slow.
Too slow to allow the Microsoft Dynamics NAV development team to run all their tests against the various versions in a reasonable time. Nowadays, Microsoft is supporting five major versions (NAV 2015, NAV 2016, NAV 2017, NAV 2018, and Business Central) for 20 countries, and each of these country versions is being built and tested at least once a day.
Any delay in the tests has a huge impact on the build of these 100 versions. In this chapter, we will have a look at what I call the five pillars of the testability framework. The five technical features that make up this framework are as follows: Test codeunits and test functions asserterror Handler functions Test runner and test isolation Test pages.

---
**Chapter Statistics:**
- Pages: 1
- Words: ~263
