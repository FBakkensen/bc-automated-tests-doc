# 3. Why automated testing?
*Pages 24-29*
## Page 24
Introduction to Automated Testing Chapter 1 [ 9 ] Had automated tests been in place, the choice would have been quite simple: the first option, resulting in no hassle at home and no hassle at work. In this chapter, we will discuss the following topics: Why automated testing? When to use automated testing.
What is automated testing? If you prefer to read the what first, you might first want to jump to What is automated testing? Why automated testing? Plainly said: it all boils down to saving you a lot of hassle.
There are no emotions or timeintensive execution will keep you from (re)running tests. It's just a matter of pushing the button and getting the tests carried out. This is reproducible, fast, and objective.
To clarify, automated tests are the following things: Easy to reproduce Fast to execute Objective in its reporting If it was as straightforward as that, then why haven't we been doing this in the Dynamics 365 Business Central world all those years? You probably can come up with a relevant number of arguments yourself, of which the most prominent might be: we do not have time for that.
Or maybe: who's going to pay for that? Why not? Before elaborating on any arguments, pro or con, let me create a more complete why not? list. Let's call it the whys of non-automated testing: Costs are too high and will make us uncompetitive.
Dynamics 365 Business Central platform does not enable it. Customers do the testing, so why should we bother?

## Page 25
Introduction to Automated Testing Chapter 1 [ 10 ] Who's going to write the test code? We already have a hard time finding people. Our everyday business does not leave room to add a new discipline. There are too many different projects to allow for test automation.
Microsoft has tests automated, and still, Dynamics 365 Business Central is not bug free. Why yes? Dynamics 365 Business Central is not as simple as it used to be way back when it was called Navigator, Navision Financials, or Microsoft Business Solutions—Navision.
And the world around us isn't as one fold either. Our development practices are becoming more formal, and, with this, the call for testing automation is pressing on us for almost the same reasons as the why of non-automated testing: Drive testing upstream and save costs Dynamics 365 Business Central platform enables test automation Relying on customers to do the testing isn't a great idea Having a hard time finding people—start automating your tests Test automation will free up time for everyday business Keep on handling different projects because of test automation Automated tests are code too Drive testing upstream and save costs Regarding the costs, I am inclined to say that, on average, the Dynamics 365 Business Central project goes 25% over budget in the end, mainly due to after go-live bug fixing.
I am not going to elaborate much on who's to pay for this, but my experiences are that it's often the implementation partner. The math is quite simple if assuming that to be the case. If you're spending 25% extra on your own account at the end of the line, why not push it upstream and spend it during the development phase on automated testing, building up a reusable collateral? During my time at Microsoft in the 2000s, research had been performed on the cost of catching a bug in the different stages of developing a major release of a product.
If my memory is not failing, the cost of catching a bug after release was found to be approximately 1,000 times higher than when catching the bug already at requirement specification. 

## Page 26
Introduction to Automated Testing Chapter 1 [ 11 ] Translating this to the world of an independent software vendor (ISV), this might roughly be a factor 10 lower. So, the cost of catching a bug all the way downstream would be 100 times higher than all the way upstream.
In case of a value-added reseller (VAR) doing oneoff projects, this could be another factor of 10 lower. Whatever the factors would be, any spending upstream is more cost effective than downstream, be it more formalized testing, better app coding, code inspection, or more detailed requirements specifying.
Note that people often do correct me, saying that the percentage of 25% is even on the low side. Dynamics 365 Business Central platform enables test automation In all honesty, this is a no-brainer, as this is the topic of this book.
But it is worthwhile realizing that the testability framework inside the platform has been there ever since version 2009 SP1, released in the summer of 2009. So, for over nine years the platform has enabled us to build automated tests.
Does it sound strange if I say that we have been sleeping for all that time? At least, most of us. Relying on customers to do the testing isn't a great idea I agree that customers might know their features the best, and as such, are the presumable testers.
But can you rely 100% that testing isn't squeezed between deadlines of an implementation, and, in addition, between deadlines of their daily work? And still, in what way does their testing contribute to a more effective test effort in the future? How structured and reproducible will it be? Posing these questions answers them already.
It isn't a great idea, in general, to rely on customers testing if you want to improve your development practices. Having said that, this doesn't mean that customers should not be included; by all means, incorporate them in setting up your automated tests.
We will elaborate on that more later. 

