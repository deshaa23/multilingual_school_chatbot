from collections import defaultdict


# -------------------------
# MARKS
# -------------------------
def format_marks(results, language="ENGLISH"):

    if not results:

        if language.upper() == "HINDI":
            return "मुझे आपके अंक नहीं मिले।"

        elif language.upper() == "HINGLISH":
            return "Mujhe aapke marks nahi mile."

        return "I couldn't find your marks."

    exams = defaultdict(list)

    for row in results:
        exams[row["exam_name"]].append(
            (
                row["subject_name"],
                int(row["marks_obtained"]),
                int(row["maximum_marks"])
            )
        )

    # ---------- English ----------
    if language.upper() == "ENGLISH":

        output = "Marks\n\n"

        for exam, subjects in exams.items():

            output += f"{exam}:\n"

            for subject, marks, maximum in subjects:
                output += f"• {subject}: {marks}/{maximum}\n"

            output += "\n"

        return output.strip()

    # ---------- Hindi ----------
    elif language.upper() == "HINDI":

        subject_map = {
            "Mathematics": "गणित",
            "English": "अंग्रेज़ी",
            "Science": "विज्ञान",
            "Social Science": "सामाजिक विज्ञान",
            "Computer Science": "कंप्यूटर विज्ञान",
        }

        exam_map = {
            "Mid Term": "मिड टर्म",
            "Final Examination": "वार्षिक परीक्षा",
            "Final Term": "वार्षिक परीक्षा",
            "Unit Test": "यूनिट टेस्ट",
            "Mid Term Examination": "मध्यावधि परीक्षा",
        }

        output = "अंक\n\n"

        for exam, subjects in exams.items():

            output += f"{exam_map.get(exam, exam)}:\n"

            for subject, marks, maximum in subjects:

                subject = subject_map.get(subject, subject)

                output += f"• {subject}: {marks}/{maximum}\n"

            output += "\n"

        return output.strip()

    # ---------- Hinglish ----------
    else:

        output = "Marks\n\n"

        for exam, subjects in exams.items():

            output += f"{exam}:\n"

            for subject, marks, maximum in subjects:

                if subject == "Mathematics":
                    subject = "Maths"

                output += f"• {subject}: {marks}/{maximum}\n"

            output += "\n"

        return output.strip()


# -------------------------
# ATTENDANCE
# -------------------------
def format_attendance(results, language="ENGLISH"):

    if not results:

        if language.upper() == "HINDI":
            return "उपस्थिति का रिकॉर्ड नहीं मिला।"

        elif language.upper() == "HINGLISH":
            return "Attendance record nahi mila."

        return "No attendance records found."

    status_hindi = {
        "present": "उपस्थित",
        "absent": "अनुपस्थित",
        "late": "देर से"
    }

    status_hinglish = {
        "present": "Present",
        "absent": "Absent",
        "late": "Late"
    }

    if language.upper() == "ENGLISH":

        output = "Attendance\n\n"

        for row in results:

            output += (
                f"• {row['attendance_date']} : "
                f"{row['status'].capitalize()}\n"
            )

        return output

    elif language.upper() == "HINDI":

        output = "उपस्थिति\n\n"

        for row in results:

            output += (
                f"• {row['attendance_date']} : "
                f"{status_hindi.get(row['status'], row['status'])}\n"
            )

        return output

    else:

        output = "Attendance\n\n"

        for row in results:

            output += (
                f"• {row['attendance_date']} : "
                f"{status_hinglish.get(row['status'], row['status'])}\n"
            )

        return output

# -------------------------
# TIMETABLE
# -------------------------
def format_timetable(results, language="ENGLISH"):

    if not results:

        if language.upper() == "HINDI":
            return "समय-सारणी उपलब्ध नहीं है।"

        elif language.upper() == "HINGLISH":
            return "Timetable available nahi hai."

        return "No timetable found."

    day_map = {
        "Monday": "सोमवार",
        "Tuesday": "मंगलवार",
        "Wednesday": "बुधवार",
        "Thursday": "गुरुवार",
        "Friday": "शुक्रवार",
        "Saturday": "शनिवार"
    }

    subject_map = {
        "Mathematics": "गणित",
        "English": "अंग्रेज़ी",
        "Science": "विज्ञान",
        "Social Science": "सामाजिक विज्ञान",
        "Hindi": "हिन्दी"
    }

    title = {
        "ENGLISH": "Timetable",
        "HINDI": "समय-सारणी",
        "HINGLISH": "Timetable"
    }

    output = title.get(language.upper(), "Timetable") + "\n\n"

    current_day = ""

    for row in results:

        day = row["day_of_week"]
        subject = row["subject_name"]

        if language.upper() == "HINDI":
            day = day_map.get(day, day)
            subject = subject_map.get(subject, subject)

        elif language.upper() == "HINGLISH":
            if subject == "Mathematics":
                subject = "Maths"

        if day != current_day:
            current_day = day
            output += f"{day}\n"

        output += (
            f"• {row['start_time']} - {row['end_time']} : {subject}\n"
        )

    return output.strip()


