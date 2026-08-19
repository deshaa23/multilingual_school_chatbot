-- ==========================================
-- SCHOOL CHATBOT DATABASE SAMPLE DATA
-- ==========================================
TRUNCATE TABLE
announcements,
timetable,
assignments,
marks,
attendance,
parent_students,
parents,
students,
class_subjects,
exams,
teachers,
users,
subjects,
classes
RESTART IDENTITY CASCADE;


-- ==========================================
-- USERS
-- ==========================================

INSERT INTO users (email, password_hash, role)
VALUES
('admin@school.com', '$2b$admin123', 'admin'),

('anita.sharma@school.com', '$2b$teacher1', 'teacher'),
('raj.gupta@school.com', '$2b$teacher2', 'teacher'),
('meera.patel@school.com', '$2b$teacher3', 'teacher'),

('rahul@student.com', '$2b$student1', 'student'),
('priya@student.com', '$2b$student2', 'student'),
('aman@student.com', '$2b$student3', 'student'),
('riya@student.com', '$2b$student4', 'student'),
('arjun@student.com', '$2b$student5', 'student'),
('neha@student.com', '$2b$student6', 'student'),
('vivek@student.com', '$2b$student7', 'student'),
('sneha@student.com', '$2b$student8', 'student'),

('rajesh@parent.com', '$2b$parent1', 'parent'),
('sunita@parent.com', '$2b$parent2', 'parent'),
('anita@parent.com', '$2b$parent3', 'parent'),

('atul@student.com','$2b$student9','student'),
('pooja@student.com','$2b$student10','student'),
('rohit@student.com','$2b$student11','student'),
('kavya@student.com','$2b$student12','student'),
('yash@student.com','$2b$student13','student'),
('isha@student.com','$2b$student14','student'),
('karan@student.com','$2b$student15','student'),
('megha@student.com','$2b$student16','student'),
('nikhil@student.com','$2b$student17','student'),
('divya@student.com','$2b$student18','student'),
('akash@student.com','$2b$student19','student'),
('muskan@student.com','$2b$student20','student');
-- ==========================================
-- CLASSES
-- ==========================================

INSERT INTO classes (class_name, section, academic_year)
VALUES
('9', 'A', '2026-27'),
('9', 'B', '2026-27'),
('10', 'A', '2026-27'),
('10', 'B', '2026-27');

-- ==========================================
-- TEACHERS
-- ==========================================

INSERT INTO teachers
(user_id, first_name, last_name, email, phone, hire_date)
VALUES
(2, 'Anita', 'Sharma', 'anita.sharma@school.com', '9876543210', '2020-06-15'),

(3, 'Raj', 'Gupta', 'raj.gupta@school.com', '9876543211', '2019-07-01'),

(4, 'Meera', 'Patel', 'meera.patel@school.com', '9876543212', '2021-03-10');

-- ==========================================
-- SUBJECTS
-- ==========================================

INSERT INTO subjects (subject_name, subject_code)
VALUES
('Mathematics', 'MATH101'),
('Science', 'SCI101'),
('English', 'ENG101'),
('Social Science', 'SST101'),
('Computer Science', 'CS101');

-- ==========================================
-- STUDENTS
-- ==========================================

INSERT INTO students
(user_id, class_id, roll_number, first_name, last_name, date_of_birth, gender, admission_date, admission_number)
VALUES
(5, 3, 1, 'Rahul', 'Verma', '2010-05-12', 'Male', '2021-04-01', 'ADM2026000'),

(6, 3, 2, 'Priya', 'Singh', '2010-08-22', 'Female', '2021-04-01', 'ADM2023001'),

(7, 4, 1, 'Aman', 'Kumar', '2010-02-18', 'Male', '2021-04-01', 'ADM2006001'),

(8, 4, 2, 'Riya', 'Shah', '2010-11-10', 'Female', '2021-04-01', 'ADM2025001'),

