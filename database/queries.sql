-- ==========================================
-- 1. Show all students
-- ==========================================

SELECT
    student_id,
    first_name,
    last_name,
    roll_number
FROM students
ORDER BY student_id;

-- ==========================================
-- 2. Student Details with Class
-- ==========================================

SELECT
    s.student_id,
    s.first_name,
    s.last_name,
    c.class_name,
    c.section
FROM students s
JOIN classes c
ON s.class_id = c.class_id
ORDER BY s.student_id;

-- ==========================================
-- 3. Show Teachers
-- ==========================================

SELECT
    teacher_id,
    first_name,
    last_name,
    email
FROM teachers;

-- ==========================================
-- 4. Students in Class 10A
-- ==========================================

SELECT
    s.roll_number,
    s.first_name,
    s.last_name
FROM students s
JOIN classes c
ON s.class_id = c.class_id
WHERE c.class_name = '10'
AND c.section = 'A'
ORDER BY s.roll_number;

-- ==========================================
-- 5. Rahul's Attendance
-- ==========================================

SELECT
    s.first_name,
    s.last_name,
    a.attendance_date,
    a.status
FROM attendance a
JOIN students s
ON a.student_id = s.student_id
WHERE s.first_name = 'Rahul'
ORDER BY a.attendance_date;

-- ==========================================
-- 6. Rahul's Marks
-- ==========================================

SELECT
    s.first_name,
    sub.subject_name,
    e.exam_name,
    m.marks_obtained,
    m.maximum_marks
FROM marks m
JOIN students s
ON m.student_id = s.student_id
JOIN class_subjects cs
ON m.class_subject_id = cs.class_subject_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
JOIN exams e
ON m.exam_id = e.exam_id
WHERE s.first_name = 'Rahul'
ORDER BY e.exam_name, sub.subject_name;

-- ==========================================
-- 7. Assignments for Class 10A
-- ==========================================

SELECT
    a.title,
    a.due_date,
    sub.subject_name
FROM assignments a
JOIN class_subjects cs
ON a.class_subject_id = cs.class_subject_id
JOIN classes c
ON cs.class_id = c.class_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
WHERE c.class_name = '10'
AND c.section = 'A'
ORDER BY a.due_date;

-- ==========================================
-- 8. Rahul's Attendance Percentage
-- ==========================================

SELECT
    s.first_name,
    ROUND(
        COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0
        / COUNT(*),
        2
    ) AS attendance_percentage
FROM students s
JOIN attendance a
ON s.student_id = a.student_id
WHERE s.first_name = 'Rahul'
GROUP BY s.first_name;

-- ==========================================
-- 9. Rahul's Average Marks
-- ==========================================

SELECT
    s.first_name,
    ROUND(AVG(m.marks_obtained), 2) AS average_marks
FROM students s
JOIN marks m
ON s.student_id = m.student_id
WHERE s.first_name = 'Rahul'
GROUP BY s.first_name;

-- ==========================================
-- 10. Topper in Mathematics
-- ==========================================

SELECT
    s.first_name,
    s.last_name,
    sub.subject_name,
    MAX(m.marks_obtained) AS highest_marks
FROM marks m
JOIN students s
ON m.student_id = s.student_id
JOIN class_subjects cs
ON m.class_subject_id = cs.class_subject_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
WHERE sub.subject_name = 'Mathematics'
GROUP BY
    s.student_id,
    s.first_name,
    s.last_name,
    sub.subject_name
ORDER BY highest_marks DESC
LIMIT 1;

-- ==========================================
-- 11. Timetable for Class 10A
-- ==========================================

SELECT
    c.class_name,
    c.section,
    sub.subject_name,
    t.day_of_week,
    t.start_time,
    t.end_time,
    t.room_number
FROM timetable t
JOIN class_subjects cs
ON t.class_subject_id = cs.class_subject_id
JOIN classes c
ON cs.class_id = c.class_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
WHERE c.class_name = '10'
AND c.section = 'A'
ORDER BY t.start_time;

-- ==========================================
-- 12. Show All Announcements
-- ==========================================

SELECT
    title,
    message,
    posted_at
FROM announcements
ORDER BY posted_at DESC;

-- ==========================================
-- 13. Get Student Details by Student ID
-- ==========================================

SELECT
    s.student_id,
    s.first_name,
    s.last_name,
    s.roll_number,
    c.class_name,
    c.section
FROM students s
JOIN classes c
ON s.class_id = c.class_id
WHERE s.student_id = %s;

-- ==========================================
-- 14. Get Attendance by Student ID
-- ==========================================

SELECT
    attendance_date,
    status
FROM attendance
WHERE student_id = %s
ORDER BY attendance_date;

-- ==========================================
-- 15. Get Marks by Student ID
-- ==========================================

SELECT
    sub.subject_name,
    e.exam_name,
    m.marks_obtained,
    m.maximum_marks
FROM marks m
JOIN class_subjects cs
ON m.class_subject_id = cs.class_subject_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
JOIN exams e
ON m.exam_id = e.exam_id
WHERE m.student_id = %s
ORDER BY e.exam_name, sub.subject_name;

-- ==========================================
-- 16. Get Timetable by Class
-- ==========================================

SELECT
    sub.subject_name,
    t.day_of_week,
    t.start_time,
    t.end_time,
    t.room_number
FROM timetable t
JOIN class_subjects cs
ON t.class_subject_id = cs.class_subject_id
JOIN classes c
ON cs.class_id = c.class_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
WHERE c.class_name = %s
AND c.section = %s
ORDER BY t.day_of_week, t.start_time;

-- ==========================================
-- 17. Get Assignments by Class
-- ==========================================

SELECT
    sub.subject_name,
    a.title,
    a.description,
    a.due_date
FROM assignments a
JOIN class_subjects cs
ON a.class_subject_id = cs.class_subject_id
JOIN classes c
ON cs.class_id = c.class_id
JOIN subjects sub
ON cs.subject_id = sub.subject_id
WHERE c.class_name = %s
AND c.section = %s
ORDER BY a.due_date;