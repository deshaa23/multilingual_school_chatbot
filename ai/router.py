import json
import re

from langchain_ollama import ChatOllama


llm = ChatOllama(
    model="llama3:latest",
    temperature=0
)


TOOL_ROUTER_PROMPT = """
You are an intent router for a school chatbot.

Choose exactly ONE tool based on what the student wants.

============================================================
PERSONAL DATA VS SCHOOL KNOWLEDGE
============================================================

If the question asks about the logged-in student's personal
academic information, use a database tool.

Personal/student data:
- marks
- performance
- attendance
- timetable
- assignments
- teacher information
- profile information

If the question asks about general school information or
information contained in school documents, use rag_tool.

Never use rag_tool to retrieve personal student data.
Never use SQL tools to answer school-policy/document questions.

TOOLS:

1. marks_tool
Use for retrieving marks/scores/results.

2. performance_tool

Use for analysis, comparison, improvement, strongest/weakest subject,
overall performance, average performance, or recommendations based on marks.

Examples:

"What is my overall performance?"
→ metric = "overall"

"What is my average?"
→ metric = "average"

"Which subject am I strongest in?"
→ metric = "highest"

"Which subject am I weakest in?"
→ metric = "lowest"

"Which subject should I improve?"
→ metric = "lowest"

"How can I improve my performance?"
→ metric = "improvement"

"Am I performing well?"
→ metric = "overall"

If no specific metric is requested:
→ metric = "overall"

3. attendance_tool
Use for attendance, presence, absence, attendance percentage,
attendance records, or attendance eligibility.

IMPORTANT:
Questions about attendance eligibility must use attendance_tool.

4. timetable_tool
Use for timetable, classes, periods, schedule, today's classes,
or a particular day's classes.

5. assignment_tool
Use for assignments, homework, pending work, upcoming work,
deadlines, or overdue assignments.

6. teacher_tool
Use for teacher information.

7. profile_tool
Use for student profile, roll number, admission number,
date of birth, or student information.

8. rag_tool

Use for information that must be answered from the school's
knowledge base, school documents, policies, rules, notices,
academic material, curriculum information, or other stored
school information.

Examples:

"What are the school uniform rules?"
→ rag_tool

"What are the rules for grades VI-X?"
→ rag_tool

"What is the school policy on attendance?"
→ rag_tool

"What is the admission procedure?"
→ rag_tool

"What are Newton's laws of motion?"
→ rag_tool

IMPORTANT:
If the question asks for the student's OWN data, never use rag_tool.

"My marks in Mathematics"
→ marks_tool

"My attendance"
→ attendance_tool

"My timetable"
→ timetable_tool

"My assignments"
→ assignment_tool

9. general_chat
Use for greetings, casual conversation, jokes, or unrelated questions.

============================================================
PARAMETER EXTRACTION
============================================================

For timetable questions:

Extract the requested day.

Valid values:

- Monday
- Tuesday
- Wednesday
- Thursday
- Friday
- Saturday
- Sunday
- today
- tomorrow
- yesterday

Examples:

"What classes do I have on Monday?"
→ day = "Monday"

"Show Tuesday's timetable"
→ day = "Tuesday"

"What is my timetable?"
→ day = null

"What classes do I have today?"
→ day = "today"

"Show me today's timetable"
→ day = "today"

"Show me tomorrow's timetable"
→ day = "tomorrow"

"What classes are there tomorrow?"
→ day = "tomorrow"

"Show yesterday's timetable"
→ day = "yesterday"

"What classes did I have yesterday?"
→ day = "yesterday"

If no specific day is mentioned:
→ day = null

For assignment questions:

Use status:

"pending", "upcoming", "due", "not completed"
→ status = "pending"

"overdue", "late"
→ status = "overdue"

Otherwise:
→ status = null

For marks questions:

Extract subject if explicitly mentioned.

Examples:
"What are my Mathematics marks?"
→ subject = "Mathematics"

"What did I score in Science?"
→ subject = "Science"

Otherwise:
→ subject = null

Extract exam if explicitly mentioned.

Examples:
"My final marks"
→ exam = "Final"

"My mid term marks"
→ exam = "Mid Term"

Otherwise:
→ exam = null

For attendance questions:

Extract metric when the user explicitly asks for a specific attendance-related value.

"What is my attendance percentage?"
→ metric = "attendance_percentage"

"What percentage of classes have I attended?"
→ metric = "attendance_percentage"

"How much attendance do I have?"
→ metric = "attendance_percentage"

"How many days was I absent?"
→ metric = "absent"

"How many classes did I miss?"
→ metric = "absent"

"Am I eligible based on my attendance?"
→ metric = "eligibility"

"Do I meet the attendance requirement?"
→ metric = "eligibility"

Otherwise:
→ metric = null

============================================================
IMPORTANT
============================================================

Do NOT answer the question.

Do NOT generate SQL.

Return ONLY valid JSON.

Return exactly this structure:

{{
    "tool": "tool_name",
    "subject": null,
    "exam": null,
    "day": null,
    "status": null,
    "metric": null,
    "confidence": 0.0
}}

User question:
{question}
"""