(9, 1, 1, 'Arjun', 'Patel', '2011-01-25', 'Male', '2022-04-01','ADM2026005'),

(10, 1, 2, 'Neha', 'Joshi', '2011-07-30', 'Female', '2022-04-01','ADM2026009'),

(11, 2, 1, 'Vivek', 'Mehta', '2011-03-15', 'Male', '2022-04-01','ADM2022001'),

(12, 2, 2, 'Sneha', 'Nair', '2011-09-05', 'Female', '2022-04-01', 'ADM2016001'),

(13,3,3,'Atul','Sharma','2010-04-12','Male','2021-04-01','ADM2026010'),

(14,3,4,'Pooja','Verma','2010-07-19','Female','2021-04-01','ADM2026011'),

(15,4,3,'Rohit','Mehta','2010-02-11','Male','2021-04-01','ADM2026012'),

(16,4,4,'Kavya','Joshi','2010-11-03','Female','2021-04-01','ADM2026013'),

(17,1,3,'Yash','Patil','2011-03-18','Male','2022-04-01','ADM2026014'),

(18,1,4,'Isha','Nair','2011-08-20','Female','2022-04-01','ADM2026015'),

(19,2,3,'Karan','Gupta','2011-01-28','Male','2022-04-01','ADM2026016'),

(20,2,4,'Megha','Singh','2011-10-15','Female','2022-04-01','ADM2026017'),

(21,3,5,'Nikhil','Patel','2010-06-09','Male','2021-04-01','ADM2026018'),

(22,3,6,'Divya','Kulkarni','2010-09-25','Female','2021-04-01','ADM2026019'),

(23,4,5,'Akash','Shah','2010-12-14','Male','2021-04-01','ADM2026020'),

(24,4,6,'Muskan','Desai','2010-05-30','Female','2021-04-01','ADM2026021');

-- ==========================================
-- PARENTS
-- ==========================================

INSERT INTO parents
(user_id, first_name, last_name, email, phone)
VALUES
(25, 'Rajesh', 'Verma', 'rajesh@parent.com', '9876500001'),
(26, 'Sunita', 'Singh', 'sunita@parent.com', '9876500002'),
(27, 'Anita', 'Patel', 'anita@parent.com', '9876500003'),
(28,'Mahesh','Sharma','mahesh@parent.com','9876500010'),
(29,'Seema','Verma','seema@parent.com','9876500011'),
(30,'Deepak','Mehta','deepak@parent.com','9876500012'),
(31,'Rekha','Joshi','rekha@parent.com','9876500013'),
(32,'Manoj','Patil','manoj@parent.com','9876500014'),
(33,'Kiran','Nair','kiran@parent.com','9876500015'),
(34,'Ramesh','Gupta','ramesh@parent.com','9876500016'),
(35,'Pooja','Singh','pooja2@parent.com','9876500017'),
(36,'Vijay','Patel','vijay@parent.com','9876500018'),
(37,'Swati','Kulkarni','swati@parent.com','9876500019'),
(38,'Amit','Shah','amit@parent.com','9876500020'),
(39,'Jyoti','Desai','jyoti@parent.com','9876500021');

-- ==========================================
-- PARENT_STUDENTS
-- ==========================================
INSERT INTO parent_students
(parent_id, student_id, relationship)
VALUES

-- Parent 1 → 2 children
(1,1,'Father'),
(1,4,'Father'),

-- Parent 2 → 2 children
(2,2,'Mother'),
(2,6,'Mother'),

-- Parent 3 → 2 children
(3,3,'Mother'),
(3,5,'Mother'),

-- Parent 4 → 1 child
(4,7,'Father'),

-- Parent 5 → 1 child
(5,8,'Mother'),

-- Parent 6 → 2 children
(6,9,'Father'),
(6,10,'Father'),

-- Parent 7 → 2 children
(7,11,'Mother'),
(7,12,'Mother'),

