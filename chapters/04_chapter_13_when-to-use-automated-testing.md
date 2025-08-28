# 4. When to use automated testing
*Pages 30-32*
## Page 30
Introduction to Automated Testing Chapter 1 [ 15 ] Shorter update cycles With agile methodologies and cloud services, it has become normal practice that updates are delivered with shorter time intervals, leaving even less time to get full testing done.
And Dynamics 365 Business Central is part of this story. If Microsoft isn't forcing us in, our customers will be requesting this from us more and more. See also the preceding discussion. Test automation is required Last but not least on this incomplete discussion of argument on the why of test automation, and perhaps the sole reason for you reading this book: automated tests are required by Microsoft when you are going to sell your Dynamics 365 Business Central extension on AppSource.
It is also great for me to be able to share my great passions with you: being a speaker on various conferences; conducting workshops; writing this book. All joking aside, this is a great opportunity for all of us.
Yes, we're pushed, but we have been lingering on this topic for too long. Now, let's get on with it. Silver bullet? Nevertheless, you might rightfully wonder whether test automation is the silver bullet that will solve everything.
And I cannot deny that. However, I can tell you that, if exercised well, it will surely raise the quality of your development effort. As mentioned before, it has the following benefits: Easy to reproduce Fast to execute Objective in its reporting When to use automated testing Those are enough arguments to convince you why you would want to use automated tests, I guess.
But how about when to use them? Ideally, this would be whenever code is changed to show that this functionality, already having been tested, is still working as it should, to show that recent modifications do not compromise the existing application.

## Page 31
Introduction to Automated Testing Chapter 1 [ 16 ] This sounds logical, but what does this mean when you have no automated tests in place? How do you go about start creating your first ones? Basically, I would advise you to use the two following criteria: What code change will give the highest return on investment when creating automated tests? For what code change will your test automation creation improve your test coding skills the most? Using these two criteria, the following kind of code changes are typical candidates for your first efforts: After go-live bug fixing Buggy code Frequently modified code Business-critical code being changed Refactoring of existing code New feature development Microsoft updates After go-live bug fixing An after go-live bug reveals an omission in the initial test efforts that can often be traced back to a flaw in the requirements.
Frequently, it has a restricted scope, and, not the least important, a clear reproduction scenario. And by all means, such a bug should be prevented from ever showing its ugly face. Buggy code You have this feature that keeps on bugging you and your customers.
Bugs keep on popping up in this code and it never seems to stop. The most elementary thing you should start with is the after go-live bug fixing approach as previously discussed. But, even more importantly, use this code to create a full test suite for the first time.

## Page 32
Introduction to Automated Testing Chapter 1 [ 17 ] Bugs are a particularly useful starting point, because they usually provide the following: A defined expectation Steps to reproduce the scenario A clear definition of how the code fails Frequently modified code One of the basic rules of good code governance is that code should only be changed when it is going to be tested.
So, if code is modified frequently, the consequence is that it will also be tested frequently. Automating these tests will give a good return on investment for sure. Business-critical code being changed Thorough testing should always be the case, but, given circumstances, it is unfortunately not always doable.
Testing changes made to business-critical code, however, should always be exhaustive. You can simply not afford any failure on them. Make it a point of honor to find even the two to five percent of bugs that statistics tell us are always there! Refactoring of existing code Refactoring code can be nerve-racking.
Removing, rewriting, and reshuffling. How do you know it is still doing the job it used to? Does it not break anything else? It certainly needs to be tested. But, when manually done, it is often executed after the whole refactoring is ready.
That might be already too late, as too many pieces got broken. Grant yourself peace of mind and start, before any refactoring, by getting an automated test suite in place for this code to prove its validity.
With every refactor step you take, run the damn suite. And again. This way, refactoring becomes fun. New feature development Starting from scratch, both on test and app code, will be an irrefutable experience.
For some, this might be the ultimate way to go. For others, this is a bridge too far, in which case, all previous candidates are probably better ones. In Section 3, Designing and Building Automated Tests for Microsoft Dynamics 365 Business Central, we will take this approach and show you the value of writing test code alongside app code.

---
**Chapter Statistics:**
- Pages: 3
- Words: ~878