VALID_TOOLS = {
    "marks_tool",
    "attendance_tool",
    "performance_tool",
    "timetable_tool",
    "assignment_tool",
    "teacher_tool",
    "profile_tool",
    "rag_tool",
    "general_chat"
}


VALID_METRICS = {
    None,
    "highest",
    "lowest",
    "attendance_percentage",
    "absent",
    "eligibility",
    "overall",
    "average",
    "improvement"
}


VALID_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "today",
    "tomorrow",
    "yesterday"
}


VALID_STATUSES = {
    None,
    "pending",
    "overdue"
}


def route_query(question: str) -> dict:

    question_lower = question.lower().strip()

    # =========================================================
    # DETERMINISTIC PROFILE ROUTING
    # =========================================================

    profile_patterns = [
        r"\broll\s*(number|no\.?|num)\b",
        r"\broll\b",
        r"\badmission\s*(number|no\.?|num)\b",
        r"\badmission\s*(id|number|no\.?)\b",
        r"\bdate\s*of\s*birth\b",
        r"\bdob\b",
        r"\bmy\s+profile\b",
        r"\bmy\s+student\s+details\b",
        r"\bmy\s+student\s+information\b",
    ]

    if any(re.search(pattern, question_lower) for pattern in profile_patterns):

        result = {
            "tool": "profile_tool",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 1.0
        }

        print("\n========== ROUTER RESULT ==========")
        print(result)
        print("===================================")

        return result
    
    # =========================================================
    # 2. DETERMINISTIC RAG ROUTING
    # =========================================================

    rag_patterns = [

    # =========================================================
    # SCHOOL RULES & REGULATIONS
    # =========================================================

    r"\bschool rules?\b",
    r"\bschool regulation(s)?\b",
    r"\bschool polic(y|ies)\b",
    r"\bschool guidelines?\b",
    r"\bschool handbook\b",
    r"\bschool code of conduct\b",
    r"\brules and regulations\b",
    r"\brules for students\b",
    r"\bstudent rules?\b",
    r"\bschool norms?\b",
    r"\bschool instructions?\b",
    r"\bschool requirements?\b",

    # =========================================================
    # ATTENDANCE POLICY / GENERAL ATTENDANCE RULES
    # =========================================================

    r"\battendance polic(y|ies)\b",
    r"\battendance rules?\b",
    r"\battendance requirement\b",
    r"\battendance requirements\b",
    r"\bminimum attendance\b",
    r"\battendance percentage\b",
    r"\brequired attendance\b",
    r"\bcompulsory attendance\b",
    r"\battendance criteria\b",
    r"\battendance eligibility\b",
    r"\battendance guidelines?\b",
    r"\battendance regulations?\b",
    r"\bhow much attendance is required\b",
    r"\bwhat percentage attendance\b",
    r"\bminimum percentage of attendance\b",

    # =========================================================
    # LIBRARY
    # =========================================================

    r"\blibrary\b",
    r"\blibrary rules?\b",
    r"\blibrary polic(y|ies)\b",
    r"\blibrary regulations?\b",
    r"\blibrary guidelines?\b",
    r"\blibrary timings?\b",
    r"\blibrary period\b",
    r"\blibrary books?\b",
    r"\blibrary fine\b",
    r"\blibrary fines?\b",
    r"\blate book\b",
    r"\blate book return\b",
    r"\bbook submission\b",
    r"\bbook return\b",
    r"\bbook issue\b",
    r"\bbook renewal\b",
    r"\breference books?\b",
    r"\bbooks? can be issued\b",
    r"\bnumber of books\b",

    # =========================================================
    # UNIFORM / DRESS CODE
    # =========================================================

    r"\buniform\b",
    r"\bschool uniform\b",
    r"\buniform rules?\b",
    r"\buniform polic(y|ies)\b",
    r"\bdress code\b",
    r"\bdress rules?\b",
    r"\bschool dress\b",
    r"\bproper uniform\b",
    r"\buniform requirements?\b",
    r"\bshoes?\b",
    r"\bsocks?\b",
    r"\btie\b",
    r"\bbelt\b",
    r"\bschool blazer\b",
    r"\bsweater\b",
    r"\bhair\b",
    r"\bhair style\b",
    r"\bhair gel\b",
    r"\bhair colour\b",
    r"\bhair color\b",
    r"\bjewellery\b",
    r"\bjewelry\b",
    r"\baccessories\b",

    # =========================================================
    # DISCIPLINE
    # =========================================================

    r"\bdiscipline\b",
    r"\bdisciplinary rules?\b",
    r"\bdisciplinary action\b",
    r"\bdisciplinary polic(y|ies)\b",
    r"\bmisconduct\b",
    r"\bindiscipline\b",
    r"\bcode of conduct\b",
    r"\bstudent conduct\b",
    r"\bbehaviour rules?\b",
    r"\bbehavior rules?\b",
    r"\bpunishment\b",
    r"\bpenalt(y|ies)\b",
    r"\bexpulsion\b",
    r"\bsuspension\b",
    r"\bwarning\b",
    r"\bstrict action\b",

    # =========================================================
    # SCHOOL TIMINGS / GENERAL SCHEDULE
    # =========================================================

    r"\bschool timings?\b",
    r"\bschool hours?\b",
    r"\bschool time\b",
    r"\bschool opening time\b",
    r"\bschool closing time\b",
    r"\bschool starts\b",
    r"\bschool ends\b",
    r"\bworking hours\b",
    r"\bworking days\b",

    # =========================================================
    # HOLIDAYS / VACATIONS
    # =========================================================

    r"\bschool holidays?\b",
    r"\bholiday list\b",
    r"\bholiday calendar\b",
    r"\bholiday schedule\b",
    r"\bvaccation\b",
    r"\bvacation\b",
    r"\bsummer vacation\b",
    r"\bwinter vacation\b",
    r"\bautumn break\b",
    r"\bterm break\b",
    r"\bbreak dates?\b",
    r"\bschool closure\b",
    r"\bholiday polic(y|ies)\b",

    # =========================================================
    # ADMISSION
    # =========================================================

    r"\badmission\b",
    r"\badmission process\b",
    r"\badmission procedure\b",
    r"\badmission polic(y|ies)\b",
    r"\badmission rules?\b",
    r"\badmission requirements?\b",
    r"\badmission criteria\b",
    r"\beligibility criteria\b",
    r"\badmission form\b",
    r"\badmission test\b",
    r"\bentrance test\b",
    r"\badmission fee\b",
    r"\badmission dates?\b",
    r"\badmission documents?\b",

    # =========================================================
    # FEES / FEE POLICY
    # =========================================================

    r"\bfee polic(y|ies)\b",
    r"\bfee payment\b",
    r"\bfee payment system\b",
    r"\bfee structure\b",
    r"\bschool fees?\b",
    r"\btuition fees?\b",
    r"\bfee rules?\b",
    r"\bfee deadline\b",
    r"\bfee due date\b",
    r"\blate fee\b",
    r"\blate payment\b",
    r"\bfee fine\b",
    r"\bfee concession\b",
    r"\bfee refund\b",
    r"\brefund polic(y|ies)\b",
    r"\bpayment method\b",
    r"\bpayment methods\b",

    # =========================================================
    # EXAMINATION / GENERAL EXAM RULES
    # =========================================================

    r"\bexam rules?\b",
    r"\bexamination rules?\b",
    r"\bexam polic(y|ies)\b",
    r"\bexamination polic(y|ies)\b",
    r"\bexam regulations?\b",
    r"\bexam guidelines?\b",
    r"\bexamination guidelines?\b",
    r"\bexam instructions?\b",
    r"\bexam eligibility\b",
    r"\bexam requirements?\b",
    r"\bexam timetable\b",
    r"\bexam schedule\b",
    r"\btest rules?\b",
    r"\bquestion paper\b",
    r"\banswer sheet\b",
    r"\bexam hall\b",
    r"\bexamination hall\b",
    r"\bexam misconduct\b",
    r"\bcheating\b",
    r"\bexam malpractice\b",

    # =========================================================
    # PROMOTION / PASSING / ACADEMIC RULES
    # =========================================================

    r"\bpromotion polic(y|ies)\b",
    r"\bpromotion rules?\b",
    r"\bpromotion criteria\b",
    r"\bpromotion requirements?\b",
    r"\bpassing criteria\b",
    r"\bpass criteria\b",
    r"\bpass percentage\b",
    r"\bpassing marks\b",
    r"\bminimum marks\b",
    r"\bacademic requirements?\b",
    r"\bacademic criteria\b",
    r"\bfailed\b",
    r"\bfail(ed|ure)?\b",
    r"\bdetention\b",
    r"\brepeat(ing)? a class\b",

    # =========================================================
    # HOMEWORK / ASSIGNMENTS - GENERAL SCHOOL POLICY
    # =========================================================

    r"\bhomework polic(y|ies)\b",
    r"\bhomework rules?\b",
    r"\bassignment polic(y|ies)\b",
    r"\bassignment rules?\b",
    r"\bhomework guidelines?\b",
    r"\bassignment guidelines?\b",
    r"\bhomework requirements?\b",

    # =========================================================
    # COMPUTER / COMPUTER LAB
    # =========================================================

    r"\bcomputer lab\b",
    r"\bcomputer laborator(y|ies)\b",
    r"\bcomputer lab rules?\b",
    r"\bcomputer rules?\b",
    r"\blab rules?\b",
    r"\blaboratory rules?\b",
    r"\binternet usage\b",
    r"\binternet rules?\b",
    r"\bonline games?\b",
    r"\bpersonal files?\b",
    r"\bcomputer usage\b",

    # =========================================================
    # SCIENCE LABS / OTHER LABS
    # =========================================================

    r"\bscience lab\b",
    r"\bphysics lab\b",
    r"\bchemistry lab\b",
    r"\bbiology lab\b",
    r"\bbiotechnology lab\b",
    r"\bmathematics lab\b",
    r"\blaboratory safety\b",
    r"\blab safety\b",
    r"\blab safety rules?\b",
    r"\blaboratory safety rules?\b",
    r"\blab equipment\b",
    r"\blaboratory equipment\b",

    # =========================================================
    # TRANSPORT / SCHOOL BUS
    # =========================================================

    r"\bschool bus\b",
    r"\bbus rules?\b",
    r"\bbus polic(y|ies)\b",
    r"\btransport rules?\b",
    r"\bschool transport\b",
    r"\bbus timings?\b",
    r"\bbus stop\b",
    r"\bbus safety\b",
    r"\btransportation\b",

    # =========================================================
    # ID CARD / ALMANAC / SCHOOL DOCUMENTS
    # =========================================================

    r"\bid card\b",
    r"\bschool id\b",
    r"\bstudent id\b",
    r"\balmanac\b",
    r"\bschool diary\b",
    r"\bschool diary rules?\b",
    r"\bdiary rules?\b",
    r"\bdocuments required\b",
    r"\bschool documents?\b",

    # =========================================================
    # MOBILE PHONES / ELECTRONIC DEVICES
    # =========================================================

    r"\bmobile phone\b",
    r"\bmobile phones\b",
    r"\bphone rules?\b",
    r"\bphone polic(y|ies)\b",
    r"\belectronic devices?\b",
    r"\belectronic gadgets?\b",
    r"\bgadgets?\b",
    r"\bsmartphone\b",
    r"\bipod\b",
    r"\bheadphones?\b",
    r"\bvaluable articles?\b",

    # =========================================================
    # FACILITIES / SCHOOL PROPERTY
    # =========================================================

    r"\bschool facilit(y|ies)\b",
    r"\bschool infrastructure\b",
    r"\bschool campus\b",
    r"\bschool building\b",
    r"\bclassroom rules?\b",
    r"\bclassroom polic(y|ies)\b",
    r"\bsmart class\b",
    r"\bauditorium\b",
    r"\bplayground\b",
    r"\bsports facilit(y|ies)\b",
    r"\blaborator(y|ies)\b",
    r"\bcomputer room\b",
    r"\bsmart classroom\b",

    # =========================================================
    # DAMAGE / LOSS / PROPERTY
    # =========================================================

    r"\bdamage to school property\b",
    r"\bschool property\b",
    r"\bproperty damage\b",
    r"\bvandalism\b",
    r"\bdamage fine\b",
    r"\bproperty fine\b",
    r"\blost property\b",
    r"\blost and found\b",
    r"\blost items?\b",
    r"\bdamaged items?\b",

    # =========================================================
    # SPORTS / ACTIVITIES
    # =========================================================

    r"\bsports rules?\b",
    r"\bsports polic(y|ies)\b",
    r"\bphysical education\b",
    r"\bpe rules?\b",
    r"\bsports activities\b",
    r"\bextracurricular activities\b",
    r"\bco-curricular activities\b",
    r"\bcultural activities\b",
    r"\bschool activities\b",

    # =========================================================
    # CLUBS / EVENTS / COMPETITIONS
    # =========================================================

    r"\bschool clubs?\b",
    r"\bclub rules?\b",
    r"\bschool events?\b",
    r"\bschool function\b",
    r"\bschool functions\b",
    r"\bcompetitions?\b",
    r"\binter-school\b",
    r"\bannual day\b",
    r"\bsports day\b",
    r"\bfest\b",
    r"\bcelebration\b",

    # =========================================================
    # MEDICAL / HEALTH / SAFETY - SCHOOL POLICY
    # =========================================================

    r"\bschool safety\b",
    r"\bsafety rules?\b",
    r"\bsafety polic(y|ies)\b",
    r"\bhealth polic(y|ies)\b",
    r"\bmedical polic(y|ies)\b",
    r"\bfirst aid\b",
    r"\bmedical room\b",
    r"\bschool nurse\b",
    r"\bemergency procedures?\b",
    r"\bemergency rules?\b",
    r"\bfire safety\b",
    r"\bfire drill\b",

    # =========================================================
    # PARENT / SCHOOL COMMUNICATION
    # =========================================================

    r"\bparent rules?\b",
    r"\bparent guidelines?\b",
    r"\bparent polic(y|ies)\b",
    r"\bparent teacher\b",
    r"\bparent-teacher\b",
    r"\bptm\b",
    r"\bparent meeting\b",
    r"\bcommunication polic(y|ies)\b",
    r"\bschool communication\b",

    # =========================================================
    # GENERAL SCHOOL INFORMATION
    # =========================================================

    r"\bschool information\b",
    r"\babout the school\b",
    r"\bschool details\b",
    r"\bgeneral school information\b",
    r"\bschool procedure\b",
    r"\bschool procedures\b",
    r"\bschool process\b",
    r"\bschool processes\b",
    r"\bschool requirements\b",
    r"\bwhat does the school say\b",
    r"\baccording to school rules\b",
    r"\baccording to school policy\b",
    r"\baccording to the handbook\b",
]

    if any(
        re.search(pattern, question_lower)
        for pattern in rag_patterns
    ):

        result = {
            "tool": "rag_tool",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 1.0
        }

        print("\n========== ROUTER RESULT ==========")
        print(result)
        print("===================================")

        return result

    # =========================================================
    # NORMAL LLM ROUTING
    # =========================================================

    prompt = TOOL_ROUTER_PROMPT.format(
        question=question
    )

    response = llm.invoke(prompt)

    content = response.content.strip()

    print("\n========== ROUTER RAW RESPONSE ==========")
    print(content)
    print("==========================================")

    # --------------------------------------------------
    # Clean markdown code fences
    # --------------------------------------------------

    content = re.sub(
        r"```json|```",
        "",
        content,
        flags=re.IGNORECASE
    ).strip()

    # --------------------------------------------------
    # Extract JSON object from LLM response
    # --------------------------------------------------

    match = re.search(
        r"\{[\s\S]*\}",
        content
    )

    if not match:

        print("Router returned invalid JSON.")

        return {
            "tool": "general_chat",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 0.0
        }

    json_text = match.group(0)

    try:
        result = json.loads(json_text)

    except json.JSONDecodeError as e:

        print("JSON parsing error:", e)
        print("Extracted JSON:", json_text)

        return {
            "tool": "general_chat",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 0.0
        }

    # --------------------------------------------------
    # Extract fields
    # --------------------------------------------------

    tool = result.get("tool")
    subject = result.get("subject")
    exam = result.get("exam")
    day = result.get("day")
    status = result.get("status")
    metric = result.get("metric")

    # --------------------------------------------------
    # Validate tool
    # --------------------------------------------------

    if tool not in VALID_TOOLS:

        tool = "general_chat"

        subject = None
        exam = None
        day = None
        status = None
        metric = None

        confidence = 0.0

    else:

        # Validate metric
        if metric not in VALID_METRICS:
            metric = None

        confidence = 1.0

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    final_result = {
        "tool": tool,
        "subject": subject,
        "exam": exam,
        "day": day,
        "status": status,
        "metric": metric,
        "confidence": confidence
    }

    print("\n========== ROUTER RESULT ==========")
    print(final_result)
    print("===================================")

    return final_result