-- Parent 8 → 1 child
(8,13,'Father'),

-- Parent 9 → 1 child
(9,14,'Mother'),

-- Parent 10 → 2 children
(10,15,'Father'),
(10,16,'Father'),

-- Parent 11 → 1 child
(11,17,'Mother'),

-- Parent 12 → 1 child
(12,18,'Father'),

-- Parent 13 → 1 child
(13,19,'Mother'),

-- Parent 14 → 1 child
(14,20,'Father');


-- ==========================================
-- CLASS SUBJECTS
-- ==========================================

INSERT INTO class_subjects (class_id, subject_id, teacher_id)
VALUES

-- Class 9A
(1,1,1),
(1,2,2),
(1,3,3),
(1,4,1),
(1,5,2),

-- Class 9B
(2,1,1),
(2,2,2),
(2,3,3),
(2,4,1),
(2,5,2),

-- Class 10A
(3,1,1),
(3,2,2),
(3,3,3),
(3,4,1),
(3,5,2),

-- Class 10B
(4,1,1),
(4,2,2),
(4,3,3),
(4,4,1),
(4,5,2);

-- ==========================================
-- EXAMS
-- ==========================================

INSERT INTO exams
(exam_name, academic_year, start_date, end_date)
VALUES
('Mid Term Examination', '2026-27', '2026-09-15', '2026-09-22'),

('Final Examination', '2026-27', '2027-02-20', '2027-02-28');


-- ==========================================
-- ATTENDANCE
-- ==========================================

INSERT INTO attendance
(student_id, attendance_date, status)
VALUES
-- 2026-09-15
(1,'2026-09-15','present'),
(2,'2026-09-15','present'),
(3,'2026-09-15','late'),
(4,'2026-09-15','present'),
(5,'2026-09-15','absent'),
(6,'2026-09-15','present'),
(7,'2026-09-15','present'),
(8,'2026-09-15','present'),
(9,'2026-09-15','present'),
(10,'2026-09-15','present'),
(11,'2026-09-15','late'),
(12,'2026-09-15','present'),
(13,'2026-09-15','present'),
(14,'2026-09-15','absent'),
(15,'2026-09-15','present'),
(16,'2026-09-15','present'),
(17,'2026-09-15','late'),
(18,'2026-09-15','present'),
(19,'2026-09-15','present'),
(20,'2026-09-15','present'),


-- 2026-09-16
(1,'2026-09-16','present'),
(2,'2026-09-16','absent'),
(3,'2026-09-16','present'),
(4,'2026-09-16','present'),
(5,'2026-09-16','present'),
(6,'2026-09-16','late'),
(7,'2026-09-16','present'),
(8,'2026-09-16','present'),
(9,'2026-09-16','present'),
(10,'2026-09-16','late'),
(11,'2026-09-16','present'),
(12,'2026-09-16','present'),
(13,'2026-09-16','present'),
(14,'2026-09-16','present'),
(15,'2026-09-16','absent'),
(16,'2026-09-16','present'),
(17,'2026-09-16','present'),
(18,'2026-09-16','late'),
(19,'2026-09-16','present'),
(20,'2026-09-16','present'),


-- 2026-09-17
(1,'2026-09-17','late'),
(2,'2026-09-17','present'),
(3,'2026-09-17','present'),
(4,'2026-09-17','absent'),
(5,'2026-09-17','present'),
(6,'2026-09-17','present'),
(7,'2026-09-17','present'),
(8,'2026-09-17','late'),
(9,'2026-09-17','present'),
(10,'2026-09-17','present'),
(11,'2026-09-17','present'),
(12,'2026-09-17','late'),
(13,'2026-09-17','present'),
(14,'2026-09-17','present'),
(15,'2026-09-17','present'),
(16,'2026-09-17','absent'),
(17,'2026-09-17','present'),
(18,'2026-09-17','present'),
(19,'2026-09-17','late'),
(20,'2026-09-17','present'),