## Page 27
Introduction to Automated Testing Chapter 1 [ 12 ] Having a hard time finding people – start automating your tests At this very moment, while I am writing this, all implementation partners in the Dynamics world are having a hard time finding people to add to their teams in order to get the work done.
Note that I deliberately didn't use the adjective right in that sentence. We all are facing this challenge. And, even if human resources were abundant, practices show that, with growing business, in either volume or size, the number of resources used does not grow proportionally.
Consequently, we must all invest in changing our daily practices, which very often leads to automation, using, for example, PowerShell to automate administrative tasks and RapidStart methodology for configuring new companies.
Likewise, writing automated tests to make your test efforts easier and faster. Indeed, it needs a certain investment to get it up and running, but it will save you time in the end. Test automation will free up time for everyday business Similar to getting the job done with proportionally fewer resources, test automation will eventually be of help in freeing up time for everyday business.
This comes with an initial price, but will pay off in due time. A logical question being posed when I touch the topic of spending time when introducing test automation, concerns the ratio of time spent on app and test coding.
Typically, at the Microsoft Dynamics 365 Business Central team, this is a 1:1 ratio, meaning that for each hour of app coding there is one hour of test coding. Keep on handling different projects because of test automation Traditional Dynamics 365 Business Central implementation partners typically have their hands full of customers with a one-off solution.
And, due to this have dedicated teams or consultants taking care of these installations, testing is handled in close cooperation with the end-user with every test run putting a significant load on those involved.
Imagine what it would mean to have an automated test collateral in place—how you would be able to keep on servicing those one-off projects as your business expands. 

## Page 28
Introduction to Automated Testing Chapter 1 [ 13 ] On any major development platform, such as Visual Studio, it has been common practice for a long time already that applications are delivered with test automation in place.
Note that more and more customers are aware of these practices. And more and more, they will be asking you why you are not providing automated tests to their solution. Each existing project is a threshold to take having a lot of functionality and no automated tests.
In a lot of cases, the major part of the features used is standard Dynamics 365 Business Central functionality, and, for these, Microsoft has made their own tests available since version 2016. Altogether, over 21,000 tests have been made available for the latest version of Business Central.
This is a humongous number, of which you might take advantage and make a relatively quick start on. We will discuss these tests and how you could get them running on any solution later. Automated tests are code too There is no way of denying it: automated tests are also code.
And any line of code has a certain probability of containing a bug. Does this mean you should refrain from test automation? If so, it sounds like refraining from coding in general. For sure, the challenge is to keep the bug probability to a bare minimum by making the test design a part of the requirements and requirements review, by reviewing the test code like you would want to review the app code, and by making sure that tests always end with an adequate number of verifications by putting them under source code management.
Ages ago, I watched a documentary on this topic, stating that research had shown that this probability was somewhere between two and five percent. The exact probability was likely to depend on the coding skills of the developer concerned.
Some more arguments Still not convinced on why you would/should/could start using test automation? Do you need more arguments to sell it inside your company and to your customers?

## Page 29
Introduction to Automated Testing Chapter 1 [ 14 ] Here are some of the arguments: Nobody loves testing Reduced risks and higher satisfaction Once the learning curve is over, it will often be quicker than manual testing Shorter update cycles Test automation is required Nobody loves testing Well, almost nobody.
And, surely, when testing means re-running and re-running today, tomorrow, next year, it tends to become a nuisance, which deteriorates the testing discipline. Automate tasks that bore people and free up time for more relevant testing where manual work makes a difference.
Reduced risks and higher satisfaction Having an automated test collateral enables you to have a quicker insight than ever before into the state of the code. And, at the same time, when building up this collection, the regression of bugs and the insertion of new ones will be much lower than ever before.
This all leads to reduced risks and higher customer satisfaction, and your management will love this. Once the learning curve is over, it will often be quicker than manual testing Learning this new skill of automating your tests will take a while, no doubt about that.
But, once mastered, conceiving and creating them will often be much quicker than doing the thing manually, as tests often are variations of each other. Copying and pasting with code is... well... can you do such a thing with manual testing? Not to mention re-running these automated tests or the manual tests.

---
**Chapter Statistics:**
- Pages: 6
- Words: ~1,888
