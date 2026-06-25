"""Rich fake businesses (replaces the Google Sheet for now). Full data so the booking +
reviews + services render. Real outreach will scrape these fields from the prospect."""

BUSINESSES = [
    {
        "name": "Brewhaus Coffee Co.", "type": "Specialty coffee shop", "niche": "coffee",
        "tagline": "Roasted with intent, poured with care",
        "location": "Portland, OR", "address": "812 SE Hawthorne Blvd, Portland, OR 97214",
        "phone": "+1 503-555-0142", "email": "hello@brewhauscoffee.com",
        "hours": "Mon-Fri 6:30 AM-6 PM; Sat-Sun 7 AM-5 PM", "rating": 4.9,
        "requirements": "Show roast-of-the-week and an 'Order Online' CTA.",
        "services": [
            {"name": "Single-Origin Pour-Over", "price": "$6", "duration": "10 min", "desc": "Rotating micro-lot, brewed to order."},
            {"name": "Espresso Flight", "price": "$9", "duration": "15 min", "desc": "Three house espressos side by side."},
            {"name": "Whole-Bean Bag (12oz)", "price": "$18", "duration": "—", "desc": "House-roasted, ground to spec."},
            {"name": "Catering — Coffee Cart", "price": "from $250", "duration": "2 hr", "desc": "Barista + cart for your event."},
        ],
        "reviews": [
            {"name": "Devon M.", "stars": 5, "date": "2 weeks ago", "text": "Best pour-over in Portland. The rotating single-origins are always a treat."},
            {"name": "Priya R.", "stars": 5, "date": "1 month ago", "text": "Cozy, friendly, and the beans they sell make my home coffee actually good."},
            {"name": "Marcus T.", "stars": 5, "date": "1 month ago", "text": "Catering cart for our launch was a hit — pro barista, zero fuss."},
        ],
    },
    {
        "name": "IronPeak Fitness", "type": "Strength & conditioning gym", "niche": "gym",
        "tagline": "Train hard. Move better. No guesswork.",
        "location": "Austin, TX", "address": "1904 E 6th St, Austin, TX 78702",
        "phone": "+1 512-555-0188", "email": "train@ironpeakfitness.com",
        "hours": "Mon-Fri 5 AM-9 PM; Sat 7 AM-4 PM; Sun 8 AM-12 PM", "rating": 5.0,
        "requirements": "Big 'Book a Free Session' CTA and a class schedule.",
        "services": [
            {"name": "Free Intro Session", "price": "Free", "duration": "45 min", "desc": "Assessment + first workout, no pressure."},
            {"name": "1:1 Personal Training", "price": "$75", "duration": "60 min", "desc": "Programmed for your goals."},
            {"name": "Small-Group Strength", "price": "$30", "duration": "60 min", "desc": "Max 6 people, coached barbell work."},
            {"name": "Nutrition Coaching", "price": "$120/mo", "duration": "—", "desc": "Macros, check-ins, real food."},
        ],
        "reviews": [
            {"name": "Sarah K.", "stars": 5, "date": "3 weeks ago", "text": "Lost 18 lbs and finally deadlift pain-free. The coaching is the difference."},
            {"name": "Jordan P.", "stars": 5, "date": "1 month ago", "text": "Small groups mean you actually get corrected. Strongest I've ever been."},
            {"name": "Aisha N.", "stars": 5, "date": "2 months ago", "text": "Walked in nervous, walked out hooked. Coaches meet you where you are."},
        ],
    },
    {
        "name": "BrightSmile Dental", "type": "Family & cosmetic dental clinic", "niche": "dental",
        "tagline": "Gentle, modern dentistry for the whole family",
        "location": "Miami, FL", "address": "2450 Brickell Ave Suite 110, Miami, FL 33129",
        "phone": "+1 305-555-0173", "email": "smile@brightsmiledental.com",
        "hours": "Mon-Thu 8 AM-5 PM; Fri 8 AM-2 PM; Sat-Sun closed", "rating": 4.9,
        "requirements": "Prominent 'Book Appointment' CTA and an insurance note.",
        "services": [
            {"name": "New Patient Exam + Cleaning", "price": "$129", "duration": "60 min", "desc": "Exam, X-rays, and a gentle cleaning."},
            {"name": "Teeth Whitening", "price": "$299", "duration": "75 min", "desc": "In-office, noticeably brighter same day."},
            {"name": "Invisalign Consult", "price": "Free", "duration": "30 min", "desc": "Scan + custom plan, no obligation."},
            {"name": "Emergency Visit", "price": "from $95", "duration": "45 min", "desc": "Same-day relief for pain or breaks."},
        ],
        "reviews": [
            {"name": "Carlos D.", "stars": 5, "date": "1 week ago", "text": "Hate the dentist, but they made it painless and actually friendly. Rare."},
            {"name": "Emily W.", "stars": 5, "date": "3 weeks ago", "text": "Whitening was worth every penny. Staff explained everything clearly."},
            {"name": "Tomas L.", "stars": 5, "date": "1 month ago", "text": "Took my whole family. Kids weren't scared — that says it all."},
        ],
    },
]

BY_NAME = {b["name"]: b for b in BUSINESSES}