-- 2026-09-18
(1,'2026-09-18','present'),
(2,'2026-09-18','present'),
(3,'2026-09-18','present'),
(4,'2026-09-18','present'),
(5,'2026-09-18','late'),
(6,'2026-09-18','present'),
(7,'2026-09-18','absent'),
(8,'2026-09-18','present'),
(9,'2026-09-18','present'),
(10,'2026-09-18','present'),
(11,'2026-09-18','present'),
(12,'2026-09-18','present'),
(13,'2026-09-18','late'),
(14,'2026-09-18','present'),
(15,'2026-09-18','present'),
(16,'2026-09-18','present'),
(17,'2026-09-18','present'),
(18,'2026-09-18','absent'),
(19,'2026-09-18','present'),
(20,'2026-09-18','present'),

-- 2026-09-19
(1,'2026-09-19','present'),
(2,'2026-09-19','present'),
(3,'2026-09-19','present'),
(4,'2026-09-19','late'),
(5,'2026-09-19','present'),
(6,'2026-09-19','present'),
(7,'2026-09-19','present'),
(8,'2026-09-19','absent'),
(9,'2026-09-19','present'),
(10,'2026-09-19','present'),
(11,'2026-09-19','late'),
(12,'2026-09-19','present'),
(13,'2026-09-19','present'),
(14,'2026-09-19','present'),
(15,'2026-09-19','present'),
(16,'2026-09-19','present'),
(17,'2026-09-19','absent'),
(18,'2026-09-19','present'),
(19,'2026-09-19','present'),
(20,'2026-09-19','late');

-- ==========================================
-- MARKS
-- ==========================================

INSERT INTO marks
(student_id, class_subject_id, exam_id, marks_obtained, maximum_marks)
VALUES

-- ==========================================
-- MID TERM (Exam ID = 1)
-- English
-- ==========================================

-- Class 10A
(1,13,1,84,100),
(2,13,1,90,100),
(9,13,1,87,100),
(10,13,1,82,100),
(13,13,1,86,100),
(14,13,1,91,100),

-- Class 10B
(3,18,1,78,100),
(4,18,1,85,100),
(11,18,1,79,100),
(12,18,1,88,100),
(15,18,1,83,100),
(16,18,1,90,100),

-- Class 9A
(5,3,1,89,100),
(6,3,1,85,100),
(17,3,1,80,100),
(18,3,1,91,100),

-- Class 9B
(7,8,1,81,100),
(8,8,1,87,100),
(19,8,1,82,100),
(20,8,1,90,100),

-- ==========================================
-- MID TERM
-- Social Science
-- ==========================================

-- Class 10A
(1,14,1,80,100),
(2,14,1,88,100),
(9,14,1,84,100),
(10,14,1,79,100),
(13,14,1,85,100),
(14,14,1,90,100),

-- Class 10B
(3,19,1,77,100),
(4,19,1,83,100),
(11,19,1,78,100),
(12,19,1,86,100),
(15,19,1,82,100),
(16,19,1,89,100),

-- Class 9A
(5,4,1,86,100),
(6,4,1,82,100),
(17,4,1,79,100),
(18,4,1,88,100),

-- Class 9B
(7,9,1,80,100),
(8,9,1,86,100),
(19,9,1,81,100),
(20,9,1,89,100),

-- ==========================================
-- MID TERM
-- Computer Science
-- ==========================================

-- Class 10A
(1,15,1,93,100),
(2,15,1,96,100),
(9,15,1,91,100),
(10,15,1,88,100),
(13,15,1,92,100),
(14,15,1,97,100),

-- Class 10B
(3,20,1,87,100),
(4,20,1,91,100),
(11,20,1,86,100),
(12,20,1,94,100),
(15,20,1,89,100),
(16,20,1,95,100),