# -------------------------
# ASSIGNMENTS
# -------------------------
def format_assignments(results, language="ENGLISH"):

    if not results:

        if language.upper() == "HINDI":
            return "कोई असाइनमेंट उपलब्ध नहीं है।"

        elif language.upper() == "HINGLISH":
            return "Koi assignment available nahi hai."

        return "No assignments found."

    if language.upper() == "ENGLISH":

        output = "Assignments\n\n"

        for row in results:

            output += (
                f"{row['title']}\n"
                f"Description: {row['description']}\n"
                f"Due Date: {row['due_date']}\n\n"
            )

        return output.strip()

    elif language.upper() == "HINDI":

        output = "असाइनमेंट\n\n"

        for row in results:

            output += (
                f"{row['title']}\n"
                f"विवरण: {row['description']}\n"
                f"अंतिम तिथि: {row['due_date']}\n\n"
            )

        return output.strip()

    else:

        output = "Assignments\n\n"

        for row in results:

            output += (
                f"{row['title']}\n"
                f"Description: {row['description']}\n"
                f"Due Date: {row['due_date']}\n\n"
            )

        return output.strip()
# -------------------------
# TEACHER
# -------------------------
def format_teacher(results, language):

    if not results:
        return (
            "No class teacher found."
            if language == "ENGLISH"
            else "कक्षा शिक्षक नहीं मिले।"
        )

    teacher = results[0]

    if language == "ENGLISH":
        return (
            
            f"{teacher['first_name']} {teacher['last_name']}"
        )
        
    elif language == "HINGLISH":
            return (
                
                f"{teacher['first_name']} {teacher['last_name']}"
            )

    return (
    
        f"{teacher['first_name']} {teacher['last_name']}"
    )
    

def format_class(results, language="ENGLISH"):

    if not results:

        if language.upper() == "HINDI":
            return "कक्षा की जानकारी उपलब्ध नहीं है।"

        elif language.upper() == "HINGLISH":
            return "Class information available nahi hai."

        return "Class information not found."

    row = results[0]

    if language.upper() == "HINDI":

        return (
            "कक्षा\n\n"
            f"कक्षा: {row['class_name']}-{row['section']}"
        )

    elif language.upper() == "HINGLISH":

        return (
            "Class\n\n"
            f"Class: {row['class_name']}-{row['section']}"
        )

    return (
        "Class\n\n"
        f"Class: {row['class_name']}-{row['section']}"
    )
    
def format_profile(results, language="ENGLISH"):

    if not results:
        return (
            "No profile found."
            if language.upper() == "ENGLISH"
            else "प्रोफ़ाइल नहीं मिली।"
        )

    row = results[0]

    # ---------- Roll Number ----------
    if list(row.keys()) == ["roll_number"]:
        if language.upper() == "ENGLISH":
            return f"Your roll number is {row['roll_number']}."
        elif language.upper() == "HINGLISH":
            return f"Aapka roll number {row['roll_number']} hai."
        else:
            return f"आपका रोल नंबर {row['roll_number']} है।"

    # ---------- Admission Number ----------
    if list(row.keys()) == ["admission_number"]:
        if language.upper() == "ENGLISH":
            return f"Your admission number is {row['admission_number']}."
        elif language.upper() == "HINGLISH":
            return f"Aapka admission number {row['admission_number']} hai."
        else:
            return f"आपका प्रवेश संख्या {row['admission_number']} है।"

    # ---------- DOB ----------
    if list(row.keys()) == ["date_of_birth"]:
        if language.upper() == "ENGLISH":
            return f"Your date of birth is {row['date_of_birth']}."
        elif language.upper() == "HINGLISH":
            return f"Aapki date of birth {row['date_of_birth']} hai."
        else:
            return f"आपकी जन्म तिथि {row['date_of_birth']} है।"

    # ---------- Full Profile ----------
    if language.upper() == "ENGLISH":
        return f"""
Name: {row['first_name']} {row['last_name']}
Admission Number: {row['admission_number']}
Roll Number: {row['roll_number']}
Class: {row['class_name']} - {row['section']}
Date of Birth: {row['date_of_birth']}
Gender: {row['gender']}
""".strip()

    elif language.upper() == "HINGLISH":
        return f"""
Name: {row['first_name']} {row['last_name']}
Admission Number: {row['admission_number']}
Roll Number: {row['roll_number']}
Class: {row['class_name']} - {row['section']}
Date of Birth: {row['date_of_birth']}
Gender: {row['gender']}
""".strip()

    else:
        return f"""
नाम: {row['first_name']} {row['last_name']}
प्रवेश संख्या: {row['admission_number']}
रोल नंबर: {row['roll_number']}
कक्षा: {row['class_name']} - {row['section']}
जन्म तिथि: {row['date_of_birth']}
लिंग: {row['gender']}
""".strip()

def format_performance(results, language="english"):

    if not results:
        return "I could not find enough data to analyze your performance."

    row = results[0]

    average = row.get("average_marks")

    if average is None:
        return "I could not calculate your overall performance."

    average = float(average)

    if average >= 90:
        level = "excellent"
    elif average >= 80:
        level = "very good"
    elif average >= 70:
        level = "good"
    elif average >= 60:
        level = "fair"
    else:
        level = "needs improvement"

    return (
        f"Based on your marks, your overall average is "
        f"{average:.1f}/100.\n\n"
        f"Overall performance: {level.capitalize()}."
    )