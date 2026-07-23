Your task is to generate a proposal using input data from a form.

Context:
We are an automation/no-code agency that develops systems revolving around growth, revenue operations, AI automation, and business systems.

Return ONE JSON object with these fields:


{
  "proposalTitle":"",
  "descriptionName":"",
  "oneParagraphProblemSummary":"",
  "solutionHeadingOne":"",
  "solutionDescriptionOne":"",
  "solutionHeadingTwo":"",
  "solutionDescriptionTwo":"",
  "solutionHeadingThree":"",
  "solutionDescriptionThree":"",
  "shortScopeTitleOne":"",
  "shortScopeTitleTwo":"",
  "shortScopeTitleThree":"",
  "shortScopeDescriptionOne":"",
  "shortScopeDescriptionTwo":"",
  "shortScopeDescriptionThree":"",
  "milestoneOneDay":"",
  "milestoneTwoDay":"",
  "milestoneThreeDay":"",
  "milestoneFourDay":"",
  "milestoneDescriptionOne":"",
  "milestoneDescriptionTwo":"",
  "milestoneDescriptionThree":"",
  "milestoneDescriptionFour":""
}

Rules:

1. Use a spartan, casual tone.
2. Be concise but professional.
3. Fill every field.
4. Description fields should be no longer than 14 words.
5.Return a JSON object.

Do not wrap the JSON in markdown.

Do not use ```json.

Do not use code fences.

Your first character must be {

Your last character must be }

EXAMPLE INPUT

{
  "companyName":"MM Digital",
  "problem":"they can't generate leads. everything is referral based rn.",
  "solution":"cold email lead gen system, client reactivation system, and best in class sales training for closing",
  "scope":"1k/day cold email infra, 30k email leads, 4 weekly zoom sessions for sales training",
  "currentDate":"Feb 4 2025",
  "howSoon":"two months",
  "depositCost":"$1,845"
}


EXAMPLE OUTPUT

{
  "proposalTitle": "Lead Gen System for MM Digital
",
  "descriptionName": "A simple, scalable lead generation system built to help grow your content efforts & connect you with the right people.
",
  "oneParagraphProblemSummary": "Right now, MM Digital is struggling with an inability to generate qualified leads. The majority of your new clients are referral-based, which, while always nice to have, is not scalable nor is it reliable. Building an alternative strategy—one that allows you to take leads from cold -> close—is vital to the health and longevity of the company, and it’s what we’re going to help you with.
",
  "solutionHeadingOne": "Cold Outbound Lead Gen",
  "solutionDescriptionOne": "We’ll put in place a robust cold-email-based system for you using best practices.",
  "solutionHeadingTwo": "Client Reactivation System",
  "solutionDescriptionTwo": "We’ll build a simple, but high-ROI reactivation system to let you extract value from pre-existing clients.",
  "solutionHeadingThree": "Best-In-Class Sales Training",
  "solutionDescriptionThree": "We’ll train your team with world-class setting & closing mechanisms.",
  "shortScopeTitleOne": "Cold email infrastructure that sends ~1K emails/day",
  "shortScopeTitleTwo": "30K high-quality scraped email leads (included)",
  "shortScopeTitleThree": "Four weekly one-hour sales training sessions over Zoom",
  "shortScopeDescriptionOne": "12 domains, 36 mailboxes, DNS optimization, and warmups included.",
  "shortScopeDescriptionTwo": "30,000 leads in your target market, delivered by CSV.",
  "shortScopeDescriptionThree": "We’ll take your sales team from 0->1.",
  "milestoneOneDay": "February 8th, 2025",
  "milestoneTwoDay": "February 28th, 2025",
  "milestoneThreeDay": "March 10th, 2025",
  "milestoneFourDay":"March 17th-April 1st, 2025",
  "milestoneDescriptionOne": "Cold email system done & ready for warmup.",
  "milestoneDescriptionTwo": "Cold email system fully warmed up & operational.",
  "milestoneDescriptionThree": "10,000 outbound emails sent; analysis & training #1.",
  "milestoneDescriptionFour":"One sales training per week alongside iteration & handoff."
}

NOW GENERATE A PROPOSAL FOR THIS CLIENT

{
  "companyName":" {{=gives["373212602"]["values"]["cmrss4x75001j0cl39toce447"]}} ",
  "problem": "{{=gives["373212602"]["values"]["cmrss4x75001m0cl37lzw1kms"]}}",
  "solution": "{{=gives["373212602"]["values"]["cmrss4x75001n0cl33q6fczlh"]}}",
  "scope": "{{=gives["373212602"]["values"]["cmrss4x75001o0cl3b4ysf6f5"]}}",
  "currentDate":"{{=gives["373212602"]["createdAt"]}}",
  "howSoon": "{{=gives["373212602"]["values"]["cmrss4x75001q0cl34xvj4icp"]}}",
  "depositCost": "{{=gives["373212602"]["values"]["cmrss4x75001p0cl3400uattd"]}}"
}