-- Class 9A
(5,5,1,90,100),
(6,5,1,87,100),
(17,5,1,84,100),
(18,5,1,92,100),

-- Class 9B
(7,10,1,86,100),
(8,10,1,90,100),
(19,10,1,87,100),
(20,10,1,93,100),

-- ==========================================
-- MID TERM
-- Science
-- ==========================================

-- Class 10A
(1,12,1,81,100),
(2,12,1,89,100),
(9,12,1,91,100),
(10,12,1,85,100),
(13,12,1,86,100),
(14,12,1,94,100),

-- Class 10B
(3,17,1,76,100),
(4,17,1,80,100),
(11,17,1,80,100),
(12,17,1,88,100),
(15,17,1,83,100),
(16,17,1,88,100),

-- Class 9A
(5,2,1,87,100),
(6,2,1,84,100),
(17,2,1,78,100),
(18,2,1,90,100),

-- Class 9B
(7,7,1,78,100),
(8,7,1,88,100),
(19,7,1,81,100),
(20,7,1,89,100),

-- ==========================================
-- MID TERM (Exam ID = 1)
-- Mathematics
-- ==========================================

-- Class 10A
(1,11,1,88,100),
(2,11,1,91,100),
(9,11,1,87,100),
(10,11,1,79,100),
(13,11,1,84,100),
(14,11,1,92,100),

-- Class 10B
(3,16,1,79,100),
(4,16,1,84,100),
(11,16,1,76,100),
(12,16,1,89,100),
(15,16,1,81,100),
(16,16,1,90,100),

-- Class 9A
(5,1,1,95,100),
(6,1,1,86,100),
(17,1,1,75,100),
(18,1,1,88,100),

-- Class 9B
(7,6,1,82,100),
(8,6,1,90,100),
(19,6,1,83,100),
(20,6,1,91,100),

-- ==========================================
-- FINAL EXAM (Exam ID = 2)
-- English
-- ==========================================

-- Class 10A
(1,13,2,89,100),
(2,13,2,94,100),
(9,13,2,91,100),
(10,13,2,87,100),
(13,13,2,90,100),
(14,13,2,95,100),

-- Class 10B
(3,18,2,84,100),
(4,18,2,89,100),
(11,18,2,83,100),
(12,18,2,92,100),
(15,18,2,87,100),
(16,18,2,94,100),

-- Class 9A
(5,3,2,93,100),
(6,3,2,89,100),
(17,3,2,85,100),
(18,3,2,95,100),

-- Class 9B
(7,8,2,86,100),
(8,8,2,91,100),
(19,8,2,87,100),
(20,8,2,94,100),

-- ==========================================
-- FINAL EXAM
-- Social Science
-- ==========================================

-- Class 10A
(1,14,2,86,100),
(2,14,2,92,100),
(9,14,2,89,100),
(10,14,2,85,100),
(13,14,2,90,100),
(14,14,2,94,100),

-- Class 10B
(3,19,2,82,100),
(4,19,2,88,100),
(11,19,2,84,100),
(12,19,2,91,100),
(15,19,2,86,100),
(16,19,2,93,100),

-- Class 9A
(5,4,2,90,100),
(6,4,2,87,100),
(17,4,2,84,100),
(18,4,2,92,100),

-- Class 9B
(7,9,2,85,100),
(8,9,2,90,100),
(19,9,2,86,100),
(20,9,2,93,100),

-- ==========================================
-- FINAL EXAM
-- Computer Science
-- ==========================================

-- Class 10A
(1,15,2,96,100),
(2,15,2,98,100),
(9,15,2,95,100),
(10,15,2,91,100),
(13,15,2,96,100),
(14,15,2,99,100),

-- Class 10B
(3,20,2,91,100),
(4,20,2,94,100),
(11,20,2,90,100),
(12,20,2,97,100),
(15,20,2,93,100),
(16,20,2,98,100),

-- Class 9A
(5,5,2,94,100),
(6,5,2,91,100),
(17,5,2,88,100),
(18,5,2,95,100),

-- Class 9B
(7,10,2,90,100),
(8,10,2,94,100),
(19,10,2,91,100),
(20,10,2,96,100),

-- ==========================================
-- FINAL EXAM (Exam ID = 2)
-- Mathematics
-- ==========================================

-- Class 10A
(1,11,2,92,100),
(2,11,2,95,100),
(9,11,2,91,100),
(10,11,2,84,100),
(13,11,2,88,100),
(14,11,2,96,100),

-- Class 10B
(3,16,2,84,100),
(4,16,2,89,100),
(11,16,2,82,100),
(12,16,2,93,100),
(15,16,2,86,100),
(16,16,2,94,100),

-- Class 9A
(5,1,2,97,100),
(6,1,2,90,100),
(17,1,2,81,100),
(18,1,2,92,100),

-- Class 9B
(7,6,2,86,100),
(8,6,2,93,100),
(19,6,2,87,100),
(20,6,2,95,100),

-- ==========================================
-- FINAL EXAM
-- Science
-- ==========================================

-- Class 10A
(1,12,2,86,100),
(2,12,2,92,100),
(9,12,2,95,100),
(10,12,2,88,100),
(13,12,2,90,100),
(14,12,2,97,100),

-- Class 10B
(3,17,2,82,100),
(4,17,2,85,100),
(11,17,2,84,100),
(12,17,2,92,100),
(15,17,2,88,100),
(16,17,2,95,100),

-- Class 9A
(5,2,2,91,100),
(6,2,2,89,100),
(17,2,2,86,100),
(18,2,2,90,100),

-- Class 9B
(7,7,2,83,100),
(8,7,2,94,100),
(19,7,2,85,100),
(20,7,2,93,100);

-- ==========================================
-- ASSIGNMENTS
-- ==========================================

INSERT INTO assignments
(class_subject_id, title, description, assigned_date, due_date)
VALUES

-- Class 9A
(1,'Algebra Worksheet','Solve exercises 1-20 from Chapter 3.','2026-08-10','2026-08-17'),
(2,'Science Project','Prepare a working model on Renewable Energy.','2026-08-12','2026-08-22'),
(3,'Essay Writing','Write an essay on Environmental Conservation.','2026-08-15','2026-08-25'),
(4,'History Notes','Complete Chapter 4 notes.','2026-08-18','2026-08-28'),
(5,'C Programming','Write a C program to find factorial.','2026-08-20','2026-08-30'),

-- Class 9B
(6,'Algebra Practice','Solve quadratic equation worksheet.','2026-08-22','2026-08-30'),
(7,'Physics Lab Report','Prepare Motion experiment report.','2026-08-24','2026-09-02'),
(8,'Grammar Practice','Complete English grammar worksheet.','2026-08-26','2026-09-03'),
(9,'Geography Assignment','Prepare India's physical map.','2026-08-28','2026-09-05'),
(10,'HTML Basics','Create a simple HTML webpage.','2026-08-30','2026-09-07'),

-- Class 10A
(11,'Trigonometry Worksheet','Solve Chapter 2 exercises.','2026-09-01','2026-09-08'),
(12,'Chemistry Assignment','Balance chemical equations.','2026-09-02','2026-09-09'),
(13,'Letter Writing','Write a formal letter.','2026-09-03','2026-09-10'),
(14,'Civics Project','Prepare presentation on Indian Constitution.','2026-09-04','2026-09-11'),
(15,'Python Basics','Write a Python program for Fibonacci series.','2026-09-05','2026-09-12'),

-- Class 10B
(16,'Probability Worksheet','Solve probability problems.','2026-09-06','2026-09-13'),
(17,'Biology Assignment','Prepare Human Digestive System diagram.','2026-09-07','2026-09-14'),
(18,'Reading Comprehension','Complete comprehension worksheet.','2026-09-08','2026-09-15'),
(19,'Economics Notes','Prepare notes on Indian Economy.','2026-09-09','2026-09-16'),
(20,'Database Basics','Create ER Diagram for Student Database.','2026-09-10','2026-09-17');

-- ==========================================
-- TIMETABLE
-- ==========================================

INSERT INTO timetable
(class_subject_id, day_of_week, start_time, end_time, room_number)
VALUES

-- ==========================================
-- CLASS 9A (class_subject_id 1-5)
-- ==========================================
(1,'Monday','09:00','10:00','A101'),
(2,'Monday','10:00','11:00','A101'),
(3,'Monday','11:15','12:15','A101'),
(4,'Monday','12:15','01:15','A101'),
(5,'Monday','02:00','03:00','Lab-A'),

(2,'Tuesday','09:00','10:00','A101'),
(1,'Tuesday','10:00','11:00','A101'),
(5,'Tuesday','11:15','12:15','Lab-A'),
(3,'Tuesday','12:15','01:15','A101'),
(4,'Tuesday','02:00','03:00','A101'),

(3,'Wednesday','09:00','10:00','A101'),
(4,'Wednesday','10:00','11:00','A101'),
(1,'Wednesday','11:15','12:15','A101'),
(2,'Wednesday','12:15','01:15','A101'),
(5,'Wednesday','02:00','03:00','Lab-A'),

(4,'Thursday','09:00','10:00','A101'),
(5,'Thursday','10:00','11:00','Lab-A'),
(2,'Thursday','11:15','12:15','A101'),
(1,'Thursday','12:15','01:15','A101'),
(3,'Thursday','02:00','03:00','A101'),

(5,'Friday','09:00','10:00','Lab-A'),
(3,'Friday','10:00','11:00','A101'),
(4,'Friday','11:15','12:15','A101'),
(2,'Friday','12:15','01:15','A101'),
(1,'Friday','02:00','03:00','A101'),

-- ==========================================
-- CLASS 9B (class_subject_id 6-10)
-- ==========================================
(6,'Monday','09:00','10:00','B101'),
(7,'Monday','10:00','11:00','B101'),
(8,'Monday','11:15','12:15','B101'),
(9,'Monday','12:15','01:15','B101'),
(10,'Monday','02:00','03:00','Lab-B'),

(7,'Tuesday','09:00','10:00','B101'),
(6,'Tuesday','10:00','11:00','B101'),
(10,'Tuesday','11:15','12:15','Lab-B'),
(8,'Tuesday','12:15','01:15','B101'),
(9,'Tuesday','02:00','03:00','B101'),

(8,'Wednesday','09:00','10:00','B101'),
(9,'Wednesday','10:00','11:00','B101'),
(6,'Wednesday','11:15','12:15','B101'),
(7,'Wednesday','12:15','01:15','B101'),
(10,'Wednesday','02:00','03:00','Lab-B'),

(9,'Thursday','09:00','10:00','B101'),
(10,'Thursday','10:00','11:00','Lab-B'),
(7,'Thursday','11:15','12:15','B101'),
(6,'Thursday','12:15','01:15','B101'),
(8,'Thursday','02:00','03:00','B101'),

(10,'Friday','09:00','10:00','Lab-B'),
(8,'Friday','10:00','11:00','B101'),
(9,'Friday','11:15','12:15','B101'),
(7,'Friday','12:15','01:15','B101'),
(6,'Friday','02:00','03:00','B101'),

-- ==========================================
-- CLASS 10A (class_subject_id 11-15)
-- ==========================================
(11,'Monday','09:00','10:00','C101'),
(12,'Monday','10:00','11:00','C101'),
(13,'Monday','11:15','12:15','C101'),
(14,'Monday','12:15','01:15','C101'),
(15,'Monday','02:00','03:00','Lab-C'),

(12,'Tuesday','09:00','10:00','C101'),
(11,'Tuesday','10:00','11:00','C101'),
(15,'Tuesday','11:15','12:15','Lab-C'),
(13,'Tuesday','12:15','01:15','C101'),
(14,'Tuesday','02:00','03:00','C101'),

(13,'Wednesday','09:00','10:00','C101'),
(14,'Wednesday','10:00','11:00','C101'),
(11,'Wednesday','11:15','12:15','C101'),
(12,'Wednesday','12:15','01:15','C101'),
(15,'Wednesday','02:00','03:00','Lab-C'),

(14,'Thursday','09:00','10:00','C101'),
(15,'Thursday','10:00','11:00','Lab-C'),
(12,'Thursday','11:15','12:15','C101'),
(11,'Thursday','12:15','01:15','C101'),
(13,'Thursday','02:00','03:00','C101'),

(15,'Friday','09:00','10:00','Lab-C'),
(13,'Friday','10:00','11:00','C101'),
(14,'Friday','11:15','12:15','C101'),
(12,'Friday','12:15','01:15','C101'),
(11,'Friday','02:00','03:00','C101'),

-- ==========================================
-- CLASS 10B (class_subject_id 16-20)
-- ==========================================
(16,'Monday','09:00','10:00','D101'),
(17,'Monday','10:00','11:00','D101'),
(18,'Monday','11:15','12:15','D101'),
(19,'Monday','12:15','01:15','D101'),
(20,'Monday','02:00','03:00','Lab-D'),

(17,'Tuesday','09:00','10:00','D101'),
(16,'Tuesday','10:00','11:00','D101'),
(20,'Tuesday','11:15','12:15','Lab-D'),
(18,'Tuesday','12:15','01:15','D101'),
(19,'Tuesday','02:00','03:00','D101'),

(18,'Wednesday','09:00','10:00','D101'),
(19,'Wednesday','10:00','11:00','D101'),
(16,'Wednesday','11:15','12:15','D101'),
(17,'Wednesday','12:15','01:15','D101'),
(20,'Wednesday','02:00','03:00','Lab-D'),

(19,'Thursday','09:00','10:00','D101'),
(20,'Thursday','10:00','11:00','Lab-D'),
(17,'Thursday','11:15','12:15','D101'),
(16,'Thursday','12:15','01:15','D101'),
(18,'Thursday','02:00','03:00','D101'),

(20,'Friday','09:00','10:00','Lab-D'),
(18,'Friday','10:00','11:00','D101'),
(19,'Friday','11:15','12:15','D101'),
(17,'Friday','12:15','01:15','D101'),
(16,'Friday','02:00','03:00','D101');

-- ==========================================
-- ANNOUNCEMENTS
-- ==========================================

INSERT INTO announcements
(title, message, posted_by)
VALUES
(
'Welcome Back',
'Welcome students to the new academic year 2026-27. We wish everyone a successful academic session.',
1
),

(
'Mid Term Examination',
'Mid Term Examinations will begin from 15 September 2026. Students are advised to complete their syllabus on time.',
1
),

(
'Science Exhibition',
'The Annual Science Exhibition will be held on 10 October 2026. Interested students should register with their science teacher.',
2
),

(
'Parent Teacher Meeting',
'Parent Teacher Meeting (PTM) is scheduled on 20 September 2026 from 9:00 AM to 1:00 PM.',
3
),

(
'Holiday Notice',
'The school will remain closed on 2 October 2026 on account of Gandhi Jayanti.',
1
),

(
'Computer Lab Competition',
'An inter-class coding competition will be organized on 5 November 2026. Students are encouraged to participate.',
2
),

(
'Sports Day',
'Annual Sports Day will be conducted on 25 November 2026. Practice sessions begin next week.',
3
),

(
'Library Week',
'Students are encouraged to participate in Library Week activities from 7 to 12 December 2026.',
1
);